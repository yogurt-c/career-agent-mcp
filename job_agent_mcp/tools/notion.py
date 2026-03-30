"""Notion CV loader tool."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from notion_client import AsyncClient

from job_agent_mcp.config import load_config


def _rich_text_to_str(rich_text: List[Dict[str, Any]]) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text)


def _block_to_markdown(block: Dict[str, Any], depth: int = 0) -> Optional[str]:
    btype = block.get("type")
    if not btype:
        return None
    content = block.get(btype, {})
    rich = content.get("rich_text", [])
    text = _rich_text_to_str(rich)
    indent = "  " * depth

    if btype == "heading_1":
        return f"# {text}"
    if btype == "heading_2":
        return f"## {text}"
    if btype == "heading_3":
        return f"### {text}"
    if btype == "paragraph":
        return f"{indent}{text}" if text else ""
    if btype == "bulleted_list_item":
        return f"{indent}- {text}"
    if btype == "numbered_list_item":
        return f"{indent}1. {text}"
    if btype == "toggle":
        return f"{indent}**{text}**"
    if btype == "callout":
        return f"{indent}> {text}"
    if btype == "quote":
        return f"{indent}> {text}"
    if btype == "divider":
        return "---"
    if btype == "code":
        lang = content.get("language", "")
        return f"```{lang}\n{text}\n```"
    if btype == "to_do":
        checked = content.get("checked", False)
        mark = "x" if checked else " "
        return f"{indent}- [{mark}] {text}"
    # column_list, column: skip wrapper, handled by children
    if btype in ("column_list", "column"):
        return None
    return f"{indent}{text}" if text else None


async def _fetch_blocks_recursive(client: AsyncClient, block_id: str, depth: int = 0) -> List[str]:
    lines: List[str] = []
    cursor = None
    while True:
        kwargs: Dict[str, Any] = {"block_id": block_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = await client.blocks.children.list(**kwargs)
        for block in resp.get("results", []):
            line = _block_to_markdown(block, depth)
            if line is not None:
                lines.append(line)
            if block.get("has_children"):
                child_lines = await _fetch_blocks_recursive(client, block["id"], depth + 1)
                lines.extend(child_lines)
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return lines


_RICH_TEXT_TYPES = {
    "paragraph", "bulleted_list_item", "numbered_list_item",
    "heading_1", "heading_2", "heading_3", "to_do",
}


def _build_block_body(block_type: str, content: str, checked: bool = False) -> Dict[str, Any]:
    """블록 타입과 내용으로 Notion API 블록 객체를 생성한다."""
    if block_type == "divider":
        return {"type": "divider", "divider": {}}
    if block_type not in _RICH_TEXT_TYPES:
        raise ValueError(f"지원하지 않는 블록 타입: {block_type}")
    rich_text = [{"type": "text", "text": {"content": content}}]
    if block_type == "to_do":
        return {"type": "to_do", "to_do": {"rich_text": rich_text, "checked": checked}}
    return {"type": block_type, block_type: {"rich_text": rich_text}}


async def _fetch_blocks_with_id(
    client: AsyncClient, block_id: str, depth: int = 0
) -> List[Dict[str, Any]]:
    """블록 ID, 타입, 텍스트를 포함한 블록 목록을 재귀 조회한다."""
    result = []
    cursor = None
    while True:
        kwargs: Dict[str, Any] = {"block_id": block_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = await client.blocks.children.list(**kwargs)
        for block in resp.get("results", []):
            btype = block.get("type", "")
            rich = block.get(btype, {}).get("rich_text", [])
            result.append({
                "id": block["id"],
                "type": btype,
                "text": _rich_text_to_str(rich),
                "depth": depth,
                "has_children": block.get("has_children", False),
            })
            if block.get("has_children"):
                result.extend(await _fetch_blocks_with_id(client, block["id"], depth + 1))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return result


async def list_cv_blocks(page_id: Optional[str] = None) -> str:
    cfg = load_config()
    if not cfg.notion_token:
        return "Notion 토큰이 설정되지 않았습니다.\nhttp://localhost:5173 에서 설정하세요."
    target_id = page_id or cfg.notion_cv_page_id
    if not target_id:
        return "페이지 ID가 없습니다. page_id를 직접 전달하거나 CV 페이지를 설정하세요."
    client = AsyncClient(auth=cfg.notion_token)
    try:
        blocks = await _fetch_blocks_with_id(client, target_id)
        if not blocks:
            return "블록이 없습니다."
        lines = []
        for b in blocks:
            indent = "  " * b["depth"]
            text_preview = b["text"][:60] + "…" if len(b["text"]) > 60 else b["text"]
            lines.append(f'{indent}[{b["id"]}] ({b["type"]}) {text_preview}')
        return "\n".join(lines)
    except Exception as e:
        return f"블록 목록 조회 실패: {e}"
    finally:
        await client.aclose()


async def append_block(
    parent_id: str,
    block_type: str,
    content: str,
    checked: bool = False,
) -> str:
    cfg = load_config()
    if not cfg.notion_token:
        return "Notion 토큰이 설정되지 않았습니다.\nhttp://localhost:5173 에서 설정하세요."
    client = AsyncClient(auth=cfg.notion_token)
    try:
        body = _build_block_body(block_type, content, checked)
        resp = await client.blocks.children.append(block_id=parent_id, children=[body])
        new_id = (resp.get("results") or [{}])[0].get("id", "알 수 없음")
        return f"블록 추가 성공. 새 블록 ID: {new_id}"
    except Exception as e:
        return f"블록 추가 실패: {e}"
    finally:
        await client.aclose()


async def update_block(block_id: str, content: str, checked: bool = False) -> str:
    cfg = load_config()
    if not cfg.notion_token:
        return "Notion 토큰이 설정되지 않았습니다.\nhttp://localhost:5173 에서 설정하세요."
    client = AsyncClient(auth=cfg.notion_token)
    try:
        existing = await client.blocks.retrieve(block_id=block_id)
        btype = existing.get("type")
        if not btype:
            return f"블록 타입을 확인할 수 없습니다. block_id: {block_id}"
        if btype == "divider":
            return "divider 블록은 내용을 수정할 수 없습니다."
        if btype not in _RICH_TEXT_TYPES:
            return f"지원하지 않는 블록 타입입니다: {btype}"
        rich_text = [{"type": "text", "text": {"content": content}}]
        if btype == "to_do":
            kwargs = {"block_id": block_id, "to_do": {"rich_text": rich_text, "checked": checked}}
        else:
            kwargs = {"block_id": block_id, btype: {"rich_text": rich_text}}
        await client.blocks.update(**kwargs)
        return f"블록 수정 성공. block_id: {block_id}"
    except Exception as e:
        return f"블록 수정 실패: {e}"
    finally:
        await client.aclose()


async def delete_block(block_id: str) -> str:
    cfg = load_config()
    if not cfg.notion_token:
        return "Notion 토큰이 설정되지 않았습니다.\nhttp://localhost:5173 에서 설정하세요."
    client = AsyncClient(auth=cfg.notion_token)
    try:
        await client.blocks.delete(block_id=block_id)
        return f"블록 삭제 성공. block_id: {block_id}"
    except Exception as e:
        return f"블록 삭제 실패: {e}"
    finally:
        await client.aclose()


async def load_cv() -> str:
    """Load CV content from Notion and return as markdown text."""
    cfg = load_config()
    if not cfg.notion_token:
        return (
            "Notion 토큰이 설정되지 않았습니다.\n"
            "http://localhost:5173 에서 Notion 설정을 완료하세요."
        )
    if not cfg.notion_cv_page_id:
        return (
            "Notion CV 페이지 ID가 설정되지 않았습니다.\n"
            "http://localhost:5173 에서 CV 페이지 URL을 입력하세요."
        )

    client = AsyncClient(auth=cfg.notion_token)
    try:
        # Get page title
        page = await client.pages.retrieve(page_id=cfg.notion_cv_page_id)
        title_prop = page.get("properties", {}).get("title", {})
        title_parts = title_prop.get("title", [])
        page_title = _rich_text_to_str(title_parts) if title_parts else "CV"

        lines = await _fetch_blocks_recursive(client, cfg.notion_cv_page_id)
        content = "\n".join(line for line in lines if line is not None)
        return f"# {page_title}\n\n{content}"
    except Exception as e:
        return f"Notion CV 조회 실패: {e}"
    finally:
        await client.aclose()

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

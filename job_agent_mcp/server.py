"""FastMCP server for job-agent-mcp."""
from __future__ import annotations

import threading
import webbrowser

from fastmcp import FastMCP

from job_agent_mcp.config import load_config
from job_agent_mcp.prompts.job_agent import build_job_agent_prompt
from job_agent_mcp.tools.notion import append_block, delete_block, list_cv_blocks, load_cv, update_block
from job_agent_mcp.tools.remember import get_job_detail, search_jobs
from job_agent_mcp.web.app import run_server

mcp = FastMCP("job-agent")

# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def load_cv_tool() -> str:
    """Notion CV를 마크다운 텍스트로 읽어온다."""
    return await load_cv()


@mcp.tool()
async def list_cv_blocks_tool(page_id: str = "") -> str:
    """Notion 페이지의 블록 목록을 블록 ID와 함께 반환한다.
    블록을 수정/삭제하기 전에 이 도구로 대상 블록 ID를 먼저 확인한다.

    Args:
        page_id: 조회할 페이지 ID. 비워두면 설정된 CV 페이지를 사용한다.
    """
    return await list_cv_blocks(page_id or None)


@mcp.tool()
async def append_block_tool(
    parent_id: str,
    block_type: str,
    content: str,
    checked: bool = False,
) -> str:
    """Notion 페이지 또는 블록에 새 블록을 추가한다.

    Args:
        parent_id: 부모 페이지 또는 블록의 ID
        block_type: 블록 타입 (paragraph / bulleted_list_item / numbered_list_item /
                    heading_1 / heading_2 / heading_3 / to_do / divider)
        content: 블록 텍스트 내용 (divider는 무시됨)
        checked: to_do 블록의 완료 여부 (기본값: False)
    """
    return await append_block(parent_id, block_type, content, checked)


@mcp.tool()
async def update_block_tool(
    block_id: str,
    content: str,
    checked: bool = False,
) -> str:
    """기존 Notion 블록의 텍스트를 수정한다. 블록 타입은 자동 감지된다.

    Args:
        block_id: 수정할 블록의 ID (list_cv_blocks_tool로 확인)
        content: 새 텍스트 내용
        checked: to_do 블록의 완료 여부 (기본값: False)
    """
    return await update_block(block_id, content, checked)


@mcp.tool()
async def delete_block_tool(block_id: str) -> str:
    """Notion 블록을 삭제한다. 삭제 후 복구할 수 없으므로 신중하게 사용한다.

    Args:
        block_id: 삭제할 블록의 ID (list_cv_blocks_tool로 확인)
    """
    return await delete_block(block_id)


@mcp.tool()
async def search_jobs_tool() -> str:
    """저장된 필터로 리멤버 커리어 채용 공고를 1~5페이지 조회한다.

    응답: 텍스트 테이블 (컬럼 순서: No, job_id, 회사명, 공고제목, 경력, 지역, 마감일)
    - job_id: get_job_detail_tool에 전달할 실제 공고 ID (예: 304027). 반드시 이 값을 사용.
    - No: 단순 순번이며 공고 ID가 아님. get_job_detail_tool에 사용 불가.
    """
    return await search_jobs()


@mcp.tool()
async def get_job_detail_tool(job_id: str) -> str:
    """특정 채용 공고의 상세 정보를 조회한다.

    Args:
        job_id: search_jobs_tool 결과 테이블의 job_id 컬럼 값 (숫자 ID, 예: "304027")
    """
    return await get_job_detail(job_id)


# ── Prompts ───────────────────────────────────────────────────────────────────

@mcp.prompt()
def job_agent() -> str:
    """채용 에이전트 전체 워크플로우 (CV 로드 → 공고 검색 → 매칭 → 지원서류 작성)"""
    return build_job_agent_prompt()


# ── Main ──────────────────────────────────────────────────────────────────────

def _start_web_server():
    run_server(port=5173, debug=False)


def main():
    cfg = load_config()

    # Start Flask in daemon thread
    web_thread = threading.Thread(target=_start_web_server, daemon=True)
    web_thread.start()

    # Auto-open browser if Notion is not configured
    if not cfg.is_notion_configured():
        webbrowser.open("http://localhost:5173")

    # Run MCP server (blocking)
    mcp.run()


if __name__ == "__main__":
    main()

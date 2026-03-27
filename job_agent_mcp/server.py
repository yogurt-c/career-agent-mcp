"""FastMCP server for job-agent-mcp."""
from __future__ import annotations

import threading
import webbrowser

from fastmcp import FastMCP

from job_agent_mcp.config import load_config
from job_agent_mcp.prompts.job_agent import build_job_agent_prompt
from job_agent_mcp.tools.notion import load_cv
from job_agent_mcp.tools.remember import get_job_detail, search_jobs
from job_agent_mcp.web.app import run_server

mcp = FastMCP("job-agent")

# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def load_cv_tool() -> str:
    """Notion CV를 마크다운 텍스트로 읽어온다."""
    return await load_cv()


@mcp.tool()
async def search_jobs_tool() -> str:
    """저장된 필터로 리멤버 커리어 채용 공고를 1~5페이지 조회한다."""
    return await search_jobs()


@mcp.tool()
async def get_job_detail_tool(job_id: str) -> str:
    """특정 채용 공고의 상세 정보를 조회한다.

    Args:
        job_id: 리멤버 커리어 공고 ID
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

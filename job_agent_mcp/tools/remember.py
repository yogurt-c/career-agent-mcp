"""Remember Career API tools."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx

from job_agent_mcp.config import load_config

BASE_URL = "https://career-api.rememberapp.co.kr"
SEARCH_SEED = 78688566


async def _fetch_page(client: httpx.AsyncClient, page: int, cfg) -> List[Dict[str, Any]]:
    payload = {
        "search": {
            "job_category_names": cfg.get_job_categories(),
            "company_sizes": cfg.company_sizes,
            "include_applied_job_posting": False,
        },
        "sort": "starts_at_desc",
        "ai_new_model": False,
        "meta": {"device_uid": cfg.device_uid},
        "page": page,
        "per": 30,
        "new_function_score": True,
        "seed": SEARCH_SEED,
    }
    resp = await client.post(
        f"{BASE_URL}/job_postings/search",
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data") or data.get("job_postings", [])


def _format_experience(min_exp, max_exp) -> str:
    if min_exp is None and max_exp is None:
        return "경력 무관"
    if min_exp == 0 and max_exp is None:
        return "신입"
    if max_exp is None:
        return f"{min_exp}년 이상"
    if min_exp == max_exp:
        return f"{min_exp}년"
    return f"{min_exp}~{max_exp}년"


def _format_location(job: Dict[str, Any]) -> str:
    addr = job.get("normalized_address") or {}
    parts = [addr.get("level1", ""), addr.get("level2", "")]
    return " ".join(p for p in parts if p) or "미정"


def _format_deadline(job: Dict[str, Any]) -> str:
    ends_at = job.get("ends_at")
    if not ends_at:
        return "상시"
    return ends_at[:10]


def _job_summary(jobs: List[Dict[str, Any]]) -> str:
    lines = [f"총 {len(jobs)}개 공고\n"]
    header = f"{'No':<5} {'job_id':<12} {'회사명':<20} {'공고제목':<40} {'경력':<12} {'지역':<14} {'마감일'}"
    lines.append(header)
    lines.append("-" * 115)

    id_index = []
    for i, job in enumerate(jobs, 1):
        job_id = job.get("id", "")
        company = (job.get("company_name") or (job.get("organization") or {}).get("name") or "")[:18]
        title = (job.get("title") or "")[:38]
        exp = _format_experience(job.get("min_experience"), job.get("max_experience"))
        loc = _format_location(job)[:12]
        deadline = _format_deadline(job)
        lines.append(f"{i:<5} {str(job_id):<12} {company:<20} {title:<40} {exp:<12} {loc:<14} {deadline}")
        id_index.append((i, job_id))

    lines.append("")
    lines.append("## JOB_ID_INDEX")
    for num, jid in id_index:
        lines.append(f"{num}={jid}")
    lines.append("## END_JOB_ID_INDEX")

    return "\n".join(lines)


async def search_jobs() -> str:
    """Search Remember Career job postings using saved filters (pages 1-5)."""
    cfg = load_config()
    if not cfg.company_sizes and not cfg.get_job_categories():
        return "필터가 설정되지 않았습니다. http://localhost:5173 에서 필터를 설정하세요."

    async with httpx.AsyncClient() as client:
        tasks = [_fetch_page(client, page, cfg) for page in range(1, 6)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[Dict[str, Any]] = []
    for r in results:
        if isinstance(r, Exception):
            continue
        all_jobs.extend(r)

    if not all_jobs:
        return "검색 조건을 만족하는 공고가 없습니다."

    return _job_summary(all_jobs)


async def get_job_detail(job_id: str) -> str:
    """Get detailed information for a specific job posting by ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/job_postings/{job_id}",
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()

    jp = data.get("data") or data.get("job_posting", data)

    def section(title: str, content) -> str:
        if not content:
            return ""
        return f"\n[ {title} ]\n{content}\n"

    exp = _format_experience(jp.get("min_experience"), jp.get("max_experience"))
    loc_parts = []
    addr = jp.get("normalized_address") or {}
    for key in ("level1", "level2", "level3"):
        v = addr.get(key)
        if v:
            loc_parts.append(v)
    loc = " ".join(loc_parts) or "미정"

    company_name = (jp.get("organization") or {}).get("name") or jp.get("company_name", "")

    lines = [
        "=" * 60,
        f"회사명    : {company_name}",
        f"공고제목  : {jp.get('title', '')}",
        f"경력      : {exp}",
        f"학력      : {jp.get('education_requirement') or jp.get('education_level') or '무관'}",
        f"지역      : {loc}",
        f"마감일    : {_format_deadline(jp)}",
        f"등록일    : {(jp.get('starts_at') or '')[:10]}",
    ]

    # Check required documents
    req = jp.get("application_requirements") or {}
    docs = []
    if req.get("language"):
        docs.append("어학 성적 (TOEIC/TOEFL/OPIc 등)")
    if req.get("certificate"):
        docs.append("자격증 사본")
    if req.get("portfolio"):
        docs.append("포트폴리오")
    if req.get("current_salary"):
        docs.append("현재 연봉 정보")
    if docs:
        lines.append("\n📋 지원 시 필요 서류:")
        for d in docs:
            lines.append(f"  • {d}")

    lines.append(section("주요업무", jp.get("job_description") or jp.get("main_tasks")))
    lines.append(section("자격요건", jp.get("qualifications")))
    lines.append(section("우대사항", jp.get("preferred_qualifications")))
    lines.append(section("채용절차", jp.get("recruiting_process") or jp.get("hiring_process")))
    lines.append(section("기업소개", jp.get("introduction") or jp.get("company_intro") or jp.get("company_description")))
    lines.append("=" * 60)

    return "\n".join(lines)

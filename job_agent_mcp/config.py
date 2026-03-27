from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".job-agent"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ── Enum constants ────────────────────────────────────────────────────────────

JOB_CATEGORIES = [
    {"level1": "SW개발", "level2": "백엔드"},
    {"level1": "마케팅·광고", "level2": "마케팅 전략·기획"},
    {"level1": "마케팅·광고", "level2": "브랜드 마케팅"},
    {"level1": "마케팅·광고", "level2": "퍼포먼스 마케팅"},
    {"level1": "마케팅·광고", "level2": "광고 관리·운영"},
]

JOB_CATEGORY_LABELS = [
    "SW개발 > 백엔드",
    "마케팅·광고 > 마케팅 전략·기획",
    "마케팅·광고 > 브랜드 마케팅",
    "마케팅·광고 > 퍼포먼스 마케팅",
    "마케팅·광고 > 광고 관리·운영",
]

COMPANY_SIZES = ["large", "middle_standing", "small_medium", "startup", "foreign"]

COMPANY_SIZE_LABELS = {
    "large": "대기업",
    "middle_standing": "중견기업",
    "small_medium": "중소기업",
    "startup": "스타트업",
    "foreign": "외국계",
}


# ── Config model ──────────────────────────────────────────────────────────────

class Config(BaseModel):
    notion_token: str = ""
    notion_cv_page_id: str = ""
    job_category_indices: List[int] = Field(default_factory=list)
    company_sizes: List[str] = Field(default_factory=lambda: ["large", "middle_standing"])
    device_uid: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def get_job_categories(self) -> list:
        if not self.job_category_indices:
            return [JOB_CATEGORIES[0]]
        return [JOB_CATEGORIES[i] for i in self.job_category_indices if 0 <= i < len(JOB_CATEGORIES)]

    def is_notion_configured(self) -> bool:
        return bool(self.notion_token and self.notion_cv_page_id)


def load_config() -> Config:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return Config(**data)
        except Exception:
            pass
    cfg = Config()
    save_config(cfg)
    return cfg


def save_config(cfg: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")


def extract_page_id(url_or_id: str) -> str:
    """Extract Notion page ID from a URL or raw ID string."""
    # URL patterns: /page-title-{32hex} or /{32hex} or ?p={32hex}
    import re
    # Remove hyphens from plain UUID
    clean = url_or_id.strip().rstrip("/")
    # Try to find a 32-char hex string at the end of the URL
    match = re.search(r"([0-9a-f]{32})(?:[?#].*)?$", clean, re.IGNORECASE)
    if match:
        raw = match.group(1)
        # Format as UUID
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    # Try standard UUID pattern already formatted
    match = re.search(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        clean,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return url_or_id

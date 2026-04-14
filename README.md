본 레포는 Notion CV를 기반으로 채용 공고를 매칭하고 지원서류 작성을 도와주는 MCP 서버입니다.

`career-agent-mcp`는 Claude Desktop, Claude Code 등 AI 에이전트에서 자연어로 **CV 로드 → 공고 검색 → 매칭 분석 → 자소서 작성** 전체 워크플로우를 조작할 수 있게 해주는 MCP 서버입니다.

## Features

| 도구 / 프롬프트 | 트리거 예시 | 설명 |
|----------------|------------|------|
| **`load_cv_tool`** | "내 CV 불러와줘" | Notion CV 페이지를 마크다운으로 읽어옴 |
| **`list_cv_blocks_tool`** | "CV 블록 목록 보여줘" | 블록 ID 포함 CV 구조 조회 (수정·삭제 전 확인용) |
| **`append_block_tool`** | "경력 항목 추가해줘" | Notion CV에 새 블록 추가 |
| **`update_block_tool`** | "이 항목 수정해줘" | 기존 블록 텍스트 수정 |
| **`delete_block_tool`** | "이 블록 삭제해줘" | 블록 삭제 (복구 불가) |
| **`search_jobs_tool`** | "공고 찾아줘", "채용공고 검색" | 저장된 필터로 리멤버 커리어 공고 1~5페이지 조회 |
| **`get_job_detail_tool`** | "이 공고 자세히 봐줘" | 특정 공고 상세 조회 |
| **`job_agent` 프롬프트** | "job_agent 실행해줘" | CV 로드 → 공고 검색 → 매칭 → 자소서 작성 전체 워크플로우 |

## Installation

### Quick Install

```bash
# Claude Code
claude mcp add career-agent -- uvx --from git+https://github.com/yogurt-c/career-agent-mcp job-agent-mcp
```

Claude Desktop은 아래 [에이전트별 등록](#에이전트별-등록) 섹션을 참고하세요.

### Prerequisites

| 항목 | 설치 방법 | 비고 |
|------|----------|------|
| uv | macOS: `brew install uv` | Homebrew 권장 |
| uv | macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh` | curl 대안 |
| uv | Windows: PowerShell에서 `irm https://astral.sh/uv/install.ps1 \| iex` | |

> **macOS 주의**: Claude Desktop은 GUI 앱이라 쉘 프로파일(`.zshrc` 등)을 읽지 않습니다.
> `curl`로 설치하면 `uvx`가 `~/.local/bin`에 놓여 Claude Desktop에서 인식되지 않을 수 있습니다.
> Homebrew로 설치하면 `/opt/homebrew/bin`에 놓여 자동으로 인식됩니다.

### 에이전트별 등록

**Claude Desktop** — Settings > Developer > Edit Config에서 `claude_desktop_config.json`을 열어 `mcpServers`에 추가합니다.

macOS (Homebrew로 uv 설치):
```json
{
  "mcpServers": {
    "career-agent": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yogurt-c/career-agent-mcp", "job-agent-mcp"]
    }
  }
}
```

macOS / Linux (curl로 uv 설치) — `uvx` 절대 경로를 먼저 확인한 뒤 `command`에 입력:
```bash
which uvx
# 예: /Users/your-username/.local/bin/uvx
```
```json
{
  "mcpServers": {
    "career-agent": {
      "command": "/Users/your-username/.local/bin/uvx",
      "args": ["--from", "git+https://github.com/yogurt-c/career-agent-mcp", "job-agent-mcp"]
    }
  }
}
```

Windows — GUI 앱도 시스템 PATH를 상속하므로 `uvx` 그대로 사용 가능:
```json
{
  "mcpServers": {
    "career-agent": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yogurt-c/career-agent-mcp", "job-agent-mcp"]
    }
  }
}
```

> 위 설정으로 실패하면 `where uvx`로 경로 확인 후 절대 경로로 교체하세요.
> (예: `C:\\Users\\your-username\\.local\\bin\\uvx.exe`)

---

**Claude Code**:
```bash
claude mcp add career-agent -- uvx --from git+https://github.com/yogurt-c/career-agent-mcp job-agent-mcp
```

---

**로컬 개발용** — `--from` 다음 값을 로컬 경로로 변경:
```bash
# Claude Code
claude mcp add career-agent -- uvx --from /path/to/career-agent-mcp job-agent-mcp
```
```json
// Claude Desktop
"args": ["--from", "/path/to/career-agent-mcp", "job-agent-mcp"]
```

## Initial Setup

Claude Desktop을 재시작하면 MCP 서버가 자동으로 기동됩니다.

1. Notion 설정이 없으면 브라우저에서 `http://localhost:5173` 자동 열림
2. 설정 페이지에서 아래 항목 입력 후 저장

| 항목 | 설명 |
|------|------|
| Notion Integration 토큰 | `ntn_` 접두사 토큰 |
| CV 페이지 URL | Notion CV 페이지 URL (페이지 ID 자동 추출) |
| 직군 / 직무 필터 | 공고 검색에 사용할 직군 선택 |
| 회사 규모 필터 | 공고 검색에 사용할 회사 규모 선택 |

3. 저장 완료 → `~/.job-agent/config.json`에 저장됨

### Notion Integration 토큰 발급

1. [Notion Integrations](https://www.notion.so/profile/integrations/internal) 접속
2. **새 Integration 생성** → 권한: **Read content**, **Update content**, **Insert content** 체크
3. 생성된 토큰(`ntn_` 접두사) 복사
4. Notion CV 페이지 우측 상단 **···** > **Connections** > Integration 추가

## Usage Examples

```
> job_agent 프롬프트 실행해줘
> 공고 찾아줘
> 내 CV 불러와서 이 공고랑 매칭 분석해줘
> 백엔드 공고 검색하고 잘 맞는 것들 추려줘
> 이 공고에 맞는 자소서 작성해줘
> CV에서 경력 항목 수정해줘
```

## Troubleshooting

### 캐시 초기화 (업데이트)

`uvx`는 설치된 패키지를 캐시합니다. 최신 소스를 받으려면 캐시를 초기화하세요.

```bash
uv cache clean
```

**Claude Desktop**: 캐시 초기화 후 재시작

**Claude Code**:
```bash
uv cache clean
claude mcp remove career-agent
claude mcp add career-agent -- uvx --from git+https://github.com/yogurt-c/career-agent-mcp job-agent-mcp
```

### 다른 PC에서 사용

1. Claude Desktop 설정에 위 JSON 추가
2. Claude Desktop 재시작 → 자동 설치 및 기동
3. `http://localhost:5173` 접속 → 설정 입력

> 설정은 각 PC의 `~/.job-agent/config.json`에 저장되므로 기기별로 별도 입력해야 합니다.

## Configuration

```
~/.job-agent/config.json
```

> ⚠️ 이 파일에는 Notion 토큰이 포함됩니다. 절대 커밋하지 마세요.

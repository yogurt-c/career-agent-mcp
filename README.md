# career-agent-mcp

Notion CV 기반으로 채용 공고를 매칭하고 지원서류 작성을 도와주는 MCP 서버입니다.

## 기능

- **`load_cv`** — Notion CV 페이지를 마크다운으로 읽어옴
- **`search_jobs`** — 저장된 필터로 채용 공고 1~5페이지 조회
- **`get_job_detail`** — 특정 공고 상세 조회
- **`job_agent` 프롬프트** — CV 로드 → 공고 검색 → 매칭 → 자소서 작성 전체 워크플로우

## 사전 요구사항

- [uv](https://docs.astral.sh/uv/getting-started/installation/) 설치

  **macOS (권장 — Homebrew)**
  ```bash
  brew install uv
  ```

  **macOS / Linux (curl)**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

  **Windows (PowerShell)**
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

  > **macOS 주의**: Claude Desktop은 GUI 앱이라 쉘 프로파일(`.zshrc` 등)을 읽지 않습니다.
  > curl로 설치하면 `uvx`가 `~/.local/bin`에 놓여 Claude Desktop에서 인식되지 않을 수 있습니다.
  > Homebrew로 설치하면 `/opt/homebrew/bin`에 놓여 자동으로 인식됩니다.

## Claude Desktop 등록

### macOS — Homebrew로 uv 설치한 경우

1. Claude Desktop 상단 메뉴 **Claude** > **Settings** 클릭
2. 좌측 사이드바에서 **Developer** 탭 선택
3. **Edit Config** 버튼 클릭 → `claude_desktop_config.json` 파일이 열림
4. `mcpServers` 항목에 아래 내용을 추가 후 저장

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

5. Claude Desktop 재시작

### macOS / Linux — curl로 uv 설치한 경우

`uvx` 절대 경로를 먼저 확인합니다:

```bash
which uvx
# 예: /Users/your-username/.local/bin/uvx
```

`command` 값을 위 경로로 교체합니다:

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

### Windows

Windows는 GUI 앱도 시스템 PATH를 상속하므로 `uvx` 그대로 사용 가능합니다:

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

> 위 설정으로 실패하면 `where uvx` 로 경로 확인 후 절대 경로로 교체하세요.
> (예: `C:\\Users\\your-username\\.local\\bin\\uvx.exe`)

### 로컬 개발용

위 JSON에서 `"--from"` 다음 값을 로컬 경로로 변경:

```json
"args": ["--from", "/path/to/career-agent-mcp", "job-agent-mcp"]
```

## Claude Code 등록

```bash
claude mcp add career-agent -- uvx --from git+https://github.com/yogurt-c/career-agent-mcp job-agent-mcp
```

### 로컬 개발용

```bash
claude mcp add career-agent -- uvx --from /path/to/career-agent-mcp job-agent-mcp
```

## 초기 설정

1. Claude Desktop을 재시작하면 MCP 서버가 자동으로 기동됩니다.
2. Notion 설정이 없으면 브라우저에서 `http://localhost:5173`이 자동으로 열립니다.
3. 설정 페이지에서:
   - **Notion Integration 토큰** 입력
   - **CV 페이지 URL** 입력 (페이지 ID 자동 추출)
   - **직군/직무 필터** 선택
   - **회사 규모 필터** 선택
4. 저장 버튼 클릭 → `~/.job-agent/config.json`에 저장됨

### Notion Integration 토큰 발급

1. [https://www.notion.so/profile/integrations/internal](https://www.notion.so/profile/integrations/internal) 접속
2. 새 Integration 생성
3. 권한: **Read content**, **Update content**, **Insert content** 체크
4. 생성된 토큰(`ntn_` 접두사)을 복사
5. Notion CV 페이지 우측 상단 **···** > **Connections** > Integration 추가

## 사용 방법

Claude Desktop 또는 Claude Code에서:

```
job_agent 프롬프트 실행해줘
```

또는 직접 도구 호출:

```
search_jobs 로 공고 검색해줘
```

## 업데이트

`uvx`는 설치된 패키지를 캐시하므로, 최신 소스를 받으려면 캐시를 초기화해야 합니다.

```bash
uv cache clean
```

**Claude Desktop**: 캐시 초기화 후 Claude Desktop 재시작

**Claude Code**:

```bash
uv cache clean
claude mcp remove career-agent
claude mcp add career-agent -- uvx --from git+https://github.com/yogurt-c/career-agent-mcp job-agent-mcp
```

## 다른 PC에서 사용

1. Claude Desktop 설정에 위 GitHub uvx 명령어 추가
2. Claude Desktop 재시작 → 자동 설치 및 기동
3. `http://localhost:5173` 접속 → 설정 완료

설정은 각 PC의 `~/.job-agent/config.json`에 저장되므로 별도로 입력해야 합니다.

## 설정 파일 위치

```
~/.job-agent/config.json
```

> ⚠️ 이 파일에는 Notion 토큰이 포함됩니다. 절대 커밋하지 마세요.

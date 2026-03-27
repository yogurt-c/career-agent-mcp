# career-agent-mcp

Notion CV 기반으로 채용 공고를 매칭하고 지원서류 작성을 도와주는 MCP 서버입니다.

## 기능

- **`load_cv`** — Notion CV 페이지를 마크다운으로 읽어옴
- **`search_jobs`** — 저장된 필터로 채용 공고 1~5페이지 조회
- **`get_job_detail`** — 특정 공고 상세 조회
- **`job_agent` 프롬프트** — CV 로드 → 공고 검색 → 매칭 → 자소서 작성 전체 워크플로우

## 사전 요구사항

- [uv](https://docs.astral.sh/uv/getting-started/installation/) 설치
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Claude Desktop 등록

`~/Library/Application Support/Claude/claude_desktop_config.json`:

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

### 로컬 개발용

```json
{
  "mcpServers": {
    "career-agent": {
      "command": "uvx",
      "args": ["--from", "/path/to/career-agent-mcp", "job-agent-mcp"]
    }
  }
}
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

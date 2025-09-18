### Pilldoc User MCP (Local MCP Server)

이 프로젝트는 MCP 호환 클라이언트에서 사용할 수 있는 로컬 MCP 서버를 제공합니다. 로그인 토큰 발급과 주성분 목록 조회 기능을 도구(tool)로 노출합니다.




### 요구 사항
- Python 3.9+

### 설치
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 환경 변수 설정
`.env.example`를 참고해 `.env.local`을 생성하세요.
```bash
cp .env.example .env.local
vi .env.local
```
- 필수
  - `EDB_BASE_URL` (예: https://dev-adminapi.edbintra.co.kr)
  - `EDB_LOGIN_URL` (예: https://dev-adminapi.edbintra.co.kr/v1/auth/login)
- 선택
  - `EDB_USER_ID`, `EDB_PASSWORD` (로그인 시 기본값)
  - `EDB_FORCE_LOGIN` (true/false)

### 서버 실행
- 단독 실행
```bash
python -m src.mcp_server
```

- 매니페스트 (MCP 클라이언트용)
```json
{
  "name": "pilldoc-user-mcp",
  "version": "0.1.0",
  "entry": "python -m src.mcp_server"
}
```
MCP 호환 클라이언트(예: IDE/Agent)에서 이 디렉토리를 로컬 서버로 등록하세요.

### 제공 도구 (Tools)
- `login(userId?, password?, force?, loginUrl?, timeout?) -> token`
  - 미지정 시 환경변수 사용: `EDB_USER_ID`, `EDB_PASSWORD`, `EDB_LOGIN_URL`
- `main_ingredient(token? | userId/password, baseUrl?, accept?, timeout?, Page, PageSize, ingredientNameKor?, IngredientCode?, drugKind?, SortBy?, a4?, a4Off?, a5?, a5Off?, drugkind?, drugkindOff?, effect?, effectOff?, showMapped?) -> JSON`
  - `token` 미제공 시 내부적으로 `login`을 호출
  - `baseUrl` 미지정 시 `EDB_BASE_URL` 사용
- `pilldoc_accounts(token? | userId/password, baseUrl?, accept?, timeout?, pageSize?, page?, sortBy?, erpKind?, isAdDisplay?, salesChannel?, pharmChain?, currentSearchType?, searchKeyword?, accountType?) -> JSON`
- `pilldoc_user(token, baseUrl, id, accept?, timeout?) -> JSON`
- `pilldoc_pharm(token, baseUrl, bizno, accept?, timeout?) -> JSON`
- `pilldoc_user_from_accounts(accountField?, accountValue?, index?, token? | userId/password, baseUrl?, accept?, timeout?) -> JSON`
  - `/v1/pilldoc/accounts`에서 계정을 골라 ID를 얻은 뒤 `/v1/pilldoc/user/{id}` 상세를 반환

### 간단 호출 예 (개념)
- 토큰 발급: `login({ userId, password, force: true })`
- 주성분 조회: `main_ingredient({ Page: 1, PageSize: 20, ingredientNameKor: "아스포타제알파" })`
- pilldoc 계정: `pilldoc_accounts({ token, baseUrl })`
- pilldoc 사용자: `pilldoc_user({ token, baseUrl, id: "USER_ID" })`
- pilldoc 계정 검색: `pilldoc_accounts({ pageSize: 20, page: 1, erpKind: ["iT3000"], accountType: "일반" })`
- pilldoc 사용자(계정에서 선택): `pilldoc_user_from_accounts({ searchKeyword: "홍길동", currentSearchType: ["s"], index: 0 })`
- pilldoc 약국: `pilldoc_pharm({ token, baseUrl, bizno: "사업자번호" })`

### 디렉토리
- `src/mcp_server.py`: MCP 서버 엔트리
- `src/auth.py`: 로그인/토큰 유틸
- `src/druginfo/main_ingredient.py`: 조회 로직 (도구에서 재사용)

### Claude Desktop 설정
macOS(로컬)에서 Claude Desktop과 연동하려면 아래 설정 파일을 생성하세요.

1) 가상환경과 의존성 준비
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) 설정 파일 생성 (macOS)
- 경로: `~/Library/Application Support/Claude/claude_desktop_config.json`
- 예시 내용(경로를 사용자의 실제 경로로 변경하세요). `-c` 실행 방식:
```json
{
  "mcpServers": {
    "pilldoc-user-mcp": {
      "command": "/ABSOLUTE/PROJECT/PATH/.venv/bin/python",
      "args": [
        "-c",
        "import sys; sys.path.insert(0, '/ABSOLUTE/PROJECT/PATH'); from src.mcp_server import create_server; create_server().run()"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": "/ABSOLUTE/PROJECT/PATH",
        "EDB_BASE_URL": "https://dev-adminapi.edbintra.co.kr",
        "EDB_LOGIN_URL": "https://dev-adminapi.edbintra.co.kr/v1/auth/login",
        "EDB_USER_ID": "EMAIL",
        "EDB_PASSWORD": "PASSWORD"
      }
    }
  }
}
```

참고: Claude Desktop은 `cwd`를 무시할 수 있습니다. 위 예시처럼 `sys.path.insert(0, PROJECT_PATH)` 또는 `env.PYTHONPATH`에 프로젝트 경로를 추가해야 `import src...`가 정상 동작합니다. 로그에 `ModuleNotFoundError: No module named 'src'`가 보이면 이 설정을 확인하세요.

3) Claude Desktop 재시작 후 사용
- Claude 대화 입력창에서 등록된 MCP 도구들을 사용할 수 있습니다.
- 환경변수는 프로젝트 루트의 `.env.local`를 활용하세요.

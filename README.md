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
- `pilldoc_accounts(token? | userId/password, baseUrl?, accept?, timeout?, pageSize?, page?, sortBy?, erpKind?, isAdDisplay?, adBlocked?, salesChannel?, pharmChain?, currentSearchType?, searchKeyword?, accountType?) -> JSON`
- `pilldoc_user(token, baseUrl, id, accept?, timeout?) -> JSON`
- `pilldoc_pharm(token, baseUrl, bizno, accept?, timeout?) -> JSON`
- `pilldoc_adps_rejects(bizNo, token? | userId/password, baseUrl?, accept?, timeout?) -> JSON`
- `pilldoc_adps_reject(bizNo, campaignId, comment, token? | userId/password, baseUrl?, accept?, timeout?) -> JSON`
- `pilldoc_user_from_accounts(accountField?, accountValue?, index?, token? | userId/password, baseUrl?, accept?, timeout?, pageSize?, page?, sortBy?, erpKind?, isAdDisplay?, adBlocked?, salesChannel?, pharmChain?, currentSearchType?, searchKeyword?, accountType?) -> JSON`
- `pilldoc_accounts_stats(token? | userId/password, baseUrl?, accept?, timeout?, pageSize?, maxPages?, sortBy?, erpKind?, isAdDisplay?, adBlocked?, salesChannel?, pharmChain?, currentSearchType?, searchKeyword?, accountType?) -> JSON`
  - 계정 목록을 페이지네이션으로 수집하여 통계를 집계합니다.
  - 반환: `totalCountReported`, `pagesFetched`, `period.from/to`, `stats.monthly/region/erpCode/adBlocked`
- `pilldoc_update_account(id, body, token? | userId/password, baseUrl?, accept?, timeout?, contentType?) -> JSON`
   - `/v1/pilldoc/account/{id}`로 PATCH 호출하여 약국/계정 정보를 수정
- `pilldoc_update_account_by_search(body, pharmName?, bizNo?, exact?, index?, accountType?, currentSearchType?, maxPages?, pageSize?, salesChannel?, erpKind?, pharmChain?, token? | userId/password, baseUrl?, accept?, timeout?, contentType?) -> JSON`
   - `/v1/pilldoc/accounts`에서 약국명/사업자번호로 id를 찾은 뒤 `/v1/pilldoc/account/{id}` PATCH 수행
  - `pharmChain` 배열 필터 지원: 지정 시 체인 소속으로 추가 필터링
  - `salesChannel`/`erpKind` 배열 필터 지원
  - `maxPages`: 검색 페이지 수 제한(0이면 전체), 대량 데이터에서 유용
  - `contentType`: PATCH 요청 Content-Type 지정(기본 `application/json`)
  - `bizNo`는 하이픈 포함 형태(`317-87-01363`)로 입력해도 자동 정규화되어 조회됩니다.
  - `/v1/pilldoc/accounts`에서 계정을 골라 ID를 얻은 뒤 `/v1/pilldoc/user/{id}` 상세를 반환

### 간단 호출 예 (개념)
- 토큰 발급: `login({ userId, password, force: true })`
- pilldoc 계정: `pilldoc_accounts({ token, baseUrl })`
- 광고 차단된 약국만: `pilldoc_accounts({ adBlocked: true })`  // 내부적으로 `isAdDisplay: 0`으로 매핑
- 광고 차단되지 않은 약국만: `pilldoc_accounts({ adBlocked: false })`  // 내부적으로 `isAdDisplay: 1`으로 매핑
- 월별/지역별 등 통계: `pilldoc_accounts_stats({ pageSize: 200, maxPages: 0 })`
- pilldoc 사용자: `pilldoc_user({ token, baseUrl, id: "USER_ID" })`
- pilldoc 계정 검색: `pilldoc_accounts({ pageSize: 20, page: 1, erpKind: ["iT3000"], accountType: "일반" })`
- pilldoc 사용자(계정에서 선택): `pilldoc_user_from_accounts({ searchKeyword: "홍길동", currentSearchType: ["s"], index: 0 })`
- pilldoc 약국: `pilldoc_pharm({ token, baseUrl, bizno: "사업자번호" })`
- 차단 캠페인: `pilldoc_adps_rejects({ token, baseUrl, bizNo: "사업자번호" })`
  - 차단 등록: `pilldoc_adps_reject({ token, baseUrl, bizNo: "사업자번호", campaignId: 123, comment: "사유" })`

#### 약국 정보 업데이트 예시
```json
// 호출 예 (개념)
{
  "id": "d596dbdb-5a96-4970-8fd9-08bae9021e05",
  "body": {
    "userType": "pharm",
    "displayName": "string",
    "email": "user@example.com",
    "memberShipType": "basic",
    "isDisable": true,
    "lockoutEnabled": true,
    "unLockAccount": true,
    "약국명": "string",
    "accountType": "일반",
    "관리자승인여부": true,
    "요양기관번호": "string",
    "약국전화번호": "string",
    "휴대전화번호": "string",
    "pharAddress": "string",
    "pharAddressDetail": "string",
    "latitude": 0,
    "longitude": 0,
    "bcode": "string",
    "pharmChain": "string",
    "erpCode": 0,
    "영업채널Code": 0,
    "salesManagerId": 0,
    "필첵QR표기": "표시",
    "약국광고표기": "표시"
  }
}
```

#### 검색 후 약국 정보 업데이트 예시 (adpsRejects 포함)
```json
// 호출 예 (개념)
{
  "pharmName": "OOO약국",
  "pharmChain": ["온누리약국"],
  "salesChannel": [5],
  "erpKind": ["IT3000", "EPHARM"],
  "maxPages": 0,
  "contentType": "application/json",
  "body": {
    "약국명": "OOO약국",
    "약국전화번호": "02-000-0000",
    "휴대전화번호": "010-0000-0000"
  }
}
```
참고: `pilldoc_find_pharm` 결과의 `matches[*]`에는 `account`, `user`, `pharm`에 더해 `adpsRejects`가 포함됩니다.

### pharmChain 허용 값
- 온누리약국
- 옵티마케어
- 더블유스토어
- 휴베이스
- 리드팜
- 메디팜
- 데이팜
- 위드팜
- 참약사

### salesChannel 코드
- 1: 약학정보원
- 2: 비트
- 3: 한미
- 0: 터울
- 4: 팜플
- 5: 이디비

### erpKind 코드
- IT3000: [약학정보원] PharmIT3000
- BIZPHARM: [비트컴퓨터] BizPharm-C
- DAYPHARM: [데이팜] DayPharm
- WITHPHARM: [위드팜] WithPharmErp
- EPHARM: [이디비] EPharm
- EGHIS: [이지스헬스케어] 이지스팜

### 디렉토리
- `src/mcp_server.py`: MCP 서버 엔트리
- `src/auth.py`: 로그인/토큰 유틸

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

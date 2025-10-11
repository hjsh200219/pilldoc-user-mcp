# PillDoc User MCP - 통일된 아키텍처

## 개요

이 문서는 PillDoc User MCP와 DrugInfo MCP의 통일된 아키텍처 구조를 설명합니다.

## 디렉토리 구조

```
project-root/
├── src/
│   ├── __init__.py
│   ├── server.py                 # MCP 서버 메인 클래스 (표준 MCP SDK 사용)
│   ├── mcp_server.py            # 서버 생성 및 실행 (FastMCP 호환)
│   ├── login_jwt.py             # CLI 유틸리티
│   │
│   ├── auth/                    # 인증 모듈
│   │   ├── __init__.py
│   │   ├── login.py            # 로그인 및 토큰 추출
│   │   └── manager.py          # 인증 관리자
│   │
│   ├── utils/                   # 유틸리티
│   │   ├── __init__.py
│   │   └── config.py           # 설정 관리
│   │
│   ├── handlers/                # MCP 핸들러
│   │   ├── __init__.py
│   │   ├── tools.py            # 도구 핸들러
│   │   ├── resources.py        # 리소스 핸들러
│   │   └── prompts.py          # 프롬프트 핸들러
│   │
│   ├── {domain}/                # 도메인별 API 클라이언트
│   │   ├── __init__.py
│   │   └── client.py
│   │
│   └── mcp_tools/               # MCP 도구 등록
│       ├── __init__.py
│       ├── auth_tools.py
│       └── {domain}_tools.py
│
├── requirements.txt
├── README.md
├── ARCHITECTURE.md
└── .env.local
```

## 아키텍처 계층

### 1. 서버 계층 (Server Layer)
- **책임**: MCP 서버 초기화 및 실행
- **파일**: `src/server.py`
- **주요 클래스**:
  - `PillDocServer` / `DrugInfoServer`: 메인 서버 클래스
  - 표준 MCP SDK 사용

### 2. 핸들러 계층 (Handler Layer)
- **책임**: MCP 프로토콜 요청 처리
- **디렉토리**: `src/handlers/`
- **구성**:
  - `tools.py`: 도구 목록 및 호출 핸들러
  - `resources.py`: 리소스 제공 핸들러
  - `prompts.py`: 프롬프트 제공 핸들러

### 3. 비즈니스 로직 계층 (Business Logic Layer)
- **책임**: 도메인별 API 클라이언트 및 비즈니스 로직
- **디렉토리**: `src/{domain}/`
- **예시**:
  - `src/pilldoc/`: PillDoc API 클라이언트
  - `src/druginfo/`: DrugInfo API 클라이언트

### 4. 도구 등록 계층 (Tool Registration Layer)
- **책임**: MCP 도구 정의 및 등록
- **디렉토리**: `src/mcp_tools/`
- **구성**:
  - `auth_tools.py`: 인증 관련 도구
  - `{domain}_tools.py`: 도메인별 도구

### 5. 유틸리티 계층 (Utility Layer)
- **책임**: 공통 유틸리티 기능
- **디렉토리**: `src/utils/`, `src/auth/`
- **구성**:
  - `utils/config.py`: 설정 관리
  - `auth/login.py`: 로그인 유틸
  - `auth/manager.py`: 인증 관리

## 핵심 컴포넌트

### Server 클래스

```python
class PillDocServer:
    """PillDoc User MCP 서버 메인 클래스"""

    def __init__(self):
        self.server = Server("pilldoc-user-mcp")
        self.config = Config()
        self.auth_manager = AuthManager(self.config)

    async def initialize(self):
        """서버 초기화 및 핸들러 설정"""
        # 자동 로그인 시도
        # 핸들러 설정

    async def run(self):
        """서버 실행"""
```

### 핸들러 패턴

```python
def setup_tool_handlers(server: Server, auth_manager: AuthManager):
    """도구 핸들러 설정"""

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """도구 목록 반환"""

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        """도구 호출 처리"""
```

### 인증 관리

```python
class AuthManager:
    """인증 관리 클래스"""

    async def auto_login(self) -> str:
        """자동 로그인"""

    async def login(self, ...) -> str:
        """수동 로그인"""
```

## 설정 관리

### Config 클래스

```python
class Config(BaseSettings):
    """애플리케이션 설정"""

    # 서버 설정
    server_name: str
    server_version: str

    # API 설정
    edb_base_url: str
    edb_login_url: Optional[str]

    # 성능 설정
    timeout: int
    max_retries: int

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 환경 변수

### 필수 환경 변수

```bash
EDB_BASE_URL=https://dev-adminapi.edbintra.co.kr
EDB_LOGIN_URL=https://dev-adminapi.edbintra.co.kr/v1/auth/login
```

### 선택 환경 변수

```bash
EDB_USER_ID=user@example.com
EDB_PASSWORD=password
EDB_FORCE_LOGIN=false
EDB_TIMEOUT=15
```

## 실행 방법

### 직접 실행

```bash
python -m src.server
```

### FastMCP 호환 (기존 코드와의 호환성)

```bash
python -m src.mcp_server
```

### Claude Desktop 설정

```json
{
  "mcpServers": {
    "pilldoc-user-mcp": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "src.server"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "EDB_BASE_URL": "https://dev-adminapi.edbintra.co.kr",
        "EDB_LOGIN_URL": "https://dev-adminapi.edbintra.co.kr/v1/auth/login"
      }
    }
  }
}
```

## 데이터 흐름

```
Claude Desktop
    ↓
MCP Protocol (stdio)
    ↓
Server (server.py)
    ↓
Handler (handlers/)
    ↓
Tool (mcp_tools/)
    ↓
Business Logic (pilldoc/)
    ↓
External API
```

## 에러 처리

### 에러 계층

1. **MCP 프로토콜 에러**: MCP SDK에서 처리
2. **비즈니스 로직 에러**: 도구에서 처리
3. **API 호출 에러**: 클라이언트에서 처리

### 에러 응답 형식

```python
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "에러 메시지",
        "details": {}
    }
}
```

## 확장 가이드

### 새로운 도구 추가

1. **도메인 API 클라이언트 작성** (`src/{domain}/client.py`)
2. **도구 등록 파일 작성** (`src/mcp_tools/{domain}_tools.py`)
3. **핸들러에서 도구 등록** (`src/handlers/tools.py`)

### 새로운 프롬프트 추가

1. **프롬프트 핸들러 수정** (`src/handlers/prompts.py`)
2. `list_prompts()`에 프롬프트 추가
3. `get_prompt()`에 프롬프트 내용 추가

## 모범 사례

### 1. 모듈 구조
- 도메인별로 명확히 분리
- 계층 간 의존성을 단방향으로 유지
- 공통 코드는 utils에 배치

### 2. 에러 처리
- 모든 에러는 적절히 catch
- 사용자에게 명확한 에러 메시지 제공
- 민감한 정보는 로그에 노출하지 않음

### 3. 설정 관리
- 환경 변수를 통한 설정
- pydantic을 이용한 검증
- 개발/프로덕션 환경 분리

### 4. 로깅
- 적절한 로그 레벨 사용
- 구조화된 로깅
- stderr로 출력 (stdio 프로토콜)

## 참고 자료

- [MCP SDK 문서](https://github.com/anthropics/mcp)
- [FastMCP 문서](https://github.com/jlowin/fastmcp)
- [Pydantic 문서](https://docs.pydantic.dev/)

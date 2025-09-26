# PillDoc MCP 서버 - 표준 MCP SDK 버전

표준 MCP SDK를 사용하여 구현된 PillDoc MCP 서버입니다.

## 🚀 주요 변경사항

### FastMCP → 표준 MCP SDK
- FastMCP 프레임워크 제거
- 표준 MCP SDK 사용으로 더 나은 호환성
- 비동기 처리 지원 (asyncio)
- stdio 기반 통신

## 📦 설치

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 설정
`.env` 파일 생성:
```env
# API 설정
EDB_BASE_URL=https://dev-adminapi.edbintra.co.kr
EDB_USER_ID=your-email@example.com
EDB_PASSWORD=your-password

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=/var/log/pilldoc-mcp.log

# 성능 설정
TIMEOUT=15
MAX_RETRIES=3
DEFAULT_PAGE_SIZE=20
```

## 🏃 실행

### 직접 실행
```bash
# Python 모듈로 실행
python -m src.main_server

# 또는 메인 파일 직접 실행
python src/main_server.py
```

### Claude Desktop 연동

1. Claude Desktop 설정 파일 열기:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. 다음 설정 추가:
```json
{
  "mcpServers": {
    "pilldoc-user-mcp": {
      "command": "python",
      "args": ["-m", "src.main_server"],
      "cwd": "/path/to/pilldoc-user-mcp",
      "env": {
        "PYTHONPATH": "/path/to/pilldoc-user-mcp",
        "EDB_BASE_URL": "https://dev-adminapi.edbintra.co.kr"
      }
    }
  }
}
```

3. Claude Desktop 재시작

## 📋 사용 가능한 도구

### 인증 관리
- `login` - 로그인 및 토큰 획득
  ```json
  {
    "userId": "user@example.com",
    "password": "password",
    "force": false
  }
  ```

### 계정 관리
- `pilldoc_accounts` - 계정 목록 조회
  ```json
  {
    "page": 1,
    "pageSize": 20,
    "erpKind": ["IT3000"],
    "salesChannel": [1, 2],
    "isAdDisplay": 0
  }
  ```

- `pilldoc_accounts_stats` - 계정 통계 조회
  ```json
  {
    "includeAdStats": true
  }
  ```

### 약국 검색
- `find_pharm` - 약국 검색
  ```json
  {
    "name": "서울약국",
    "region": "강남구",
    "page": 1,
    "pageSize": 20
  }
  ```

### 서버 관리
- `get_server_metrics` - 메트릭 조회
- `reset_server_metrics` - 메트릭 초기화
- `health_check` - 서버 상태 확인
- `get_server_config` - 설정 조회

## 🏗️ 프로젝트 구조

```
pilldoc-user-mcp/
├── src/
│   ├── main_server.py      # 메인 서버 (표준 MCP SDK)
│   ├── tool_registry.py    # 도구 레지스트리
│   ├── register_tools.py   # 도구 등록 로직
│   ├── config.py          # 설정 관리
│   ├── schemas/           # Pydantic 스키마
│   ├── utils/             # 유틸리티
│   │   ├── errors.py      # 에러 처리
│   │   ├── logging.py     # 로깅
│   │   ├── metrics.py     # 메트릭
│   │   └── validation.py  # 검증
│   └── mcp_tools/         # 기존 도구 로직
├── requirements.txt       # 의존성
├── .env                  # 환경 설정
└── claude_desktop_config.json  # Claude Desktop 설정 예제
```

## 🔧 개발

### 새 도구 추가

`src/register_tools.py`에 새 도구 추가:
```python
async def my_tool_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """도구 로직"""
    # 구현
    return {"result": "success"}

registry.register(
    name="my_tool",
    description="설명",
    handler=my_tool_handler,
    input_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        }
    }
)
```

### 로깅
```python
from src.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("메시지")
```

### 에러 처리
```python
from src.utils.errors import ValidationError

if not valid:
    raise ValidationError("잘못된 입력", field="input")
```

## 📊 모니터링

### 메트릭 확인
서버 실행 중 `get_server_metrics` 도구 호출:
```json
{
  "uptime_seconds": 3600,
  "overall": {
    "total_calls": 100,
    "success_rate": "98.0%"
  },
  "tools": {
    "login": {
      "call_count": 10,
      "avg_duration": "0.250s"
    }
  }
}
```

### 로그 확인
```bash
# 실시간 로그
tail -f /var/log/pilldoc-mcp.log

# 에러만 확인
grep ERROR /var/log/pilldoc-mcp.log
```

## 🚨 문제 해결

### 서버가 시작되지 않을 때
1. Python 버전 확인 (3.8+)
2. 의존성 설치 확인
3. 환경 변수 확인
4. 로그 파일 확인

### 도구 호출 실패
1. `health_check`로 서버 상태 확인
2. 입력 파라미터 검증
3. 토큰 유효성 확인
4. API 서버 상태 확인

### Claude Desktop 연동 실패
1. 설정 파일 경로 확인
2. Python 경로 확인
3. 작업 디렉토리 확인
4. Claude Desktop 재시작

## 📝 라이센스

MIT License
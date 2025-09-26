#!/usr/bin/env python3
"""표준 MCP SDK를 사용한 PillDoc MCP 서버 (개선 버전)"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.config import get_settings
from src.utils.logging import setup_logging, get_logger
from src.utils.errors import error_response
from src.tool_registry import ToolRegistry
from src.register_tools import register_all_tools

# 환경 변수 로드
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)

# 설정 및 로깅 초기화
settings = get_settings()
setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)


class PillDocServer:
    """PillDoc MCP 서버"""

    def __init__(self):
        self.server = Server("pilldoc-user-mcp")
        self.registry = ToolRegistry()
        self.settings = settings

    async def initialize(self):
        """서버 초기화"""
        logger.info("Initializing PillDoc MCP Server")

        # 모든 도구 등록
        await register_all_tools(self.registry)

        # MCP 핸들러 설정
        self._setup_handlers()

        logger.info(f"Server initialized with {len(self.registry.tools)} tools")

    def _setup_handlers(self):
        """MCP 서버 핸들러 설정"""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """사용 가능한 도구 목록 반환"""
            return self.registry.get_tool_list()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
            """도구 실행"""
            logger.info(f"Tool called: {name}", extra={"arguments": arguments})

            try:
                # 도구 실행
                result = await self.registry.execute(name, arguments or {})

                # 결과를 JSON 문자열로 변환
                import json
                result_text = json.dumps(result, ensure_ascii=False, indent=2)

                return [TextContent(type="text", text=result_text)]

            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
                error_result = error_response(e)

                import json
                error_text = json.dumps(error_result, ensure_ascii=False, indent=2)

                return [TextContent(type="text", text=error_text)]

        @self.server.list_prompts()
        async def list_prompts():
            """사용 가능한 프롬프트 목록"""
            return [
                {
                    "name": "tool_usage_guide",
                    "description": "도구 사용 가이드라인"
                },
                {
                    "name": "error_handling_guide",
                    "description": "에러 처리 가이드"
                }
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, Any]] = None):
            """프롬프트 내용 반환"""

            prompts = {
                "tool_usage_guide": self._get_tool_usage_guide(),
                "error_handling_guide": self._get_error_handling_guide()
            }

            content = prompts.get(name)
            if content is None:
                raise ValueError(f"Unknown prompt: {name}")

            return {
                "messages": [{
                    "role": "system",
                    "content": content
                }]
            }

    def _get_tool_usage_guide(self) -> str:
        """도구 사용 가이드 반환"""
        return """
🎯 PillDoc MCP 서버 도구 사용 가이드

=== 주요 도구 카테고리 ===

📌 인증 관리
- login: 로그인 및 토큰 획득
  - userId, password 필요
  - 토큰은 다른 API 호출에 사용

📊 계정 관리
- pilldoc_accounts: 계정 목록 조회
  - 다양한 필터 지원 (ERP, 채널, 체인 등)
  - 페이지네이션 지원
- pilldoc_accounts_stats: 계정 통계 조회

🏥 약국 검색
- find_pharm: 약국 검색
  - 사업자번호, 이름, 코드, 지역으로 검색 가능
  - 결과 페이지네이션

🔧 서버 관리
- get_server_metrics: 메트릭 조회
- reset_server_metrics: 메트릭 초기화
- health_check: 서버 상태 확인
- get_server_config: 설정 조회

=== 사용 팁 ===

1. 인증 토큰 관리
   - 토큰이 없으면 userId/password로 자동 인증
   - 토큰 만료 시 자동 재인증

2. 페이지네이션
   - 대량 데이터는 page/pageSize 활용
   - 기본값: page=1, pageSize=20

3. 필터링
   - 배열 필터는 여러 값 동시 지원
   - 예: erpKind=["IT3000", "BIZPHARM"]

4. 에러 처리
   - 모든 에러는 표준 형식으로 반환
   - success 필드로 성공 여부 확인
"""

    def _get_error_handling_guide(self) -> str:
        """에러 처리 가이드 반환"""
        return """
🚨 에러 처리 가이드

=== 표준 에러 응답 형식 ===
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "사용자 친화적 메시지",
        "details": {
            // 추가 디버깅 정보
        }
    }
}

=== 에러 코드 ===
- VALIDATION_ERROR: 입력값 검증 실패
- AUTH_ERROR: 인증 실패
- API_ERROR: 외부 API 호출 실패
- NOT_FOUND: 리소스를 찾을 수 없음
- INTERNAL_ERROR: 서버 내부 오류

=== 일반적인 해결 방법 ===

1. VALIDATION_ERROR
   - 필수 파라미터 확인
   - 데이터 형식 확인
   - 값 범위 확인

2. AUTH_ERROR
   - userId/password 확인
   - 토큰 갱신 시도
   - force=true로 재로그인

3. API_ERROR
   - 네트워크 연결 확인
   - API 서버 상태 확인
   - 재시도

4. INTERNAL_ERROR
   - 서버 로그 확인
   - 서버 재시작
   - 관리자 문의
"""

    async def run(self):
        """서버 실행"""
        await self.initialize()

        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server started on stdio")

            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pilldoc-user-mcp",
                    server_version="2.0.0"
                )
            )


async def main():
    """메인 실행 함수"""
    server = PillDocServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
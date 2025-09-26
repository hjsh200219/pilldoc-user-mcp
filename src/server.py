#!/usr/bin/env python3
"""표준 MCP SDK를 사용한 PillDoc MCP 서버"""

import os
import sys
import asyncio
import logging
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

# MCP SDK imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)

# 로컬 imports
from src.config import get_settings
from src.utils.logging import setup_logging, get_logger
from src.utils.errors import (
    MCPError,
    ValidationError,
    AuthenticationError,
    error_response
)
from src.utils.metrics import get_global_metrics, reset_global_metrics

# 환경 변수 로드
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)

# 로깅 설정
settings = get_settings()
setup_logging(settings.log_level, settings.log_file)
logger = get_logger(__name__)


class PillDocMCPServer:
    """PillDoc MCP 서버"""

    def __init__(self):
        self.server = Server("pilldoc-user-mcp")
        self.settings = get_settings()
        self.tools: Dict[str, callable] = {}

        # 서버 정보 설정
        self.server.request_context.server_info.name = "pilldoc-user-mcp"
        self.server.request_context.server_info.version = "2.0.0"

    async def initialize(self):
        """서버 초기화"""
        logger.info("Initializing PillDoc MCP Server")

        # 도구 등록
        await self._register_tools()

        # 프롬프트 등록
        await self._register_prompts()

        logger.info("Server initialization complete")

    async def _register_tools(self):
        """모든 도구 등록"""

        # 서버 관리 도구들
        await self._register_server_tools()

        # 비즈니스 로직 도구들 등록
        await self._register_business_tools()

        logger.info(f"Registered {len(self.tools)} tools")

    async def _register_server_tools(self):
        """서버 관리 도구 등록"""

        # 메트릭 조회 도구
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """사용 가능한 도구 목록 반환"""
            tools = []

            # 메트릭 조회
            tools.append(Tool(
                name="get_server_metrics",
                description="서버 운영 메트릭 조회 (호출 수, 성공률, 평균 응답시간 등)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ))

            # 메트릭 초기화
            tools.append(Tool(
                name="reset_server_metrics",
                description="서버 메트릭 초기화",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ))

            # 헬스체크
            tools.append(Tool(
                name="health_check",
                description="서버 상태 확인",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ))

            # 설정 조회
            tools.append(Tool(
                name="get_server_config",
                description="서버 설정 조회 (민감한 정보 제외)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ))

            # 비즈니스 도구들도 추가
            tools.extend(await self._get_business_tools())

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
            """도구 실행"""

            logger.info(f"Tool called: {name}", extra={"arguments": arguments})

            try:
                # 서버 관리 도구들
                if name == "get_server_metrics":
                    result = get_global_metrics()
                elif name == "reset_server_metrics":
                    reset_global_metrics()
                    result = {"success": True, "message": "메트릭이 초기화되었습니다"}
                elif name == "health_check":
                    result = {
                        "status": "healthy",
                        "server": self.settings.server_name,
                        "version": "2.0.0",
                        "uptime": get_global_metrics().get("uptime_formatted", "unknown")
                    }
                elif name == "get_server_config":
                    result = {
                        "server_name": self.settings.server_name,
                        "base_url": self.settings.edb_base_url,
                        "timeout": self.settings.timeout,
                        "max_retries": self.settings.max_retries,
                        "default_page_size": self.settings.default_page_size,
                        "max_page_size": self.settings.max_page_size,
                        "metrics_enabled": self.settings.enable_metrics,
                        "log_level": self.settings.log_level
                    }
                # 비즈니스 도구들
                elif name in self.tools:
                    result = await self.tools[name](arguments or {})
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=str(result))]

            except MCPError as e:
                logger.error(f"MCP Error in {name}: {e.message}", extra={"code": e.code})
                error_result = error_response(e)
                return [TextContent(type="text", text=str(error_result))]
            except Exception as e:
                logger.error(f"Unexpected error in {name}: {str(e)}", exc_info=True)
                error_result = error_response(e)
                return [TextContent(type="text", text=str(error_result))]

    async def _register_business_tools(self):
        """비즈니스 로직 도구 등록"""

        # 도구 임포트 및 등록
        from src.mcp_tools.helpers import ensure_token, need_base_url

        # 로그인 도구
        async def login_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """로그인 및 토큰 획득"""
            from src.auth import login_and_get_token

            user_id = args.get("userId") or self.settings.edb_user_id
            password = args.get("password") or self.settings.edb_password
            force = args.get("force", False)

            if not user_id or not password:
                raise ValidationError("userId와 password가 필요합니다")

            token = login_and_get_token(
                self.settings.get_login_url(),
                user_id,
                password,
                force,
                self.settings.timeout
            )

            return {"success": True, "token": token}

        self.tools["login"] = login_tool

        # 계정 조회 도구
        async def get_accounts_tool(args: Dict[str, Any]) -> Dict[str, Any]:
            """계정 목록 조회"""
            from src.pilldoc.api import get_accounts

            token = ensure_token(
                args.get("token"),
                args.get("userId"),
                args.get("password"),
                args.get("loginUrl"),
                args.get("timeout", self.settings.timeout)
            )
            base_url = need_base_url(args.get("baseUrl"))

            # 필터 구성
            filters = {}
            for key in ["page", "pageSize", "erpKind", "salesChannel", "pharmChain",
                       "isAdDisplay", "searchKeyword", "accountType"]:
                if key in args and args[key] is not None:
                    filters[key] = args[key]

            return get_accounts(base_url, token, timeout=self.settings.timeout, filters=filters)

        self.tools["pilldoc_accounts"] = get_accounts_tool

        # 추가 도구들은 동일한 패턴으로 등록...

    async def _get_business_tools(self) -> List[Tool]:
        """비즈니스 도구 정의 반환"""
        tools = []

        # 로그인 도구
        tools.append(Tool(
            name="login",
            description="PillDoc 서비스 로그인 및 인증 토큰 획득",
            inputSchema={
                "type": "object",
                "properties": {
                    "userId": {
                        "type": "string",
                        "description": "사용자 ID (이메일)"
                    },
                    "password": {
                        "type": "string",
                        "description": "비밀번호"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "강제 재로그인 여부",
                        "default": False
                    }
                },
                "required": []
            }
        ))

        # 계정 조회 도구
        tools.append(Tool(
            name="pilldoc_accounts",
            description="PillDoc 가입 약국 계정 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "인증 토큰"},
                    "page": {"type": "integer", "description": "페이지 번호", "minimum": 1},
                    "pageSize": {"type": "integer", "description": "페이지 크기", "minimum": 1, "maximum": 100},
                    "erpKind": {"type": "array", "items": {"type": "string"}, "description": "ERP 종류 필터"},
                    "salesChannel": {"type": "array", "items": {"type": "integer"}, "description": "판매 채널 필터"},
                    "pharmChain": {"type": "array", "items": {"type": "string"}, "description": "약국 체인 필터"},
                    "isAdDisplay": {"type": "integer", "description": "광고 표시 여부 (0: 표시, 1: 차단)"},
                    "searchKeyword": {"type": "string", "description": "검색 키워드"},
                    "accountType": {"type": "string", "description": "계정 타입"}
                },
                "required": []
            }
        ))

        return tools

    async def _register_prompts(self):
        """프롬프트 등록"""

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

            if name == "tool_usage_guide":
                return {
                    "messages": [{
                        "role": "system",
                        "content": self._get_tool_usage_guide()
                    }]
                }
            elif name == "error_handling_guide":
                return {
                    "messages": [{
                        "role": "system",
                        "content": self._get_error_handling_guide()
                    }]
                }
            else:
                raise ValueError(f"Unknown prompt: {name}")

    def _get_tool_usage_guide(self) -> str:
        """도구 사용 가이드 반환"""
        return """
🎯 TOOL 선택 가이드 - 목적에 맞는 도구 사용하기

=== 인증 관리 ===
- login: 로그인 및 토큰 획득
- 토큰은 대부분의 API 호출에 필요
- 토큰 만료 시 자동 재인증

=== 계정 관리 ===
- pilldoc_accounts: 계정 목록 조회
- 다양한 필터 옵션 지원
- 페이지네이션 지원

=== 서버 관리 ===
- get_server_metrics: 메트릭 조회
- reset_server_metrics: 메트릭 초기화
- health_check: 상태 확인
- get_server_config: 설정 조회

=== 사용 원칙 ===
1. 인증 필요한 작업은 토큰 확인
2. 페이지네이션 활용으로 성능 최적화
3. 에러 발생 시 재시도 로직 적용
4. 민감한 정보는 로그에 노출 금지
"""

    def _get_error_handling_guide(self) -> str:
        """에러 처리 가이드 반환"""
        return """
🚨 에러 처리 가이드

=== 에러 코드 ===
- VALIDATION_ERROR: 입력 검증 실패
- AUTH_ERROR: 인증 실패
- API_ERROR: 외부 API 호출 실패
- INTERNAL_ERROR: 서버 내부 오류

=== 에러 응답 형식 ===
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "에러 메시지",
        "details": {}
    }
}

=== 복구 방법 ===
1. 에러 코드 확인
2. 메시지 내용 검토
3. 필요시 재시도
4. 지속적 실패 시 관리자 문의
"""

    async def run(self):
        """서버 실행"""
        await self.initialize()

        # stdio 서버로 실행
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server started on stdio")

            init_options = InitializationOptions(
                server_name="pilldoc-user-mcp",
                server_version="2.0.0",
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )

            await self.server.run(
                read_stream,
                write_stream,
                init_options
            )


async def main():
    """메인 실행 함수"""
    try:
        server = PillDocMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
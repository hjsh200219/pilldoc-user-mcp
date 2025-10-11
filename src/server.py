#!/usr/bin/env python3
"""
PillDoc User MCP Server - 약국 계정 관리 및 서비스 도구
표준 MCP SDK를 사용한 구현
"""

import asyncio
import sys
import logging

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# 환경 변수 로드
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("pilldoc-user-mcp")

# 핸들러 임포트
from handlers import (
    setup_tool_handlers,
    setup_resource_handlers,
    setup_prompt_handlers,
)
from auth.manager import AuthManager
from utils.config import Config


class PillDocServer:
    """PillDoc User MCP 서버 메인 클래스"""

    def __init__(self):
        self.server = Server("pilldoc-user-mcp")
        self.config = Config()
        self.auth_manager = AuthManager(self.config)

        # 서버 정보 설정
        self.server.request_context.server_info = {
            "name": "pilldoc-user-mcp",
            "version": "1.0.0",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True,
            }
        }

    async def initialize(self):
        """서버 초기화"""
        logger.info("PillDoc User MCP 서버 초기화 중...")

        # 자동 로그인 시도
        if self.config.auto_login_enabled:
            try:
                await self.auth_manager.auto_login()
                logger.info("자동 로그인 성공")
            except Exception as e:
                logger.warning(f"자동 로그인 실패: {e}")

        # 핸들러 설정
        setup_tool_handlers(self.server, self.auth_manager)
        setup_resource_handlers(self.server, self.config)
        setup_prompt_handlers(self.server)

        logger.info("PillDoc User MCP 서버 초기화 완료")

    async def run(self):
        """서버 실행"""
        await self.initialize()

        # stdio 서버 실행
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pilldoc-user-mcp",
                    server_version="1.0.0",
                )
            )


async def main():
    """메인 진입점"""
    try:
        server = PillDocServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("서버 종료 중...")
    except Exception as e:
        logger.error(f"서버 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

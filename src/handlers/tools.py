"""MCP 도구 핸들러 설정"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool

logger = logging.getLogger(__name__)


def setup_tool_handlers(server: Server, auth_manager: Any):
    """도구 핸들러 설정

    Args:
        server: MCP 서버 인스턴스
        auth_manager: 인증 관리자
    """

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """등록된 도구 목록 반환"""
        from ..mcp_tools import get_registered_tools
        return get_registered_tools()

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[Any]:
        """도구 호출 처리"""
        from ..mcp_tools import call_tool
        return await call_tool(name, arguments, auth_manager)

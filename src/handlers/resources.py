"""MCP 리소스 핸들러 설정"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import Resource, ResourceContents

logger = logging.getLogger(__name__)


def setup_resource_handlers(server: Server, config: Any):
    """리소스 핸들러 설정

    Args:
        server: MCP 서버 인스턴스
        config: 설정 객체
    """

    @server.list_resources()
    async def handle_list_resources() -> list[Resource]:
        """리소스 목록 반환"""
        return [
            Resource(
                uri="config://pilldoc-user-mcp",
                name="PillDoc User MCP Configuration",
                description="서버 설정 정보",
                mimeType="application/json",
            )
        ]

    @server.read_resource()
    async def handle_read_resource(uri: str) -> ResourceContents:
        """리소스 읽기"""
        if uri == "config://pilldoc-user-mcp":
            import json
            config_data = {
                "server_name": config.server_name,
                "server_version": config.server_version,
                "base_url": config.edb_base_url,
                "timeout": config.timeout,
            }
            return ResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps(config_data, indent=2, ensure_ascii=False),
            )

        raise ValueError(f"Unknown resource: {uri}")

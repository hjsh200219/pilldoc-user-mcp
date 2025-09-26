"""표준 MCP SDK용 도구 레지스트리"""

import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable
from mcp.types import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """도구 관리를 위한 레지스트리"""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Any]]] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Any]],
        input_schema: Optional[Dict[str, Any]] = None
    ):
        """도구 등록

        Args:
            name: 도구 이름
            description: 도구 설명
            handler: 도구 실행 함수 (async)
            input_schema: JSON Schema 형식의 입력 스키마
        """
        if name in self.tools:
            raise ValueError(f"Tool already registered: {name}")

        # 기본 스키마
        if input_schema is None:
            input_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }

        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema
        }
        self.handlers[name] = handler

        logger.info(f"Registered tool: {name}")

    def get_tool_list(self) -> List[Tool]:
        """MCP Tool 객체 리스트 반환"""
        return [
            Tool(
                name=tool["name"],
                description=tool["description"],
                inputSchema=tool["inputSchema"]
            )
            for tool in self.tools.values()
        ]

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """도구 실행

        Args:
            name: 도구 이름
            arguments: 도구 인자

        Returns:
            도구 실행 결과

        Raises:
            ValueError: 도구를 찾을 수 없을 때
        """
        if name not in self.handlers:
            raise ValueError(f"Tool not found: {name}")

        handler = self.handlers[name]
        return await handler(arguments)

    def has_tool(self, name: str) -> bool:
        """도구 존재 여부 확인"""
        return name in self.tools

    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """도구 스키마 반환"""
        tool = self.tools.get(name)
        return tool["inputSchema"] if tool else None
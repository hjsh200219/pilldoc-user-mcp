"""MCP 핸들러 모듈"""

from .tools import setup_tool_handlers
from .resources import setup_resource_handlers
from .prompts import setup_prompt_handlers

__all__ = [
    "setup_tool_handlers",
    "setup_resource_handlers",
    "setup_prompt_handlers",
]

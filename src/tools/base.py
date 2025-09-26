"""도구 베이스 클래스"""
from typing import Any, Dict, Optional, Callable
from functools import wraps
import logging
from abc import ABC, abstractmethod

from ..utils.errors import handle_error, ValidationError
from ..utils.logging import log_tool_call
from ..utils.metrics import track_execution
from ..utils.validation import validate_arguments


class BaseTool(ABC):
    """모든 도구의 베이스 클래스"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """도구 파라미터 스키마 반환"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """도구 실행 로직"""
        pass

    def validate_and_execute(self, **kwargs) -> Dict[str, Any]:
        """검증 후 실행"""
        # 파라미터 검증
        schema = self.get_schema()
        if schema:
            validated_args = validate_arguments(kwargs, schema)
        else:
            validated_args = kwargs

        # 실행
        return self.execute(**validated_args)


def tool_handler(
    name: str,
    description: str,
    schema: Optional[Dict[str, Any]] = None
) -> Callable:
    """도구 핸들러 데코레이터

    에러 처리, 로깅, 메트릭 수집을 자동으로 처리합니다.

    Args:
        name: 도구 이름
        description: 도구 설명
        schema: 파라미터 검증 스키마

    Example:
        @tool_handler("search", "검색 도구", schema={
            "query": {"type": "str", "required": True},
            "limit": {"type": "int", "default": 10, "min": 1, "max": 100}
        })
        def search_tool(query: str, limit: int = 10):
            return {"results": [...]}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @handle_error
        @log_tool_call(name)
        @track_execution(name)
        def wrapper(**kwargs) -> Dict[str, Any]:
            # 파라미터 검증
            if schema:
                validated_args = validate_arguments(kwargs, schema)
            else:
                validated_args = kwargs

            # 도구 실행
            result = func(**validated_args)

            # 결과 포맷팅
            if not isinstance(result, dict):
                result = {"data": result}

            if "success" not in result:
                result["success"] = True

            return result

        # 메타데이터 추가
        wrapper.tool_name = name
        wrapper.tool_description = description
        wrapper.tool_schema = schema

        return wrapper
    return decorator


class ToolRegistry:
    """도구 레지스트리"""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, tool: Callable) -> None:
        """도구 등록"""
        if not hasattr(tool, "tool_name"):
            raise ValueError("도구에 tool_name 속성이 필요합니다")

        name = tool.tool_name
        if name in self.tools:
            raise ValueError(f"도구가 이미 등록되어 있습니다: {name}")

        self.tools[name] = tool
        logging.info(f"도구 등록됨: {name}")

    def get(self, name: str) -> Optional[Callable]:
        """도구 가져오기"""
        return self.tools.get(name)

    def list_tools(self) -> list[Dict[str, Any]]:
        """등록된 모든 도구 목록"""
        return [
            {
                "name": tool.tool_name,
                "description": tool.tool_description,
                "schema": tool.tool_schema
            }
            for tool in self.tools.values()
        ]

    def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """도구 실행"""
        tool = self.get(name)
        if not tool:
            raise ValidationError(f"도구를 찾을 수 없습니다: {name}")

        return tool(**kwargs)
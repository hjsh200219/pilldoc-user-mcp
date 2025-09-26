"""에러 처리 유틸리티"""
from typing import Any, Dict, Optional
import logging
import traceback
from functools import wraps

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """MCP 서버 기본 에러"""
    def __init__(self, message: str, code: str = "MCP_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class ValidationError(MCPError):
    """입력 검증 에러"""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(MCPError):
    """인증 에러"""
    def __init__(self, message: str = "인증에 실패했습니다"):
        super().__init__(message, "AUTH_ERROR")


class NotFoundError(MCPError):
    """리소스를 찾을 수 없음"""
    def __init__(self, resource: str):
        super().__init__(f"{resource}을(를) 찾을 수 없습니다", "NOT_FOUND", {"resource": resource})


class APIError(MCPError):
    """외부 API 호출 에러"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        super().__init__(message, "API_ERROR", details)


def error_response(error: Exception) -> Dict[str, Any]:
    """에러를 표준 응답 형식으로 변환"""
    if isinstance(error, MCPError):
        return {
            "success": False,
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details
            }
        }

    # 일반 예외
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return {
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "내부 서버 오류가 발생했습니다",
            "details": {
                "type": type(error).__name__,
                "message": str(error)
            }
        }
    }


def handle_error(func):
    """에러 처리 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPError as e:
            logger.error(f"MCP Error in {func.__name__}: {e.message}", extra={"code": e.code, "details": e.details})
            return error_response(e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return error_response(e)

    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """필수 필드 검증"""
    missing = [field for field in required_fields if field not in data or data[field] is None]
    if missing:
        raise ValidationError(
            f"필수 필드가 누락되었습니다: {', '.join(missing)}",
            field=missing[0]
        )
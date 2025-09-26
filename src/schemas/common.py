"""공통 스키마 정의"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지당 항목 수")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 형식"""
    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="추가 세부 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "INVALID_REQUEST",
                "message": "요청 파라미터가 올바르지 않습니다",
                "details": {
                    "field": "email",
                    "reason": "올바른 이메일 형식이 아닙니다"
                }
            }
        }


class BaseResponse(BaseModel):
    """기본 응답 형식"""
    success: bool = Field(..., description="성공 여부")
    data: Optional[Any] = Field(None, description="응답 데이터")
    error: Optional[ErrorResponse] = Field(None, description="에러 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "example"},
                "error": None
            }
        }
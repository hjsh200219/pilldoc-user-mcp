"""인증 관련 스키마"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class LoginRequest(BaseModel):
    """로그인 요청"""
    user_id: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=1, description="비밀번호")
    force: bool = Field(False, description="강제 재로그인 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user@example.com",
                "password": "password123",
                "force": False
            }
        }


class TokenInfo(BaseModel):
    """토큰 정보"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field("Bearer", description="토큰 타입")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_at": "2025-09-27T10:00:00Z"
            }
        }


class LoginResponse(BaseModel):
    """로그인 응답"""
    success: bool = Field(..., description="로그인 성공 여부")
    token: Optional[TokenInfo] = Field(None, description="토큰 정보")
    message: Optional[str] = Field(None, description="응답 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIs...",
                    "token_type": "Bearer"
                },
                "message": "로그인 성공"
            }
        }
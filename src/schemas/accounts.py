"""계정 관련 스키마"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class AccountFilter(BaseModel):
    """계정 검색 필터"""
    erp_kind: Optional[List[str]] = Field(None, description="ERP 종류")
    sales_channel: Optional[List[int]] = Field(None, description="판매 채널")
    pharm_chain: Optional[List[str]] = Field(None, description="약국 체인")
    is_ad_display: Optional[int] = Field(None, ge=0, le=1, description="광고 표시 여부")
    search_keyword: Optional[str] = Field(None, description="검색 키워드")
    account_type: Optional[str] = Field(None, description="계정 타입")

    class Config:
        json_schema_extra = {
            "example": {
                "erp_kind": ["IT3000", "BIZPHARM"],
                "sales_channel": [1, 2],
                "is_ad_display": 0,
                "search_keyword": "서울"
            }
        }


class AccountInfo(BaseModel):
    """계정 정보"""
    id: str = Field(..., description="계정 ID")
    name: str = Field(..., description="약국명")
    biz_no: Optional[str] = Field(None, description="사업자번호")
    pharm_code: Optional[str] = Field(None, description="약국코드")
    erp_kind: Optional[str] = Field(None, description="ERP 종류")
    sales_channel: Optional[int] = Field(None, description="판매 채널")
    pharm_chain: Optional[str] = Field(None, description="약국 체인")
    is_ad_display: Optional[int] = Field(None, description="광고 표시 여부")
    created_at: Optional[datetime] = Field(None, description="생성일")
    address: Optional[str] = Field(None, description="주소")
    phone: Optional[str] = Field(None, description="전화번호")


class AccountStats(BaseModel):
    """계정 통계"""
    total_count: int = Field(..., description="전체 개수")
    active_count: int = Field(0, description="활성 계정 수")
    blocked_count: int = Field(0, description="차단된 계정 수")
    by_erp: Optional[dict] = Field(None, description="ERP별 통계")
    by_channel: Optional[dict] = Field(None, description="채널별 통계")
    by_chain: Optional[dict] = Field(None, description="체인별 통계")

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 1000,
                "active_count": 800,
                "blocked_count": 200,
                "by_erp": {"IT3000": 500, "BIZPHARM": 300},
                "by_channel": {"1": 600, "2": 400}
            }
        }
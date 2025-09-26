"""약국 관련 스키마"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class PharmacySearchRequest(BaseModel):
    """약국 검색 요청"""
    keyword: Optional[str] = Field(None, description="검색 키워드 (약국명, 주소 등)")
    biz_no: Optional[str] = Field(None, description="사업자번호")
    pharm_code: Optional[str] = Field(None, description="약국코드")
    region: Optional[str] = Field(None, description="지역명")
    chain: Optional[str] = Field(None, description="체인명")
    page: int = Field(1, ge=1, description="페이지 번호")
    page_size: int = Field(20, ge=1, le=100, description="페이지당 항목 수")

    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "서울약국",
                "region": "서울특별시 강남구",
                "page": 1,
                "page_size": 20
            }
        }


class PharmacyInfo(BaseModel):
    """약국 정보"""
    id: str = Field(..., description="약국 ID")
    name: str = Field(..., description="약국명")
    biz_no: Optional[str] = Field(None, description="사업자번호")
    pharm_code: Optional[str] = Field(None, description="약국코드 (요양기관기호)")
    owner_name: Optional[str] = Field(None, description="대표자명")
    phone: Optional[str] = Field(None, description="전화번호")
    address: Optional[str] = Field(None, description="주소")
    latitude: Optional[float] = Field(None, description="위도")
    longitude: Optional[float] = Field(None, description="경도")
    chain: Optional[str] = Field(None, description="체인명")
    open_date: Optional[datetime] = Field(None, description="개업일")
    is_active: bool = Field(True, description="활성 상태")
    created_at: Optional[datetime] = Field(None, description="등록일")
    updated_at: Optional[datetime] = Field(None, description="수정일")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "PHARM001",
                "name": "행복약국",
                "biz_no": "123-45-67890",
                "pharm_code": "12345678",
                "owner_name": "김약사",
                "phone": "02-1234-5678",
                "address": "서울특별시 강남구 테헤란로 123",
                "chain": "온누리약국",
                "is_active": True
            }
        }
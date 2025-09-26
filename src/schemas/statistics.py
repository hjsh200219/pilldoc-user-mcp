"""통계 관련 스키마"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import date


class StatisticsRequest(BaseModel):
    """통계 요청"""
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")
    group_by: Optional[Literal["month", "region", "erp", "channel"]] = Field(
        None, description="그룹핑 기준"
    )
    filters: Optional[Dict[str, Any]] = Field(None, description="필터 조건")
    summary_only: bool = Field(False, description="요약만 반환")
    max_items: int = Field(0, ge=0, description="최대 항목 수 (0=무제한)")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2025-09-01",
                "end_date": "2025-09-30",
                "group_by": "region",
                "summary_only": True
            }
        }


class ERPStatistics(BaseModel):
    """ERP별 통계"""
    erp_code: str = Field(..., description="ERP 코드")
    erp_name: str = Field(..., description="ERP 이름")
    pharmacy_count: int = Field(..., description="약국 수")
    print_count: int = Field(0, description="출력 수")
    percentage: float = Field(0.0, description="비율(%)")

    class Config:
        json_schema_extra = {
            "example": {
                "erp_code": "IT3000",
                "erp_name": "PharmIT3000",
                "pharmacy_count": 500,
                "print_count": 10000,
                "percentage": 25.5
            }
        }


class RegionStatistics(BaseModel):
    """지역별 통계"""
    region: str = Field(..., description="지역명")
    level: Literal["sido", "sigungu", "emdong"] = Field(..., description="지역 레벨")
    pharmacy_count: int = Field(..., description="약국 수")
    print_count: int = Field(0, description="출력 수")
    sub_regions: Optional[List['RegionStatistics']] = Field(None, description="하위 지역")

    class Config:
        json_schema_extra = {
            "example": {
                "region": "서울특별시",
                "level": "sido",
                "pharmacy_count": 2000,
                "print_count": 50000,
                "sub_regions": []
            }
        }


class StatisticsResponse(BaseModel):
    """통계 응답"""
    total_count: int = Field(..., description="전체 개수")
    period: Optional[Dict[str, str]] = Field(None, description="조회 기간")
    statistics: Optional[List[Any]] = Field(None, description="통계 데이터")
    summary: Optional[Dict[str, Any]] = Field(None, description="요약 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 5000,
                "period": {
                    "start": "2025-09-01",
                    "end": "2025-09-30"
                },
                "summary": {
                    "total_pharmacies": 5000,
                    "total_prints": 100000,
                    "average_prints_per_pharmacy": 20
                }
            }
        }


# Update forward references
RegionStatistics.model_rebuild()
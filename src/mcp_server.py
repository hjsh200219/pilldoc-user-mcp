import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.mcp_tools import (
    register_auth_tools,
    register_pilldoc_tools,
)
from src.mcp_tools.medical_institution_tools import register_medical_institution_tools
from src.mcp_tools.product_orders_tools import register_product_orders_tools
from src.mcp_tools.stats_tools import register_stats_tools
from src.mcp_tools.database_tools import register_database_tools


# Load env once
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)


def create_server() -> FastMCP:
    mcp = FastMCP("pilldoc-user-mcp")
    
    # Tool 사용 가이드라인 System Prompt 등록
    @mcp.prompt("tool_usage_guide")
    def tool_usage_guide() -> str:
        """Tool 사용 가이드라인"""
        return """
다음 규칙에 따라 tool을 사용하세요:

1. 인증 관련 tools (auth_tools):
   - 로그인 후 토큰을 안전하게 저장
   - 토큰 만료 시 자동 재로그인 처리
   - 민감한 인증 정보는 로그에 노출하지 않음

2. 약국 관련 tools (pharmacy_tools):
   - 약국 검색 시 적절한 필터 조건 사용
   - 대량 데이터 조회 시 페이징 처리
   - 약국 정보 수정 전 기존 데이터 확인

3. 계정 관리 tools (accounts_tools):
   - 계정 생성/수정 시 필수 필드 검증
   - 권한 변경 시 현재 권한 레벨 확인
   - 계정 삭제는 반드시 사용자 확인 후 실행

4. 캠페인 관리 tools (campaign_tools):
   - 캠페인 생성 시 시작/종료 날짜 검증
   - 예산 설정 시 한도 확인
   - 캠페인 상태 변경 시 영향도 검토

5. 통계 관련 tools (stats_tools):
   - 날짜 범위는 합리적인 기간으로 제한
   - 대용량 통계 데이터는 청크 단위로 처리
   - 실시간 통계는 캐싱 활용
   - ERP 통계: get_erp_statistics로 ERP 코드별 약국 수와 출력 수 조회
   - 지역별 통계: get_region_statistics로 시도/시군구별 약국 수와 출력 수 조회
   - 날짜 형식은 YYYY-MM-DD 사용 (예: 2025-09-25)
   - 지역 검색은 부분 검색 지원 (예: '서울' → '서울특별시')

6. 요양기관기호 관련 tools (medical_institution_tools):
   - 8자리 숫자 형식 검증 필수
   - 지역코드(1-2자리)와 종별구분(3자리) 유효성 확인
   - 요양병원 특별 규칙 적용 (3자리:2, 4자리:8)
   - 대량 코드 분석 시 패턴 분석 도구 활용
   - 잘못된 코드는 상세한 오류 정보 제공

7. 상품 주문 관리 tools (product_orders_tools):
   - 날짜 형식은 YYYY-MM-DD 사용 (예: 2025-09-25)
   - 상태코드 확인: 0=결제진행중, 1=결제완료, 2=취소/환불
   - 페이징 처리 시 적절한 page_size 설정 (기본 20)
   - 통계 분석 시 충분한 데이터 수집을 위해 page_size 증가
   - 검색 시 search_type 활용하여 정확한 검색 수행
   - 대화 길이 제한 방지: summary_only=true 또는 전용 요약 도구 사용

8. 데이터베이스 관리 tools (database_tools):
   - PostgreSQL salesdb의 institutions 테이블 직접 접근
   - 페이징 처리: limit/offset 파라미터 활용 (기본 limit=100)
   - 검색 기능: 기관명, 유형, 지역별 필터링 지원
   - 스키마 조회: get_institutions_schema로 테이블 구조 확인
   - 통계 정보: get_institutions_stats로 분포 현황 파악
   - 커스텀 쿼리: execute_institutions_query (SELECT만 허용)
   - 보안: 읽기 전용 접근, 쿼리 결과 제한, 파라미터 바인딩 사용

9. 대화 길이 제한 방지 원칙:
   - 대량 데이터 조회 시 반드시 summary_only=true 옵션 활용
   - max_items 파라미터로 결과 개수 제한 (기본 50개)
   - 요약 전용 도구 우선 사용 (예: get_order_summary)
   - 상세 조회가 필요한 경우에만 전체 데이터 반환
   - 페이징을 활용하여 단계별 데이터 조회

10. 일반 원칙:
   - 모든 데이터 조회는 LIMIT 절 포함
   - 절대 경로 사용 권장
   - 중요한 작업은 사용자 확인 후 실행
   - 에러 발생 시 명확한 에러 메시지 제공
   - API 호출 시 적절한 타임아웃 설정
"""
    
    register_auth_tools(mcp)
    register_pilldoc_tools(mcp)
    register_medical_institution_tools(mcp)
    register_product_orders_tools(mcp)
    register_stats_tools(mcp)
    register_database_tools(mcp)
    return mcp


if __name__ == "__main__":
    create_server().run()



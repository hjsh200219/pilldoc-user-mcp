import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.mcp_tools import (
    register_auth_tools,
    register_pilldoc_service_tools,
)
from src.mcp_tools.medical_institution_tools import register_medical_institution_tools
from src.mcp_tools.product_orders_tools import register_product_orders_tools
from src.mcp_tools.pilldoc_statistics_tools import register_pilldoc_statistics_tools
from src.mcp_tools.national_medical_institutions_tools import register_national_medical_institutions_tools


# Load env once
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)


def create_server() -> FastMCP:
    mcp = FastMCP("pilldoc-user-mcp")
    
    # Tool 사용 가이드라인 System Prompt 등록
    @mcp.prompt("tool_usage_guide")
    def tool_usage_guide() -> str:
        """Tool 사용 가이드라인 - 올바른 도구 선택을 위한 가이드"""
        return """
🎯 TOOL 선택 가이드 - 목적에 맞는 도구 사용하기

=== 데이터 소스별 도구 구분 ===

🏥 전국 의료기관 데이터 (national_medical_institutions_tools):
- 소스: PostgreSQL salesdb의 institutions 테이블
- 내용: 전국 모든 의료기관 (의원, 병원, 약국, 치과 등)
- 용도: 전국 의료기관 현황, 지역별 의료기관 분포 분석
- 도구: get_institutions_distribution_by_region_and_type, get_institutions

💊 PillDoc 서비스 가입자 데이터 (pilldoc_statistics_tools, accounts_tools):
- 소스: PillDoc(필독) 서비스 - 이디비(EDB) 제공
- 내용: PillDoc 서비스에 가입한 약국들 (전체 의료기관의 부분집합)
- 용도: PillDoc 가입 약국 통계, 서비스 이용 현황 분석
- 도구: get_accounts_stats, get_erp_statistics, get_region_statistics

🔍 PillDoc 가입 약국 관리 (pilldoc_pharmacy_tools):
- 소스: PillDoc 서비스 API
- 내용: PillDoc 가입 약국의 상세 정보 및 관리 기능
- 용도: 개별 약국 검색, 약국 정보 조회, 약국 관리
- 도구: find_pharm, pilldoc_pharm

=== 데이터 조회 목적별 도구 선택 ===

🏥 전국 의료기관 분포 조회 시:
❌ 잘못된 선택: pilldoc_statistics_tools, accounts_tools (PillDoc 가입자만)
✅ 올바른 선택: national_medical_institutions_tools
   - 예: "전국 의원 분포", "서울시 구별 병원 현황"

💊 PillDoc 가입 약국 분포/통계 조회 시:
❌ 잘못된 선택: national_medical_institutions_tools (전체 의료기관)
✅ 올바른 선택: pilldoc_statistics_tools, accounts_tools
   - 예: "PillDoc 가입자 분포", "서비스 이용 통계"

🔍 개별 검색 시:
- PillDoc 가입 약국: pilldoc_pharmacy_tools (find_pharm)
- 전체 의료기관: national_medical_institutions_tools (get_institutions)

=== 구체적인 사용 시나리오 ===

🌏 "서울시 구별 XX 분포는?" 질문 시:
1. "PillDoc 가입자 분포" → accounts_tools: get_accounts_stats
2. "전국 의료기관(의원/병원) 분포" → national_medical_institutions_tools: get_institutions_distribution_by_region_and_type  
3. "PillDoc 출력 통계 분포" → pilldoc_statistics_tools: get_region_statistics

📊 "전국 XX 통계는?" 질문 시:
1. "PillDoc ERP별 출력 통계" → pilldoc_statistics_tools: get_erp_statistics
2. "PillDoc 지역별 출력 통계" → pilldoc_statistics_tools: get_region_statistics
3. "전국 의료기관 유형별 분포" → national_medical_institutions_tools: get_institutions_distribution_by_region_and_type

🔍 검색 질문 시:
1. "XX 약국 찾아줘" (PillDoc 가입) → pilldoc_pharmacy_tools: find_pharm
2. "XX 의료기관 정보" (전체) → national_medical_institutions_tools: get_institutions

💡 핵심 구분 포인트:
- "PillDoc/필독" 언급 시 → pilldoc_statistics_tools, accounts_tools
- "전국 의료기관" 언급 시 → national_medical_institutions_tools
- "가입자/서비스" 언급 시 → pilldoc_statistics_tools, accounts_tools
- "출력/통계" 언급 시 → pilldoc_statistics_tools
- 개별 검색 시 → pilldoc_pharmacy_tools (가입자), national_medical_institutions_tools (전체)

🚨 애매한 질문 처리 원칙:
- "약국", "병원", "의원" 등 의료기관 언급 시 데이터 소스 불분명한 경우
- 반드시 사용자에게 확인 요청:
  1. "전국 모든 의료기관 데이터" vs "PillDoc 가입자 데이터" 
  2. 각각의 범위와 차이점 설명
  3. 사용자 선택 후 해당 도구 사용
- 추측하지 말고 명확한 확인 후 진행

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

5. PillDoc 통계 관련 tools (pilldoc_statistics_tools):
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

8. 전국 의료기관 데이터 관리 tools (national_medical_institutions_tools):
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
    register_pilldoc_service_tools(mcp)
    register_medical_institution_tools(mcp)
    register_product_orders_tools(mcp)
    register_pilldoc_statistics_tools(mcp)
    register_national_medical_institutions_tools(mcp)
    return mcp


if __name__ == "__main__":
    create_server().run()
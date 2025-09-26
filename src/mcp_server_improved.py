"""개선된 MCP 서버 - 로깅, 메트릭, 에러 처리 통합"""
import os
import sys
import signal
import logging
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 설정 및 유틸리티 임포트
from src.config import get_settings
from src.utils.logging import setup_logging, get_logger
from src.utils.metrics import get_global_metrics, reset_global_metrics

# 도구 등록 함수들
from src.mcp_tools import (
    register_auth_tools,
    register_pilldoc_service_tools,
)
from src.mcp_tools.medical_institution_tools import register_medical_institution_tools
from src.mcp_tools.product_orders_tools import register_product_orders_tools
from src.mcp_tools.pilldoc_statistics_tools import register_pilldoc_statistics_tools
from src.mcp_tools.national_medical_institutions_tools import register_national_medical_institutions_tools

# 환경 변수 로드
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)

logger = get_logger(__name__)


def setup_signal_handlers(mcp: FastMCP):
    """시그널 핸들러 설정"""
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received, shutting down gracefully...")

        # 메트릭 저장
        settings = get_settings()
        if settings.enable_metrics and settings.metrics_export_path:
            metrics = get_global_metrics()
            logger.info(f"Final metrics: {metrics}")

            # 메트릭을 파일로 저장
            import json
            with open(settings.metrics_export_path, 'w') as f:
                json.dump(metrics, f, indent=2)

        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def create_server() -> FastMCP:
    """개선된 MCP 서버 생성"""
    settings = get_settings()

    # 로깅 설정
    setup_logging(settings.log_level, settings.log_file)
    logger.info(f"Starting {settings.server_name} MCP server")
    logger.info(f"Configuration loaded: base_url={settings.edb_base_url}, timeout={settings.timeout}s")

    # MCP 인스턴스 생성
    mcp = FastMCP(settings.server_name)

    # 시그널 핸들러 설정
    setup_signal_handlers(mcp)

    # 메트릭 도구 추가
    @mcp.tool()
    def get_server_metrics() -> dict:
        """서버 메트릭 조회

        Returns:
            서버 운영 메트릭 (호출 수, 성공률, 평균 응답시간 등)
        """
        logger.info("Metrics requested")
        return get_global_metrics()

    @mcp.tool()
    def reset_server_metrics() -> dict:
        """서버 메트릭 초기화

        Returns:
            초기화 결과 메시지
        """
        logger.info("Resetting metrics")
        reset_global_metrics()
        return {"success": True, "message": "메트릭이 초기화되었습니다"}

    # 헬스체크 도구
    @mcp.tool()
    def health_check() -> dict:
        """서버 상태 확인

        Returns:
            서버 상태 정보
        """
        return {
            "status": "healthy",
            "server": settings.server_name,
            "version": "1.0.0",
            "uptime": get_global_metrics().get("uptime_formatted", "unknown")
        }

    # 설정 조회 도구 (민감한 정보 제외)
    @mcp.tool()
    def get_server_config() -> dict:
        """서버 설정 조회 (민감한 정보 제외)

        Returns:
            공개 가능한 서버 설정 정보
        """
        return {
            "server_name": settings.server_name,
            "base_url": settings.edb_base_url,
            "timeout": settings.timeout,
            "max_retries": settings.max_retries,
            "default_page_size": settings.default_page_size,
            "max_page_size": settings.max_page_size,
            "metrics_enabled": settings.enable_metrics,
            "log_level": settings.log_level
        }

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

=== 서버 관리 도구 ===

📊 메트릭 및 모니터링:
- get_server_metrics: 서버 운영 메트릭 조회
- reset_server_metrics: 메트릭 초기화
- health_check: 서버 상태 확인
- get_server_config: 서버 설정 조회

=== 사용 원칙 ===

1. 데이터 범위 명확히 구분:
   - "전국" 언급 시 → national_medical_institutions_tools
   - "PillDoc/필독" 언급 시 → pilldoc_statistics_tools
   - 애매한 경우 반드시 사용자에게 확인

2. 성능 최적화:
   - 대량 데이터 조회 시 summary_only=true 사용
   - 페이지네이션 적절히 활용
   - 불필요한 중복 호출 방지

3. 에러 처리:
   - 토큰 만료 시 자동 재인증
   - API 오류 시 명확한 에러 메시지 제공
   - 재시도 가능한 오류는 자동 재시도

4. 보안 준수:
   - 민감한 정보는 로그에 노출하지 않음
   - 인증 정보는 환경 변수 사용
   - 중요한 작업은 사용자 확인 후 실행
"""

    # 개선된 오류 안내 프롬프트
    @mcp.prompt("error_handling_guide")
    def error_handling_guide() -> str:
        """에러 처리 가이드"""
        return """
🚨 에러 처리 가이드

=== 일반적인 에러와 해결 방법 ===

1. 인증 에러 (AUTH_ERROR):
   - 원인: 토큰 만료, 잘못된 자격 증명
   - 해결: 토큰 갱신 또는 올바른 자격 증명 제공

2. 검증 에러 (VALIDATION_ERROR):
   - 원인: 필수 파라미터 누락, 잘못된 형식
   - 해결: 파라미터 확인 및 올바른 형식으로 재시도

3. API 에러 (API_ERROR):
   - 원인: 외부 API 호출 실패
   - 해결: 네트워크 연결 확인, API 상태 확인

4. 내부 에러 (INTERNAL_ERROR):
   - 원인: 예상치 못한 서버 오류
   - 해결: 로그 확인, 서버 재시작

=== 에러 응답 형식 ===

모든 에러는 다음 형식으로 반환됩니다:
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "사용자 친화적 메시지",
        "details": {
            // 추가 디버깅 정보
        }
    }
}

=== 자동 복구 메커니즘 ===

- 토큰 만료: 자동 재인증 시도
- 네트워크 오류: 3회 재시도 (지수 백오프)
- 중복 로그인: 강제 재로그인

=== 문제 해결 단계 ===

1. 에러 코드 확인
2. 에러 메시지의 안내 따르기
3. 메트릭 조회로 전반적 상태 확인
4. 필요시 서버 재시작
"""

    # 기존 도구들 등록
    logger.info("Registering tools...")
    try:
        register_auth_tools(mcp)
        register_pilldoc_service_tools(mcp)
        register_medical_institution_tools(mcp)
        register_product_orders_tools(mcp)
        register_pilldoc_statistics_tools(mcp)
        register_national_medical_institutions_tools(mcp)
        logger.info("All tools registered successfully")
    except Exception as e:
        logger.error(f"Failed to register tools: {e}", exc_info=True)
        raise

    return mcp


def main():
    """메인 실행 함수"""
    try:
        server = create_server()
        logger.info("MCP server started successfully")
        server.run()
    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
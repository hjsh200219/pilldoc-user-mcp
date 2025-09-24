import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from src.mcp_tools import (
    register_auth_tools,
    register_pilldoc_tools,
)


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

6. 일반 원칙:
   - 모든 데이터 조회는 LIMIT 절 포함
   - 절대 경로 사용 권장
   - 중요한 작업은 사용자 확인 후 실행
   - 에러 발생 시 명확한 에러 메시지 제공
   - API 호출 시 적절한 타임아웃 설정
"""
    
    register_auth_tools(mcp)
    register_pilldoc_tools(mcp)
    return mcp


if __name__ == "__main__":
    create_server().run()



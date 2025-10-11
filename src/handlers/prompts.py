"""MCP 프롬프트 핸들러 설정"""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import Prompt, PromptMessage, PromptArgument, GetPromptResult, TextContent

logger = logging.getLogger(__name__)


def setup_prompt_handlers(server: Server):
    """프롬프트 핸들러 설정

    Args:
        server: MCP 서버 인스턴스
    """

    @server.list_prompts()
    async def handle_list_prompts() -> list[Prompt]:
        """프롬프트 목록 반환"""
        return [
            Prompt(
                name="tool_usage_guide",
                description="Tool 사용 가이드라인",
                arguments=[],
            )
        ]

    @server.get_prompt()
    async def handle_get_prompt(
        name: str,
        arguments: dict[str, str] | None = None
    ) -> GetPromptResult:
        """프롬프트 가져오기"""
        if name == "tool_usage_guide":
            content = """
🎯 TOOL 선택 가이드 - 목적에 맞는 도구 사용하기

=== 데이터 소스별 도구 구분 ===

🏥 전국 의료기관 데이터:
- 소스: PostgreSQL salesdb의 institutions 테이블
- 내용: 전국 모든 의료기관 (의원, 병원, 약국, 치과 등)
- 용도: 전국 의료기관 현황, 지역별 의료기관 분포 분석

💊 PillDoc 서비스 가입자 데이터:
- 소스: PillDoc(필독) 서비스 - 이디비(EDB) 제공
- 내용: PillDoc 서비스에 가입한 약국들
- 용도: PillDoc 가입 약국 통계, 서비스 이용 현황 분석

=== 주요 원칙 ===

1. 인증 관련:
   - 로그인 후 토큰을 안전하게 저장
   - 토큰 만료 시 자동 재로그인 처리

2. 약국 관련:
   - 약국 검색 시 적절한 필터 조건 사용
   - 대량 데이터 조회 시 페이징 처리

3. 일반 원칙:
   - 모든 데이터 조회는 LIMIT 절 포함
   - 중요한 작업은 사용자 확인 후 실행
"""

            return GetPromptResult(
                description="Tool 사용 가이드라인",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=content
                        )
                    )
                ]
            )

        raise ValueError(f"Unknown prompt: {name}")

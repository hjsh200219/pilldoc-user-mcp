"""PillDoc 서비스 통합 도구들 - 모든 PillDoc 관련 도구들의 통합 등록"""
from mcp.server.fastmcp import FastMCP

# 개별 모듈에서 도구들 import
from .accounts_tools import register_accounts_tools
from .pilldoc_pharmacy_tools import register_pilldoc_pharmacy_tools
from .campaign_tools import register_campaign_tools
from .pilldoc_statistics_tools import register_pilldoc_statistics_tools


def register_pilldoc_service_tools(mcp: FastMCP) -> None:
    """모든 PillDoc 서비스 도구들을 등록합니다."""

    # 각 카테고리별 도구 등록
    register_accounts_tools(mcp)
    register_pilldoc_pharmacy_tools(mcp)
    register_campaign_tools(mcp)
    register_pilldoc_statistics_tools(mcp)
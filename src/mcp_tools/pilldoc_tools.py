"""MCP 도구 등록 - 리팩토링된 버전"""
from mcp.server.fastmcp import FastMCP

# 개별 모듈에서 도구들 import
from .accounts_tools import register_accounts_tools
from .pharmacy_tools import register_pharmacy_tools
from .campaign_tools import register_campaign_tools
from .stats_tools import register_stats_tools


def register_pilldoc_tools(mcp: FastMCP) -> None:
    """모든 Pilldoc 도구들을 등록합니다."""

    # 각 카테고리별 도구 등록
    register_accounts_tools(mcp)
    register_pharmacy_tools(mcp)
    register_campaign_tools(mcp)
    register_stats_tools(mcp)
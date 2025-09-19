"""캠페인 관련 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_rejected_campaigns, post_rejected_campaign
from .helpers import need_base_url, ensure_token, normalize_bizno, handle_http_error


def register_campaign_tools(mcp: FastMCP) -> None:
    """캠페인 관련 도구들 등록"""

    @mcp.tool()
    def pilldoc_adps_rejects(
        bizNo: str,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """차단된 캠페인 목록 조회"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)
        bizNo = normalize_bizno(bizNo)
        try:
            return get_rejected_campaigns(base_url, tok, bizNo, accept, timeout)
        except _req.HTTPError as e:
            return handle_http_error(e)

    @mcp.tool()
    def pilldoc_adps_reject(
        bizNo: str,
        campaignId: int,
        comment: str,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """캠페인 차단/차단해제"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)
        bizNo = normalize_bizno(bizNo)
        try:
            return post_rejected_campaign(base_url, tok, bizNo, int(campaignId), str(comment), accept, timeout)
        except _req.HTTPError as e:
            return handle_http_error(e)
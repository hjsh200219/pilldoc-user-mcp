"""캠페인 관련 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_rejected_campaigns, post_rejected_campaign
from .helpers import need_base_url, ensure_token, normalize_bizno, handle_http_error


def register_campaign_tools(mcp: FastMCP) -> None:
    """캠페인 관련 도구들 등록"""

    @mcp.tool()
    def pilldoc_campaign(
        bizNo: str,
        action: str = "list",  # list, block, unblock
        campaignId: Optional[int] = None,
        comment: Optional[str] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """캠페인 관리 (통합 도구)

        액션:
        - list: 차단된 캠페인 목록 조회 (기본값)
        - block: 캠페인 차단 (campaignId, comment 필요)
        - unblock: 캠페인 차단해제 (campaignId, comment 필요)
        """
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)
        bizNo = normalize_bizno(bizNo)

        try:
            if action == "list":
                return get_rejected_campaigns(base_url, tok, bizNo, accept, timeout)

            elif action in ("block", "unblock"):
                if campaignId is None:
                    raise RuntimeError(f"{action} 액션에는 campaignId가 필요합니다.")
                if comment is None:
                    comment = f"캠페인 {action} 처리"
                return post_rejected_campaign(base_url, tok, bizNo, int(campaignId), str(comment), accept, timeout)

            else:
                raise RuntimeError(f"알 수 없는 액션: {action}. list, block, unblock 중 하나를 선택하세요.")

        except _req.HTTPError as e:
            return handle_http_error(e)
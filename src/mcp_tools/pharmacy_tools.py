"""약국 검색 및 관리 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_accounts, get_user, get_pharm, get_rejected_campaigns
from .helpers import (
    need_base_url, ensure_token, items_of, normalize_bizno,
    handle_http_error
)


def register_pharmacy_tools(mcp: FastMCP) -> None:
    """약국 관련 도구들 등록"""

    @mcp.tool()
    def pilldoc_pharm(
        bizno: str,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """약국 정보 조회"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)
        try:
            return get_pharm(base_url, tok, bizno, accept, timeout)
        except _req.HTTPError as e:
            return handle_http_error(e)

    @mcp.tool()
    def pilldoc_find_pharm_by_name(
        name: str,
        exact: bool = True,
        maxPages: int = 0,
        pageSize: int = 100,
        stopOnFirst: bool = True,
        usePharmDetail: bool = True,
        currentSearchType: Optional[list] = None,
        accountType: Optional[str] = None,
        pharmChain: Optional[list] = None,
        salesChannel: Optional[list] = None,
        erpKind: Optional[list] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """약국명으로 약국 검색"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        matches = []
        checked = 0
        searched_pages = 0

        page = 1
        last_page: Optional[int] = None
        while True:
            filters: Dict[str, Any] = {"page": page, "pageSize": int(pageSize), "searchKeyword": name}
            if currentSearchType is not None:
                filters["currentSearchType"] = list(currentSearchType)
            if accountType is not None:
                filters["accountType"] = str(accountType)
            if pharmChain is not None:
                filters["pharmChain"] = list(pharmChain)
            if salesChannel is not None:
                filters["salesChannel"] = list(salesChannel)
            if erpKind is not None:
                filters["erpKind"] = list(erpKind)

            try:
                resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
            except _req.HTTPError as e:
                result = handle_http_error(e)
                result["page"] = page
                return result

            if last_page is None:
                try:
                    total_page = int(resp.get("totalPage")) if isinstance(resp, dict) and resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = items_of(resp)
            if not items:
                break
            searched_pages += 1

            for it in items:
                if not isinstance(it, dict):
                    continue
                pharm_name = str(it.get("약국명") or "").strip()
                if not pharm_name:
                    continue
                checked += 1
                if exact:
                    if pharm_name == name:
                        matches.append(it)
                else:
                    if name in pharm_name:
                        matches.append(it)

                # 보조 검사: 계정의 약국명이 다르더라도 약국 상세에서 정확 일치할 수 있음
                if not matches and usePharmDetail and exact:
                    biz_no_val = normalize_bizno(str(it.get("bizNO") or "").strip())
                    if biz_no_val:
                        try:
                            p = get_pharm(base_url, tok, biz_no_val, accept, timeout)
                            pharm_data = p.get("data") if isinstance(p, dict) else None
                            detail_name = str(pharm_data.get("약국명") or "").strip() if isinstance(pharm_data, dict) else ""
                            if detail_name == name:
                                matches.append(it)
                        except Exception:
                            pass

                if stopOnFirst and exact and matches:
                    break

            if stopOnFirst and exact and matches:
                break
            if last_page is not None and page >= last_page:
                break
            page += 1

        return {"matches": matches, "searchedPages": searched_pages, "totalChecked": checked}

    @mcp.tool()
    def pilldoc_find_pharm(
        pharmName: Optional[str] = None,
        ownerName: Optional[str] = None,
        bizNo: Optional[str] = None,
        exact: bool = True,
        maxPages: int = 0,
        pageSize: int = 100,
        stopOnFirst: bool = True,
        usePharmDetail: bool = True,
        currentSearchType: Optional[list] = None,
        accountType: Optional[str] = None,
        pharmChain: Optional[list] = None,
        salesChannel: Optional[list] = None,
        erpKind: Optional[list] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """약국 검색 (다양한 필터 지원)"""
        if not (pharmName or ownerName or bizNo):
            raise RuntimeError("pharmName, ownerName, bizNo 중 하나는 지정해야 합니다.")

        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        def _matches(it: Dict[str, Any]) -> bool:
            name_val = str(it.get("약국명") or "").strip()
            owner_val = str(it.get("displayName") or "").strip()
            biz_val = str(it.get("bizNO") or "").strip()
            conds = []
            if pharmName is not None:
                conds.append(name_val == pharmName if exact else (pharmName in name_val))
            if ownerName is not None:
                conds.append(owner_val == ownerName if exact else (ownerName in owner_val))
            if bizNo is not None:
                conds.append(biz_val == bizNo if exact else (bizNo in biz_val))
            return all(conds) if conds else False

        matches = []
        checked = 0
        searched_pages = 0

        page = 1
        last_page: Optional[int] = None
        bizNo = normalize_bizno(bizNo)
        while True:
            search_keyword = bizNo or pharmName or ownerName
            filters: Dict[str, Any] = {"page": page, "pageSize": int(pageSize)}
            if search_keyword:
                filters["searchKeyword"] = search_keyword
            if currentSearchType is not None:
                filters["currentSearchType"] = list(currentSearchType)
            if accountType is not None:
                filters["accountType"] = str(accountType)
            if pharmChain is not None:
                filters["pharmChain"] = list(pharmChain)
            if salesChannel is not None:
                filters["salesChannel"] = list(salesChannel)
            if erpKind is not None:
                filters["erpKind"] = list(erpKind)

            try:
                resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
            except _req.HTTPError as e:
                result = handle_http_error(e)
                result["page"] = page
                return result

            if last_page is None:
                try:
                    total_page = int(resp.get("totalPage")) if isinstance(resp, dict) and resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = items_of(resp)
            if not items:
                break
            searched_pages += 1

            for it in items:
                if not isinstance(it, dict):
                    continue
                checked += 1
                matched = _matches(it)
                if matched:
                    matches.append(it)
                # 계정명 불일치시 약국 상세에서 정확 매칭 확인
                elif usePharmDetail and pharmName and exact:
                    biz_no_val = normalize_bizno(str(it.get("bizNO") or "").strip())
                    if biz_no_val:
                        try:
                            p = get_pharm(base_url, tok, biz_no_val, accept, timeout)
                            pharm_data = p.get("data") if isinstance(p, dict) else None
                            detail_name = str(pharm_data.get("약국명") or "").strip() if isinstance(pharm_data, dict) else ""
                            if detail_name == pharmName:
                                matches.append(it)
                        except Exception:
                            pass

                if stopOnFirst and exact and matches:
                    break

            if stopOnFirst and exact and matches:
                break
            if last_page is not None and page >= last_page:
                break
            page += 1

        enriched = []
        for account in matches:
            user_detail: Any = None
            pharm_detail: Any = None
            adps_rejects: Any = None

            user_id_val = None
            for key in ("id", "Id", "userId", "UserId", "accountId", "AccountId"):
                if key in account and account[key] is not None and str(account[key]).strip() != "":
                    user_id_val = str(account[key]).strip()
                    break

            biz_no_val = None
            for key in ("bizNO", "bizNo", "사업자등록번호"):
                if key in account and account[key] is not None and str(account[key]).strip() != "":
                    biz_no_val = str(account[key]).strip()
                    break

            if user_id_val:
                try:
                    user_detail = get_user(base_url, tok, user_id_val, accept, timeout)
                except _req.HTTPError as e:
                    user_detail = handle_http_error(e)

            if biz_no_val:
                try:
                    pharm_detail = get_pharm(base_url, tok, biz_no_val, accept, timeout)
                except _req.HTTPError as e:
                    pharm_detail = handle_http_error(e)

                # adps reject campaigns
                try:
                    adps_rejects = get_rejected_campaigns(base_url, tok, biz_no_val, accept, timeout)
                except _req.HTTPError as e:
                    adps_rejects = handle_http_error(e)

            enriched.append({"account": account, "user": user_detail, "pharm": pharm_detail, "adpsRejects": adps_rejects})

        return {"matches": enriched, "searchedPages": searched_pages, "totalChecked": checked}
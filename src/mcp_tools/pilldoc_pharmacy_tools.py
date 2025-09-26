"""PillDoc 가입 약국 검색 및 관리 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_accounts, get_user, get_pharm, get_rejected_campaigns
from .helpers import (
    need_base_url, ensure_token, items_of, normalize_bizno,
    handle_http_error, normalize_filter_params
)


def register_pilldoc_pharmacy_tools(mcp: FastMCP) -> None:
    """PillDoc 가입 약국 관련 도구들 등록"""

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
        max_pages: Optional[int] = None,
        pageSize: int = 100,
        page_size: Optional[int] = None,
        size: Optional[int] = None,
        limit: Optional[int] = None,
        stopOnFirst: bool = True,
        stop_on_first: Optional[bool] = None,
        usePharmDetail: bool = True,
        use_pharm_detail: Optional[bool] = None,
        currentSearchType: Optional[list] = None,
        search_type: Optional[list] = None,
        searchType: Optional[list] = None,
        accountType: Optional[str] = None,
        account_type: Optional[str] = None,
        pharmChain: Optional[list] = None,
        pharm_chain: Optional[list] = None,
        chain: Optional[list] = None,
        salesChannel: Optional[list] = None,
        sales_channel: Optional[list] = None,
        channel: Optional[list] = None,
        erpKind: Optional[list] = None,
        erp_kind: Optional[list] = None,
        erp: Optional[list] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        **kwargs
    ) -> Dict[str, Any]:
        """약국명으로 약국 검색"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # 파라미터 통합
        maxPages = max_pages if max_pages is not None else maxPages
        stopOnFirst = stop_on_first if stop_on_first is not None else stopOnFirst
        usePharmDetail = use_pharm_detail if use_pharm_detail is not None else usePharmDetail

        # 필터 파라미터 수집 및 정규화
        filter_params = {}
        if pageSize is not None: filter_params["pageSize"] = pageSize
        if page_size is not None: filter_params["page_size"] = page_size
        if size is not None: filter_params["size"] = size
        if limit is not None: filter_params["limit"] = limit
        if currentSearchType is not None: filter_params["currentSearchType"] = currentSearchType
        if search_type is not None: filter_params["search_type"] = search_type
        if searchType is not None: filter_params["searchType"] = searchType
        if accountType is not None: filter_params["accountType"] = accountType
        if account_type is not None: filter_params["account_type"] = account_type
        if pharmChain is not None: filter_params["pharmChain"] = pharmChain
        if pharm_chain is not None: filter_params["pharm_chain"] = pharm_chain
        if chain is not None: filter_params["pharmChain"] = chain
        if salesChannel is not None: filter_params["salesChannel"] = salesChannel
        if sales_channel is not None: filter_params["sales_channel"] = sales_channel
        if channel is not None: filter_params["salesChannel"] = channel
        if erpKind is not None: filter_params["erpKind"] = erpKind
        if erp_kind is not None: filter_params["erp_kind"] = erp_kind
        if erp is not None: filter_params["erp"] = erp
        filter_params.update(kwargs)

        normalized = normalize_filter_params(filter_params)

        matches = []
        checked = 0
        searched_pages = 0

        page = 1
        last_page: Optional[int] = None
        while True:
            filters: Dict[str, Any] = {
                "page": page,
                "pageSize": normalized.get("pageSize", 100),
                "searchKeyword": name
            }
            if normalized.get("currentSearchType"):
                filters["currentSearchType"] = normalized["currentSearchType"]
            if normalized.get("accountType"):
                filters["accountType"] = normalized["accountType"]
            if normalized.get("pharmChain"):
                filters["pharmChain"] = normalized["pharmChain"]
            if normalized.get("salesChannel"):
                filters["salesChannel"] = normalized["salesChannel"]
            if normalized.get("erpKind"):
                filters["erpKind"] = normalized["erpKind"]

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
        pharm_name: Optional[str] = None,
        pharmacy: Optional[str] = None,
        ownerName: Optional[str] = None,
        owner_name: Optional[str] = None,
        displayName: Optional[str] = None,
        bizNo: Optional[str] = None,
        biz_no: Optional[str] = None,
        bizno: Optional[str] = None,
        exact: bool = True,
        maxPages: int = 0,
        max_pages: Optional[int] = None,
        pageSize: int = 100,
        page_size: Optional[int] = None,
        size: Optional[int] = None,
        limit: Optional[int] = None,
        stopOnFirst: bool = True,
        stop_on_first: Optional[bool] = None,
        usePharmDetail: bool = True,
        use_pharm_detail: Optional[bool] = None,
        currentSearchType: Optional[list] = None,
        search_type: Optional[list] = None,
        searchType: Optional[list] = None,
        accountType: Optional[str] = None,
        account_type: Optional[str] = None,
        pharmChain: Optional[list] = None,
        pharm_chain: Optional[list] = None,
        chain: Optional[list] = None,
        salesChannel: Optional[list] = None,
        sales_channel: Optional[list] = None,
        channel: Optional[list] = None,
        erpKind: Optional[list] = None,
        erp_kind: Optional[list] = None,
        erp: Optional[list] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        **kwargs
    ) -> Dict[str, Any]:
        """약국 검색 (다양한 필터 지원)

        다양한 파라미터 이름을 지원합니다:
        - 약국명: pharmName, pharm_name, pharmacy
        - 약국장: ownerName, owner_name, displayName
        - 사업자번호: bizNo, biz_no, bizno
        - 체인: pharmChain, pharm_chain, chain
        - 채널: salesChannel, sales_channel, channel
        - ERP: erpKind, erp_kind, erp
        """
        # 파라미터 통합
        pharmName = pharmName or pharm_name or pharmacy
        ownerName = ownerName or owner_name or displayName
        bizNo = bizNo or biz_no or bizno
        maxPages = max_pages if max_pages is not None else maxPages
        stopOnFirst = stop_on_first if stop_on_first is not None else stopOnFirst
        usePharmDetail = use_pharm_detail if use_pharm_detail is not None else usePharmDetail

        if not (pharmName or ownerName or bizNo):
            raise RuntimeError("pharmName, ownerName, bizNo 중 하나는 지정해야 합니다.")

        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # 필터 파라미터 수집 및 정규화
        filter_params = {}
        if pageSize is not None: filter_params["pageSize"] = pageSize
        if page_size is not None: filter_params["page_size"] = page_size
        if size is not None: filter_params["size"] = size
        if limit is not None: filter_params["limit"] = limit
        if currentSearchType is not None: filter_params["currentSearchType"] = currentSearchType
        if search_type is not None: filter_params["search_type"] = search_type
        if searchType is not None: filter_params["searchType"] = searchType
        if accountType is not None: filter_params["accountType"] = accountType
        if account_type is not None: filter_params["account_type"] = account_type
        if pharmChain is not None: filter_params["pharmChain"] = pharmChain
        if pharm_chain is not None: filter_params["pharm_chain"] = pharm_chain
        if chain is not None: filter_params["pharmChain"] = chain
        if salesChannel is not None: filter_params["salesChannel"] = salesChannel
        if sales_channel is not None: filter_params["sales_channel"] = sales_channel
        if channel is not None: filter_params["salesChannel"] = channel
        if erpKind is not None: filter_params["erpKind"] = erpKind
        if erp_kind is not None: filter_params["erp_kind"] = erp_kind
        if erp is not None: filter_params["erp"] = erp
        filter_params.update(kwargs)

        normalized = normalize_filter_params(filter_params)

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
            filters: Dict[str, Any] = {
                "page": page,
                "pageSize": normalized.get("pageSize", 100)
            }
            if search_keyword:
                filters["searchKeyword"] = search_keyword
            if normalized.get("currentSearchType"):
                filters["currentSearchType"] = normalized["currentSearchType"]
            if normalized.get("accountType"):
                filters["accountType"] = normalized["accountType"]
            if normalized.get("pharmChain"):
                filters["pharmChain"] = normalized["pharmChain"]
            if normalized.get("salesChannel"):
                filters["salesChannel"] = normalized["salesChannel"]
            if normalized.get("erpKind"):
                filters["erpKind"] = normalized["erpKind"]

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
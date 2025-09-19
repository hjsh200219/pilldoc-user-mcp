"""계정 관련 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_accounts, get_user, update_account
from .helpers import (
    need_base_url, ensure_token, items_of, normalize_bizno,
    is_ad_display_from_item, client_sort_items, handle_http_error
)
from .filter_builder import FilterBuilder


def register_accounts_tools(mcp: FastMCP) -> None:
    """계정 관련 도구들 등록"""

    @mcp.tool()
    def pilldoc_accounts(
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        pageSize: Optional[int] = None,
        page: Optional[int] = None,
        page_no: Optional[int] = None,
        page_count: Optional[int] = None,
        sortBy: Optional[str] = None,
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
        enforceSortLocal: bool = False,
    ) -> Dict[str, Any]:
        """계정 목록 조회"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        filters = FilterBuilder.build_account_filters(
            pageSize=pageSize,
            page=page,
            page_no=page_no,
            page_count=page_count,
            sortBy=sortBy,
            erpKind=erpKind,
            isAdDisplay=isAdDisplay,
            salesChannel=salesChannel,
            pharmChain=pharmChain,
            currentSearchType=currentSearchType,
            searchKeyword=searchKeyword,
            accountType=accountType
        )

        try:
            resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
            # 서버 정렬 미적용 대비: 클라이언트 보정 정렬(옵션)
            if enforceSortLocal and sortBy is not None and isinstance(resp, dict):
                items = items_of(resp)
                if items:
                    sorted_items = client_sort_items(list(items), sortBy)
                    if isinstance(resp.get("items"), list):
                        resp["items"] = sorted_items
                    elif isinstance(resp.get("data"), list):
                        resp["data"] = sorted_items
            return resp
        except _req.HTTPError as e:
            return handle_http_error(e)

    @mcp.tool()
    def pilldoc_accounts_compact(
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        pageSize: Optional[int] = None,
        page: Optional[int] = None,
        sortBy: Optional[str] = None,
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
        fields: Optional[list] = None,
        includeAdBlockedBool: bool = False,
        includeItems: bool = False,
        limitItems: Optional[int] = None,
        enforceSortLocal: bool = True,
    ) -> Dict[str, Any]:
        """계정 목록을 간결한 형태로 반환합니다. 선택한 필드만 노출하고 adBlocked 불리언을 포함할 수 있습니다.

        기본 필드: ["id", "bizno"] (bizno는 원본의 bizNO/bizNo/사업자등록번호에서 정규화)
        """
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        filters = FilterBuilder.build_account_filters(
            pageSize=pageSize,
            page=page,
            sortBy=sortBy,
            erpKind=erpKind,
            isAdDisplay=isAdDisplay,
            salesChannel=salesChannel,
            pharmChain=pharmChain,
            currentSearchType=currentSearchType,
            searchKeyword=searchKeyword,
            accountType=accountType
        )

        default_fields = ["id", "bizno"]
        wanted = list(fields) if isinstance(fields, list) and fields else default_fields

        def _select_item(it: Dict[str, Any]) -> Dict[str, Any]:
            slim: Dict[str, Any] = {}
            for k in wanted:
                if k == "bizno":
                    raw = it.get("bizNO") or it.get("bizNo") or it.get("사업자등록번호") or it.get("bizno")
                    try:
                        raw = str(raw).strip() if raw is not None else None
                    except Exception:
                        raw = None
                    slim["bizno"] = normalize_bizno(raw)
                else:
                    slim[k] = it.get(k)
            if includeAdBlockedBool:
                isd = is_ad_display_from_item(it)
                slim["isAdDisplay"] = isd
            return slim

        try:
            resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
        except _req.HTTPError as e:
            return handle_http_error(e)

        items = items_of(resp)
        if enforceSortLocal and sortBy is not None and items:
            items = client_sort_items(list(items), sortBy)
        slim_items = [_select_item(it) for it in items if isinstance(it, dict)]
        if limitItems is not None:
            try:
                slim_items = slim_items[: int(limitItems)]
            except Exception:
                pass

        meta: Dict[str, Any] = {}
        if isinstance(resp, dict):
            for key in ("totalCount", "totalPage", "nowPage"):
                if key in resp:
                    meta[key] = resp[key]

        if includeItems:
            meta["items"] = slim_items
        return meta

    @mcp.tool()
    def pilldoc_user(
        id: str,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """사용자 정보 조회"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)
        try:
            return get_user(base_url, tok, id, accept, timeout)
        except _req.HTTPError as e:
            return handle_http_error(e)

    @mcp.tool()
    def pilldoc_user_from_accounts(
        accountField: Optional[str] = None,
        accountValue: Optional[str] = None,
        index: int = 0,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        pageSize: Optional[int] = None,
        page: Optional[int] = None,
        page_no: Optional[int] = None,
        page_count: Optional[int] = None,
        sortBy: Optional[str] = None,
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        adBlocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
        enforceSortLocal: bool = True,
    ) -> Dict[str, Any]:
        """계정 목록에서 사용자 정보 추출"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        filters = FilterBuilder.build_account_filters(
            pageSize=pageSize,
            page=page,
            page_no=page_no,
            page_count=page_count,
            sortBy=sortBy,
            erpKind=erpKind,
            isAdDisplay=isAdDisplay,
            adBlocked=adBlocked,
            salesChannel=salesChannel,
            pharmChain=pharmChain,
            currentSearchType=currentSearchType,
            searchKeyword=searchKeyword,
            accountType=accountType
        )

        try:
            accounts_resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
        except _req.HTTPError as e:
            return handle_http_error(e, "accounts")

        def _extract_list(obj: Any) -> list:
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                for key in ("data", "items", "results", "list"):
                    if key in obj and isinstance(obj[key], list):
                        return obj[key]
            return []

        items = _extract_list(accounts_resp)
        if enforceSortLocal and sortBy is not None and items:
            items = client_sort_items(list(items), sortBy)
        if not items:
            preview_keys = list(accounts_resp.keys()) if isinstance(accounts_resp, dict) else None
            return {"error": "계정 목록을 찾지 못했습니다.", "preview_keys": preview_keys, "raw": accounts_resp}

        selected = None
        if accountField and accountValue is not None:
            for it in items:
                if isinstance(it, dict) and str(it.get(accountField)) == str(accountValue):
                    selected = it
                    break
            if selected is None:
                return {"error": "일치하는 계정을 찾지 못했습니다.", "accountField": accountField, "accountValue": accountValue}
        else:
            if index < 0 or index >= len(items):
                return {"error": "index 범위를 벗어났습니다.", "index": index, "count": len(items)}
            selected = items[index]

        if not isinstance(selected, dict):
            return {"error": "선택된 항목 형식이 올바르지 않습니다.", "selected": selected}

        id_keys = ["id", "Id", "userId", "UserId", "accountId", "AccountId"]
        user_id_value: Optional[str] = None
        for k in id_keys:
            if k in selected and selected[k] is not None and str(selected[k]).strip() != "":
                user_id_value = str(selected[k]).strip()
                break
        if not user_id_value:
            return {"error": "계정 항목에서 id를 찾지 못했습니다.", "available_keys": list(selected.keys())}

        try:
            return get_user(base_url, tok, user_id_value, accept, timeout)
        except _req.HTTPError as e:
            return handle_http_error(e, "user")

    @mcp.tool()
    def pilldoc_update_account(
        id: str,
        body: Dict[str, Any],
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        contentType: str = "application/json",
    ) -> Dict[str, Any]:
        """계정 정보 업데이트"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)
        try:
            return update_account(base_url, tok, id, body, accept, timeout, content_type=contentType)
        except _req.HTTPError as e:
            return handle_http_error(e)

    @mcp.tool()
    def pilldoc_update_account_by_search(
        body: Dict[str, Any],
        pharmName: Optional[str] = None,
        bizNo: Optional[str] = None,
        exact: bool = True,
        index: int = 0,
        accountType: Optional[str] = None,
        currentSearchType: Optional[list] = None,
        pharmChain: Optional[list] = None,
        salesChannel: Optional[list] = None,
        erpKind: Optional[list] = None,
        maxPages: int = 0,
        pageSize: int = 100,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        contentType: str = "application/json",
    ) -> Dict[str, Any]:
        """약국명 또는 사업자등록번호로 계정을 찾아 id를 얻은 뒤 PATCH 수행."""
        if not (pharmName or bizNo):
            raise RuntimeError("pharmName 또는 bizNo 중 하나는 반드시 지정해야 합니다.")

        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # 1) /v1/pilldoc/accounts 페이지네이션 조회
        page = 1
        last_page: Optional[int] = None
        candidates: list = []

        # 기본 검색 타입 보정: bizNo가 주어지면 ['b'], pharmName이면 ['s']
        default_search = ["b"] if bizNo else (["s"] if pharmName else None)

        bizNo = normalize_bizno(bizNo)
        while True:
            filters: Dict[str, Any] = {"page": page, "pageSize": int(pageSize)}
            search_keyword = bizNo or pharmName
            if search_keyword:
                filters["searchKeyword"] = search_keyword
            if currentSearchType is not None:
                filters["currentSearchType"] = list(currentSearchType)
            elif default_search is not None:
                filters["currentSearchType"] = default_search
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
                return handle_http_error(e, "accounts")

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

            def _matches(it: Dict[str, Any]) -> bool:
                name_val = str(it.get("약국명") or "").strip()
                biz_val = normalize_bizno(str(it.get("bizNO") or it.get("bizNo") or "").strip())
                conds = []
                if pharmName is not None:
                    conds.append(name_val == pharmName if exact else (pharmName in name_val))
                if bizNo is not None:
                    conds.append(biz_val == bizNo if exact else (bizNo in biz_val))
                return all(conds) if conds else True

            for it in items:
                if isinstance(it, dict) and _matches(it):
                    candidates.append(it)

            if last_page is not None and page >= last_page:
                break
            page += 1

        if not candidates:
            return {"error": "검색어와 일치하는 항목이 없습니다.", "count": 0}

        if index < 0 or index >= len(candidates):
            return {"error": "index 범위를 벗어났습니다.", "index": index, "count": len(candidates)}

        selected = candidates[index]
        if not isinstance(selected, dict):
            return {"error": "선택된 항목 형식이 올바르지 않습니다.", "selected": selected}

        # 3) id 추출
        id_keys = ["id", "Id", "userId", "UserId", "accountId", "AccountId"]
        user_id_value: Optional[str] = None
        for k in id_keys:
            if k in selected and selected[k] is not None and str(selected[k]).strip() != "":
                user_id_value = str(selected[k]).strip()
                break
        if not user_id_value:
            return {"error": "계정 항목에서 id를 찾지 못했습니다.", "available_keys": list(selected.keys())}

        # 4) PATCH /v1/pilldoc/account/{id}
        try:
            result = update_account(base_url, tok, user_id_value, body, accept, timeout, content_type=contentType)
            return {"id": user_id_value, "result": result}
        except _req.HTTPError as e:
            return handle_http_error(e, "update")
import os
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

try:
    from src.auth import login_and_get_token
    from src.pilldoc.api import get_accounts, get_user, get_pharm, update_account, get_rejected_campaigns, post_rejected_campaign
except ModuleNotFoundError:
    import sys as _sys, os as _os
    _sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from src.auth import login_and_get_token
    from src.pilldoc.api import get_accounts, get_user, get_pharm, update_account, get_rejected_campaigns, post_rejected_campaign


def _need_base_url(baseUrl: Optional[str]) -> str:
    base_url = (baseUrl or os.getenv("EDB_BASE_URL") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("EDB_BASE_URL 이 필요합니다. .env(.local) 설정 또는 baseUrl 인자 사용")
    return base_url


def _ensure_token(token: Optional[str], userId: Optional[str], password: Optional[str], loginUrl: Optional[str], timeout: int) -> str:
    if token is None:
        # 환경변수/자동로그인 캐시 우선 사용
        env_tok = os.getenv("EDB_TOKEN")
        if env_tok:
            return env_tok
    else:
        return token
    uid = userId or os.getenv("EDB_USER_ID")
    pwd = password or os.getenv("EDB_PASSWORD")
    _login_url = loginUrl or os.getenv("EDB_LOGIN_URL")
    if not uid or not pwd:
        raise RuntimeError("token 또는 userId/password 가 필요합니다.")
    return login_and_get_token(_login_url, uid, pwd, False, int(timeout))


def _items_of(obj: Any) -> list:
    if isinstance(obj, dict):
        if isinstance(obj.get("items"), list):
            return obj["items"]
        if isinstance(obj.get("data"), list):
            return obj["data"]
    return []


def register_pilldoc_tools(mcp: FastMCP) -> None:
    def _normalize_bizno(val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        try:
            s = str(val)
        except Exception:
            return None
        digits = "".join(ch for ch in s if ch.isdigit())
        return digits or s
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
        adBlocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
    ) -> Dict[str, Any]:
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)

        filters: Dict[str, Any] = {}
        if page_no is not None and page is None:
            page = page_no
        if page_count is not None and pageSize is None:
            pageSize = page_count
        if pageSize is not None:
            filters["pageSize"] = int(pageSize)
        if page is not None:
            filters["page"] = int(page)
        if sortBy is not None:
            filters["sortBy"] = str(sortBy)
        if erpKind is not None:
            filters["erpKind"] = list(erpKind)
        if isAdDisplay is not None:
            filters["isAdDisplay"] = int(isAdDisplay)
        elif adBlocked is not None:
            # Alias: adBlocked=True => isAdDisplay=0 (차단), adBlocked=False => isAdDisplay=1 (미차단)
            filters["isAdDisplay"] = 0 if bool(adBlocked) else 1
        if salesChannel is not None:
            filters["salesChannel"] = list(salesChannel)
        if pharmChain is not None:
            filters["pharmChain"] = list(pharmChain)
        if currentSearchType is not None:
            filters["currentSearchType"] = list(currentSearchType)
        if searchKeyword is not None:
            filters["searchKeyword"] = str(searchKeyword)
        if accountType is not None:
            filters["accountType"] = str(accountType)

        try:
            return get_accounts(base_url, tok, accept, timeout, filters=filters)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

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
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)
        try:
            return get_user(base_url, tok, id, accept, timeout)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

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
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)
        try:
            return get_pharm(base_url, tok, bizno, accept, timeout)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

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
    ) -> Dict[str, Any]:
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)

        filters: Dict[str, Any] = {}
        if page_no is not None and page is None:
            page = page_no
        if page_count is not None and pageSize is None:
            pageSize = page_count
        if pageSize is not None:
            filters["pageSize"] = int(pageSize)
        if page is not None:
            filters["page"] = int(page)
        if sortBy is not None:
            filters["sortBy"] = str(sortBy)
        if erpKind is not None:
            filters["erpKind"] = list(erpKind)
        if isAdDisplay is not None:
            filters["isAdDisplay"] = int(isAdDisplay)
        elif adBlocked is not None:
            # Alias: adBlocked=True => isAdDisplay=0 (차단), adBlocked=False => isAdDisplay=1 (미차단)
            filters["isAdDisplay"] = 0 if bool(adBlocked) else 1
        if salesChannel is not None:
            filters["salesChannel"] = list(salesChannel)
        if pharmChain is not None:
            filters["pharmChain"] = list(pharmChain)
        if currentSearchType is not None:
            filters["currentSearchType"] = list(currentSearchType)
        if searchKeyword is not None:
            filters["searchKeyword"] = str(searchKeyword)
        if accountType is not None:
            filters["accountType"] = str(accountType)

        try:
            accounts_resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"step": "accounts", "error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

        def _extract_list(obj: Any) -> list:
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                for key in ("data", "items", "results", "list"):
                    if key in obj and isinstance(obj[key], list):
                        return obj[key]
            return []

        items = _extract_list(accounts_resp)
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
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"step": "user", "userId": user_id_value, "error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

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
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)

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
                try:
                    body = e.response.json()
                except Exception:
                    body = e.response.text if e.response is not None else None
                return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body, "page": page}

            if last_page is None:
                try:
                    total_page = int(resp.get("totalPage")) if isinstance(resp, dict) and resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = _items_of(resp)
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
                    biz_no_val = _normalize_bizno(str(it.get("bizNO") or "").strip())
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
        import requests as _req

        if not (pharmName or ownerName or bizNo):
            raise RuntimeError("pharmName, ownerName, bizNo 중 하나는 지정해야 합니다.")

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)

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
        bizNo = _normalize_bizno(bizNo)
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
                try:
                    body = e.response.json()
                except Exception:
                    body = e.response.text if e.response is not None else None
                return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body, "page": page}

            if last_page is None:
                try:
                    total_page = int(resp.get("totalPage")) if isinstance(resp, dict) and resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = _items_of(resp)
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
                    biz_no_val = _normalize_bizno(str(it.get("bizNO") or "").strip())
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
                    try:
                        body = e.response.json()
                    except Exception:
                        body = e.response.text if e.response is not None else None
                    user_detail = {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

            if biz_no_val:
                try:
                    pharm_detail = get_pharm(base_url, tok, biz_no_val, accept, timeout)
                except _req.HTTPError as e:
                    try:
                        body = e.response.json()
                    except Exception:
                        body = e.response.text if e.response is not None else None
                    pharm_detail = {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

                # adps reject campaigns
                try:
                    adps_rejects = get_rejected_campaigns(base_url, tok, biz_no_val, accept, timeout)
                except _req.HTTPError as e:
                    try:
                        body = e.response.json()
                    except Exception:
                        body = e.response.text if e.response is not None else None
                    adps_rejects = {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

            enriched.append({"account": account, "user": user_detail, "pharm": pharm_detail, "adpsRejects": adps_rejects})

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
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)
        bizNo = _normalize_bizno(bizNo)
        try:
            return get_rejected_campaigns(base_url, tok, bizNo, accept, timeout)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

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
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)
        bizNo = _normalize_bizno(bizNo)
        try:
            return post_rejected_campaign(base_url, tok, bizNo, int(campaignId), str(comment), accept, timeout)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}

        return {"matches": enriched, "searchedPages": searched_pages, "totalChecked": checked}


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
        import requests as _req

        if not (pharmName or bizNo):
            raise RuntimeError("pharmName 또는 bizNo 중 하나는 반드시 지정해야 합니다.")

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)

        # 1) /v1/pilldoc/accounts 페이지네이션 조회
        page = 1
        last_page: Optional[int] = None
        candidates: list = []

        # 기본 검색 타입 보정: bizNo가 주어지면 ['b'], pharmName이면 ['s']
        default_search = ["b"] if bizNo else (["s"] if pharmName else None)

        bizNo = _normalize_bizno(bizNo)
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
                try:
                    err_body = e.response.json()
                except Exception:
                    err_body = e.response.text if e.response is not None else None
                return {"step": "accounts", "error": str(e), "status": getattr(e.response, "status_code", None), "body": err_body, "page": page}

            if last_page is None:
                try:
                    total_page = int(resp.get("totalPage")) if isinstance(resp, dict) and resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = _items_of(resp)
            if not items:
                break

            def _matches(it: Dict[str, Any]) -> bool:
                name_val = str(it.get("약국명") or "").strip()
                biz_val = _normalize_bizno(str(it.get("bizNO") or it.get("bizNo") or "").strip())
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
            try:
                err_body = e.response.json()
            except Exception:
                err_body = e.response.text if e.response is not None else None
            return {"step": "update", "userId": user_id_value, "error": str(e), "status": getattr(e.response, "status_code", None), "body": err_body}

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
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)
        try:
            return update_account(base_url, tok, id, body, accept, timeout, content_type=contentType)
        except _req.HTTPError as e:
            try:
                body = e.response.json()
            except Exception:
                body = e.response.text if e.response is not None else None
            return {"error": str(e), "status": getattr(e.response, "status_code", None), "body": body}


    @mcp.tool()
    def pilldoc_accounts_stats(
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        pageSize: int = 200,
        maxPages: int = 0,
        sortBy: Optional[str] = None,
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        adBlocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
    ) -> Dict[str, Any]:
        """pilldoc 계정 목록을 페이지네이션으로 수집해 통계(월별/지역별/ERP/광고차단)를 집계합니다."""
        import requests as _req

        base_url = _need_base_url(baseUrl)
        tok = _ensure_token(token, userId, password, loginUrl, timeout)

        def _region_of(item: Dict[str, Any]) -> Optional[str]:
            for key in ("검색용주소", "주소"):
                val = str(item.get(key) or "").strip()
                if val and val != "None":
                    try:
                        return val.split()[0]
                    except Exception:
                        return None
            return None

        def _month_of(created_at: Optional[str]) -> Optional[str]:
            if not created_at:
                return None
            s = str(created_at)
            # ISO-like: YYYY-MM-... → first 7 chars
            return s[:7] if len(s) >= 7 else None

        def _ad_blocked_of(item: Dict[str, Any]) -> Optional[bool]:
            label = str(item.get("광고차단") or "").strip()
            if label == "":
                return None
            if label in ("표시", "차단", "Y", "YES", "Yes"):
                return True
            if label in ("미표시", "N", "NO", "No"):
                return False
            return None

        total_reported: Optional[int] = None
        pages_fetched = 0
        first_created: Optional[str] = None
        last_created: Optional[str] = None

        monthly: Dict[str, int] = {}
        region: Dict[str, int] = {}
        erp: Dict[str, int] = {}
        adstats = {"blocked": 0, "notBlocked": 0, "unknown": 0}

        page = 1
        last_page: Optional[int] = None

        while True:
            filters: Dict[str, Any] = {"page": page, "pageSize": int(pageSize)}
            if sortBy is not None:
                filters["sortBy"] = str(sortBy)
            if erpKind is not None:
                filters["erpKind"] = list(erpKind)
            if isAdDisplay is not None:
                filters["isAdDisplay"] = int(isAdDisplay)
            elif adBlocked is not None:
                filters["isAdDisplay"] = 0 if bool(adBlocked) else 1
            if salesChannel is not None:
                filters["salesChannel"] = list(salesChannel)
            if pharmChain is not None:
                filters["pharmChain"] = list(pharmChain)
            if currentSearchType is not None:
                filters["currentSearchType"] = list(currentSearchType)
            if searchKeyword is not None:
                filters["searchKeyword"] = str(searchKeyword)
            if accountType is not None:
                filters["accountType"] = str(accountType)

            try:
                resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
            except _req.HTTPError as e:
                try:
                    body = e.response.json()
                except Exception:
                    body = e.response.text if e.response is not None else None
                return {"step": "accounts", "error": str(e), "status": getattr(e.response, "status_code", None), "body": body, "page": page}

            if total_reported is None and isinstance(resp, dict):
                try:
                    total_reported = int(resp.get("totalCount")) if resp.get("totalCount") is not None else None
                except Exception:
                    total_reported = None

            if last_page is None and isinstance(resp, dict):
                try:
                    total_page = int(resp.get("totalPage")) if resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = _items_of(resp)
            if not items:
                break
            pages_fetched += 1

            for it in items:
                if not isinstance(it, dict):
                    continue

                # createdAt range
                created_at = str(it.get("createdAt") or "").strip()
                if created_at:
                    if first_created is None or created_at < first_created:
                        first_created = created_at
                    if last_created is None or created_at > last_created:
                        last_created = created_at

                # monthly
                mkey = _month_of(created_at)
                if mkey:
                    monthly[mkey] = monthly.get(mkey, 0) + 1

                # region
                rkey = _region_of(it)
                if rkey:
                    region[rkey] = region.get(rkey, 0) + 1

                # erp
                ecode = it.get("erpCode")
                ekey = "null" if ecode is None else str(ecode)
                erp[ekey] = erp.get(ekey, 0) + 1

                # ad block
                ab = _ad_blocked_of(it)
                if ab is True:
                    adstats["blocked"] += 1
                elif ab is False:
                    adstats["notBlocked"] += 1
                else:
                    adstats["unknown"] += 1

            if last_page is not None and page >= last_page:
                break
            page += 1

        def _sorted_dict_counts(d: Dict[str, int], by_numeric_key: bool = False) -> Any:
            try:
                if by_numeric_key:
                    items_sorted = sorted(((k, v) for k, v in d.items()), key=lambda kv: (int(kv[0]) if kv[0].lstrip("-+").isdigit() else 10**9, kv[0]))
                else:
                    items_sorted = sorted(d.items(), key=lambda kv: kv[0])
            except Exception:
                items_sorted = sorted(d.items(), key=lambda kv: kv[0])
            return [{"key": k, "count": v} for k, v in items_sorted]

        monthly_sorted = [{"month": k, "count": v} for k, v in sorted(monthly.items(), key=lambda kv: kv[0])]
        region_sorted = _sorted_dict_counts(region)
        erp_sorted = _sorted_dict_counts(erp, by_numeric_key=True)

        return {
            "filters": {
                "pageSize": pageSize,
                "maxPages": maxPages,
                "sortBy": sortBy,
                "erpKind": erpKind,
                "isAdDisplay": isAdDisplay if isAdDisplay is not None else (0 if adBlocked else (1 if adBlocked is False else None)),
                "salesChannel": salesChannel,
                "pharmChain": pharmChain,
                "currentSearchType": currentSearchType,
                "searchKeyword": searchKeyword,
                "accountType": accountType,
            },
            "totalCountReported": total_reported,
            "pagesFetched": pages_fetched,
            "period": {"from": first_created, "to": last_created},
            "stats": {
                "monthly": monthly_sorted,
                "region": region_sorted,
                "erpCode": erp_sorted,
                "adBlocked": adstats,
            },
        }


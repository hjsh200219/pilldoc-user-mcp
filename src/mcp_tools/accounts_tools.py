"""계정 관련 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_accounts, get_user, update_account
from .helpers import (
    need_base_url, ensure_token, items_of, normalize_bizno,
    is_ad_display_from_item, client_sort_items, handle_http_error,
    normalize_filter_params
)
from .filter_builder import FilterBuilder


def _sanitize_update_body(body: Dict[str, Any]) -> Dict[str, Any]:
    """계정 업데이트 body 필드를 정제하고 검증하는 공통 함수

    - 일반적인 실수 패턴을 올바른 필드로 자동 변환
    - 값 형식 검증 및 변환
    - 허용되지 않은 필드 제거
    """
    # 일반적인 실수 패턴 자동 수정
    field_mappings = {
        # 약국장 관련
        "ownerName": "displayName",
        "owner": "displayName",
        "약국장": "displayName",
        "대표자": "displayName",
        "대표": "displayName",
        "약국장이름": "displayName",
        "대표자이름": "displayName",
        # 광고 관련
        "isAdDisplay": None,  # 특별 처리
        "adDisplay": None,  # 특별 처리
        "광고표시": "약국광고표기",
        "광고": "약국광고표기",
        "ad": "약국광고표기",
        # QR 관련
        "QR표기": "필첵QR표기",
        "qr": "필첵QR표기",
        "pillcheckQR": "필첵QR표기",
        # 전화번호 관련
        "전화번호": "약국전화번호",
        "phone": "약국전화번호",
        "tel": "약국전화번호",
        "mobile": "휴대전화번호",
        "휴대폰": "휴대전화번호",
        "핸드폰": "휴대전화번호",
        "cellphone": "휴대전화번호",
        # 주소 관련
        "address": "pharAddress",
        "주소": "pharAddress",
        "약국주소": "pharAddress",
        "상세주소": "pharAddressDetail",
        "addressDetail": "pharAddressDetail",
        # 위치 관련
        "lat": "latitude",
        "lng": "longitude",
        "lon": "longitude",
        "위도": "latitude",
        "경도": "longitude",
        # 기타
        "이메일": "email",
        "mail": "email",
        "타입": "userType",
        "type": "userType",
        "disabled": "isDisable",
        "disable": "isDisable",
        "locked": "lockoutEnabled",
        "lockout": "lockoutEnabled",
        "unlock": "unLockAccount",
        "승인": "관리자승인여부",
        "승인여부": "관리자승인여부",
        "요양번호": "요양기관번호",
        "기관번호": "요양기관번호",
        "체인": "pharmChain",
        "chain": "pharmChain",
        "erp": "erpCode",
        "영업채널": "영업채널Code",
        "salesChannel": "영업채널Code",
        "salesManager": "salesManagerId",
        "담당자": "salesManagerId",
    }

    # 필드명 자동 변환
    converted_body = {}
    for key, value in body.items():
        # 매핑 테이블 확인
        if key in field_mappings:
            mapped_key = field_mappings[key]
            if mapped_key:  # None이 아닌 경우 단순 매핑
                converted_body[mapped_key] = value
                print(f"INFO: '{key}' → '{mapped_key}'로 자동 변환")
            # isAdDisplay 등 특별 처리가 필요한 경우는 아래에서 처리
        else:
            converted_body[key] = value

    body = converted_body

    # 허용된 필드 목록 (API 스펙 기준)
    allowed_fields = {
        "userType", "displayName", "email", "memberShipType", "isDisable",
        "lockoutEnabled", "unLockAccount", "약국명", "accountType", "관리자승인여부",
        "요양기관번호", "약국전화번호", "휴대전화번호", "pharAddress", "pharAddressDetail",
        "latitude", "longitude", "bcode", "pharmChain", "erpCode", "영업채널Code",
        "salesManagerId", "필첵QR표기", "약국광고표기"
    }

    # isAdDisplay, adDisplay 특별 처리
    if "isAdDisplay" in body or "adDisplay" in body:
        is_ad_display = body.pop("isAdDisplay", body.pop("adDisplay", None))
        if is_ad_display == 0 or str(is_ad_display).lower() in ["false", "no", "표시"]:
            body["약국광고표기"] = "표시"
            print(f"INFO: isAdDisplay: {is_ad_display} → 약국광고표기: '표시'로 변환")
        elif is_ad_display == 1 or str(is_ad_display).lower() in ["true", "yes", "미표시"]:
            body["약국광고표기"] = "미표시"
            print(f"INFO: isAdDisplay: {is_ad_display} → 약국광고표기: '미표시'로 변환")

    # 값 형식 검증 및 변환
    if "약국광고표기" in body:
        value = str(body["약국광고표기"]).lower()
        if value in ["true", "1", "yes", "on", "표시", "show", "display"]:
            body["약국광고표기"] = "표시"
        elif value in ["false", "0", "no", "off", "미표시", "hide", "hidden"]:
            body["약국광고표기"] = "미표시"
        elif value not in ["표시", "미표시"]:
            print(f"WARNING: 약국광고표기 값 '{body['약국광고표기']}'가 올바르지 않습니다. '표시' 또는 '미표시'만 허용됩니다.")
            body.pop("약국광고표기")

    if "필첵QR표기" in body:
        value = str(body["필첵QR표기"]).lower()
        if value in ["true", "1", "yes", "on", "표시", "show", "display"]:
            body["필첵QR표기"] = "표시"
        elif value in ["false", "0", "no", "off", "미표시", "hide", "hidden"]:
            body["필첵QR표기"] = "미표시"
        elif value not in ["표시", "미표시"]:
            print(f"WARNING: 필첵QR표기 값 '{body['필첵QR표기']}'가 올바르지 않습니다. '표시' 또는 '미표시'만 허용됩니다.")
            body.pop("필첵QR표기")

    # accountType 검증
    if "accountType" in body:
        valid_types = ["일반", "테스터"]
        if body["accountType"] not in valid_types:
            print(f"WARNING: accountType '{body['accountType']}'는 유효하지 않습니다. 허용값: {valid_types}")
            body.pop("accountType")

    # memberShipType 검증
    if "memberShipType" in body:
        valid_types = ["basic", "premium"]
        if body["memberShipType"] not in valid_types:
            print(f"WARNING: memberShipType '{body['memberShipType']}'는 유효하지 않습니다. 허용값: {valid_types}")
            body.pop("memberShipType")

    # 불린 필드 검증
    boolean_fields = ["isDisable", "lockoutEnabled", "unLockAccount", "관리자승인여부"]
    for field in boolean_fields:
        if field in body and not isinstance(body[field], bool):
            # 문자열을 불린으로 변환
            value = str(body[field]).lower()
            body[field] = value in ["true", "1", "yes", "예", "y", "on", "활성", "사용"]

    # 숫자 필드 검증
    numeric_fields = ["latitude", "longitude", "erpCode", "영업채널Code", "salesManagerId"]
    for field in numeric_fields:
        if field in body:
            try:
                if field in ["latitude", "longitude"]:
                    body[field] = float(body[field])
                else:
                    body[field] = int(body[field])
            except (ValueError, TypeError):
                print(f"WARNING: {field} 값이 숫자가 아닙니다: {body[field]}")
                body.pop(field)

    # 전화번호 형식 검증 및 정규화
    phone_fields = ["약국전화번호", "휴대전화번호"]
    for field in phone_fields:
        if field in body:
            # 숫자만 추출
            phone = ''.join(filter(str.isdigit, str(body[field])))
            if field == "휴대전화번호" and not phone.startswith("01"):
                print(f"WARNING: 휴대전화번호는 01로 시작해야 합니다: {body[field]}")
                body.pop(field)
            elif len(phone) < 9:
                print(f"WARNING: {field}가 너무 짧습니다: {body[field]}")
                body.pop(field)
            else:
                # 하이픈 추가 (선택적)
                if field == "휴대전화번호" and len(phone) == 11:
                    body[field] = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                elif len(phone) == 10:
                    body[field] = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"

    # 이메일 형식 간단 검증
    if "email" in body:
        email = str(body["email"])
        if "@" not in email or "." not in email.split("@")[-1]:
            print(f"WARNING: 이메일 형식이 올바르지 않습니다: {email}")
            body.pop("email")

    # 허용되지 않은 필드 제거
    invalid_fields = [k for k in body.keys() if k not in allowed_fields]
    if invalid_fields:
        print(f"WARNING: 허용되지 않은 필드가 제거됩니다: {invalid_fields}")
        for field in invalid_fields:
            body.pop(field)

    return body


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
        # 다양한 파라미터 이름 지원
        pageSize: Optional[int] = None,
        page_size: Optional[int] = None,
        size: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        page_no: Optional[int] = None,
        pageNo: Optional[int] = None,
        page_count: Optional[int] = None,
        sortBy: Optional[str] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        erpKind: Optional[list] = None,
        erp: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        adBlocked: Optional[bool] = None,
        ad_blocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        sales_channel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        pharm_chain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        search_type: Optional[list] = None,
        searchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        search: Optional[str] = None,
        keyword: Optional[str] = None,
        query: Optional[str] = None,
        accountType: Optional[str] = None,
        account_type: Optional[str] = None,
        enforceSortLocal: bool = False,
        **kwargs  # 추가 파라미터를 위한 kwargs
    ) -> Dict[str, Any]:
        """계정 목록 조회

        다양한 파라미터 이름을 지원합니다:
        - 페이지: page, page_no, pageNo 등
        - 크기: pageSize, page_size, size, limit 등
        - 정렬: sortBy, sort, order 등
        - 광고: isAdDisplay, adBlocked, ad_blocked 등
        - 검색: searchKeyword, search, keyword, query 등
        """
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # 모든 파라미터를 하나의 딕셔너리로 수집
        all_params = {}

        # 명시적 파라미터들
        if pageSize is not None: all_params["pageSize"] = pageSize
        if page_size is not None: all_params["page_size"] = page_size
        if size is not None: all_params["size"] = size
        if limit is not None: all_params["limit"] = limit
        if page is not None: all_params["page"] = page
        if page_no is not None: all_params["page_no"] = page_no
        if pageNo is not None: all_params["pageNo"] = pageNo
        if page_count is not None: all_params["page_count"] = page_count
        if sortBy is not None: all_params["sortBy"] = sortBy
        if sort is not None: all_params["sort"] = sort
        if order is not None: all_params["order"] = order
        if erpKind is not None: all_params["erpKind"] = erpKind
        if erp is not None: all_params["erp"] = erp
        if isAdDisplay is not None: all_params["isAdDisplay"] = isAdDisplay
        if adBlocked is not None: all_params["adBlocked"] = adBlocked
        if ad_blocked is not None: all_params["ad_blocked"] = ad_blocked
        if salesChannel is not None: all_params["salesChannel"] = salesChannel
        if sales_channel is not None: all_params["sales_channel"] = sales_channel
        if pharmChain is not None: all_params["pharmChain"] = pharmChain
        if currentSearchType is not None: all_params["currentSearchType"] = currentSearchType
        if search_type is not None: all_params["search_type"] = search_type
        if searchType is not None: all_params["searchType"] = searchType
        if searchKeyword is not None: all_params["searchKeyword"] = searchKeyword
        if search is not None: all_params["search"] = search
        if keyword is not None: all_params["keyword"] = keyword
        if query is not None: all_params["query"] = query
        if accountType is not None: all_params["accountType"] = accountType
        if account_type is not None: all_params["account_type"] = account_type

        # kwargs에서 추가 파라미터 수집
        all_params.update(kwargs)

        # 파라미터 정규화
        normalized = normalize_filter_params(all_params)

        # FilterBuilder에 맞게 다시 매핑
        filters = FilterBuilder.build_account_filters(
            pageSize=normalized.get("pageSize"),
            page=normalized.get("page"),
            page_no=None,  # normalize_filter_params가 page로 통합
            page_count=None,  # 제거
            sortBy=normalized.get("sortBy"),
            erpKind=normalized.get("erpKind"),
            isAdDisplay=normalized.get("isAdDisplay"),
            salesChannel=normalized.get("salesChannel"),
            pharmChain=normalized.get("pharmChain"),
            currentSearchType=normalized.get("currentSearchType"),
            searchKeyword=normalized.get("searchKeyword"),
            accountType=normalized.get("accountType")
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
        """계정 목록을 간결한 형태로 반환합니다. 선택한 필드만 노출하고 isAdDisplay 숫자를 포함할 수 있습니다.

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
        # 다양한 파라미터 이름 지원
        pageSize: Optional[int] = None,
        page_size: Optional[int] = None,
        size: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        page_no: Optional[int] = None,
        pageNo: Optional[int] = None,
        sortBy: Optional[str] = None,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        erpKind: Optional[list] = None,
        erp: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        adBlocked: Optional[bool] = None,
        ad_blocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        search_type: Optional[list] = None,
        searchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        search: Optional[str] = None,
        keyword: Optional[str] = None,
        query: Optional[str] = None,
        accountType: Optional[str] = None,
        account_type: Optional[str] = None,
        enforceSortLocal: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """계정 목록에서 사용자 정보 추출"""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # 모든 파라미터를 하나의 딕셔너리로 수집
        all_params = {}
        if pageSize is not None: all_params["pageSize"] = pageSize
        if page_size is not None: all_params["page_size"] = page_size
        if size is not None: all_params["size"] = size
        if limit is not None: all_params["limit"] = limit
        if page is not None: all_params["page"] = page
        if page_no is not None: all_params["page_no"] = page_no
        if pageNo is not None: all_params["pageNo"] = pageNo
        if sortBy is not None: all_params["sortBy"] = sortBy
        if sort is not None: all_params["sort"] = sort
        if order is not None: all_params["order"] = order
        if erpKind is not None: all_params["erpKind"] = erpKind
        if erp is not None: all_params["erp"] = erp
        if isAdDisplay is not None: all_params["isAdDisplay"] = isAdDisplay
        if adBlocked is not None: all_params["adBlocked"] = adBlocked
        if ad_blocked is not None: all_params["ad_blocked"] = ad_blocked
        if salesChannel is not None: all_params["salesChannel"] = salesChannel
        if pharmChain is not None: all_params["pharmChain"] = pharmChain
        if currentSearchType is not None: all_params["currentSearchType"] = currentSearchType
        if search_type is not None: all_params["search_type"] = search_type
        if searchType is not None: all_params["searchType"] = searchType
        if searchKeyword is not None: all_params["searchKeyword"] = searchKeyword
        if search is not None: all_params["search"] = search
        if keyword is not None: all_params["keyword"] = keyword
        if query is not None: all_params["query"] = query
        if accountType is not None: all_params["accountType"] = accountType
        if account_type is not None: all_params["account_type"] = account_type
        all_params.update(kwargs)

        # 파라미터 정규화
        normalized = normalize_filter_params(all_params)

        filters = FilterBuilder.build_account_filters(
            pageSize=normalized.get("pageSize"),
            page=normalized.get("page"),
            sortBy=normalized.get("sortBy"),
            erpKind=normalized.get("erpKind"),
            isAdDisplay=normalized.get("isAdDisplay"),
            adBlocked=normalized.get("adBlocked"),
            salesChannel=normalized.get("salesChannel"),
            pharmChain=normalized.get("pharmChain"),
            currentSearchType=normalized.get("currentSearchType"),
            searchKeyword=normalized.get("searchKeyword"),
            accountType=normalized.get("accountType")
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
        """계정 정보 업데이트

        중요 필드 구분:
        - displayName: 약국장/대표자 이름 (❌ 약국명이 아님!)
        - 약국명: 약국의 상호명
        - 약국광고표기: "표시" 또는 "미표시"

        자동 변환:
        - isAdDisplay: 0 → 약국광고표기: "표시"
        - isAdDisplay: 1 → 약국광고표기: "미표시"

        허용된 필드:
        - userType, displayName(약국장), email, memberShipType, isDisable,
        - lockoutEnabled, unLockAccount, 약국명(상호), accountType, 관리자승인여부,
        - 요양기관번호, 약국전화번호, 휴대전화번호, pharAddress, pharAddressDetail,
        - latitude, longitude, bcode, pharmChain, erpCode, 영업채널Code,
        - salesManagerId, 필첵QR표기, 약국광고표기
        """
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # body 필드 정제 (공통 함수 사용)
        body = _sanitize_update_body(body)

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
        """약국명 또는 사업자등록번호로 계정을 찾아 id를 얻은 뒤 PATCH 수행.

        주의: isAdDisplay 필드는 자동으로 약국광고표기로 변환됩니다.
        """
        if not (pharmName or bizNo):
            raise RuntimeError("pharmName 또는 bizNo 중 하나는 반드시 지정해야 합니다.")

        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        # body 필드 정제 함수 (pilldoc_update_account와 동일한 로직)
        body = _sanitize_update_body(body)

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
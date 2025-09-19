"""공통 유틸리티 함수들"""
import os
from typing import Any, Dict, Optional
from datetime import datetime

from src.auth import login_and_get_token


def need_base_url(baseUrl: Optional[str]) -> str:
    """Base URL 확인 및 반환"""
    base_url = (baseUrl or os.getenv("EDB_BASE_URL") or "").rstrip("/")
    if not base_url:
        raise RuntimeError("EDB_BASE_URL 이 필요합니다. .env(.local) 설정 또는 baseUrl 인자 사용")
    return base_url


def ensure_token(token: Optional[str], userId: Optional[str], password: Optional[str], loginUrl: Optional[str], timeout: int) -> str:
    """토큰 확인 및 자동 획득"""
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


def items_of(obj: Any) -> list:
    """응답 객체에서 아이템 리스트 추출"""
    if isinstance(obj, dict):
        if isinstance(obj.get("items"), list):
            return obj["items"]
        if isinstance(obj.get("data"), list):
            return obj["data"]
    return []


def normalize_filter_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """필터 파라미터 정규화 - 일반적인 실수 패턴을 API 스펙에 맞게 변환

    계정 조회 필터링 파라미터 매핑:
    - 페이지네이션, 정렬, 필터링 파라미터 정규화
    - 잘못된 이름을 올바른 파라미터로 매핑
    """
    # 파라미터 이름 매핑
    param_mappings = {
        # 페이지네이션 관련
        "page_size": "pageSize",
        "pagesize": "pageSize",
        "size": "pageSize",
        "limit": "pageSize",
        "per_page": "pageSize",
        "page_no": "page",
        "pageNo": "page",
        "page_num": "page",
        "pageNum": "page",
        "offset": "page",  # offset을 page로 변환 (주의 필요)

        # 정렬 관련
        "sort": "sortBy",
        "order": "sortBy",
        "orderBy": "sortBy",
        "sort_by": "sortBy",

        # ERP 관련
        "erp": "erpKind",
        "erpType": "erpKind",
        "erp_kind": "erpKind",
        "erp_type": "erpKind",

        # 광고 관련
        "ad_display": "isAdDisplay",
        "adDisplay": "isAdDisplay",
        "광고표시": "isAdDisplay",
        "광고": "isAdDisplay",
        "ad_blocked": "adBlocked",
        "광고차단": "adBlocked",

        # 판매채널
        "sales_channel": "salesChannel",
        "channel": "salesChannel",
        "영업채널": "salesChannel",

        # 약국체인
        "pharm_chain": "pharmChain",
        "chain": "pharmChain",
        "체인": "pharmChain",
        "pharmacy_chain": "pharmChain",

        # 검색 관련
        "search": "searchKeyword",
        "keyword": "searchKeyword",
        "query": "searchKeyword",
        "q": "searchKeyword",
        "search_keyword": "searchKeyword",
        "검색": "searchKeyword",
        "검색어": "searchKeyword",

        # 검색 타입
        "search_type": "currentSearchType",
        "searchType": "currentSearchType",
        "검색타입": "currentSearchType",
        "검색유형": "currentSearchType",

        # 계정 타입
        "account_type": "accountType",
        "type": "accountType",
        "계정타입": "accountType",
        "계정유형": "accountType",
    }

    # 파라미터 이름 변환
    normalized = {}
    for key, value in params.items():
        # 매핑 테이블에서 찾기
        mapped_key = param_mappings.get(key, key)
        normalized[mapped_key] = value

    # 값 정규화

    # pageSize: 숫자로 변환, 기본값 처리
    if "pageSize" in normalized:
        try:
            normalized["pageSize"] = int(normalized["pageSize"])
            # 범위 제한 (1-1000)
            normalized["pageSize"] = max(1, min(1000, normalized["pageSize"]))
        except (ValueError, TypeError):
            normalized["pageSize"] = 100  # 기본값

    # page: 숫자로 변환, 1부터 시작
    if "page" in normalized:
        try:
            normalized["page"] = int(normalized["page"])
            normalized["page"] = max(1, normalized["page"])
        except (ValueError, TypeError):
            normalized["page"] = 1

    # isAdDisplay: 0 또는 1로 변환
    if "isAdDisplay" in normalized:
        val = normalized["isAdDisplay"]
        if isinstance(val, bool):
            normalized["isAdDisplay"] = 0 if val else 1
        elif str(val).lower() in ["true", "yes", "표시", "show"]:
            normalized["isAdDisplay"] = 0  # 0이 표시
        elif str(val).lower() in ["false", "no", "미표시", "차단", "hide"]:
            normalized["isAdDisplay"] = 1  # 1이 미표시/차단
        else:
            try:
                normalized["isAdDisplay"] = int(val)
            except:
                pass

    # adBlocked: boolean으로 변환
    if "adBlocked" in normalized:
        val = normalized["adBlocked"]
        if isinstance(val, str):
            normalized["adBlocked"] = val.lower() in ["true", "1", "yes", "차단"]
        elif isinstance(val, int):
            normalized["adBlocked"] = bool(val)

    # currentSearchType: 배열로 변환
    if "currentSearchType" in normalized:
        val = normalized["currentSearchType"]
        if isinstance(val, str):
            # "s", "b", "sb" 같은 문자열을 배열로 변환
            if val in ["s", "b", "sb", "bs"]:
                normalized["currentSearchType"] = list(val) if len(val) > 1 else [val]
            else:
                normalized["currentSearchType"] = [val]
        elif not isinstance(val, list):
            normalized["currentSearchType"] = [str(val)]

    # erpKind, salesChannel, pharmChain: 배열로 변환
    for field in ["erpKind", "salesChannel", "pharmChain"]:
        if field in normalized:
            val = normalized[field]
            if not isinstance(val, list):
                normalized[field] = [val] if val is not None else []

    # sortBy: 서버 스펙을 존중하여 값은 그대로 전달 (예: "CreatedAt")

    return normalized


def normalize_bizno(val: Optional[str]) -> Optional[str]:
    """사업자 번호 정규화 (하이픈 제거)"""
    if val is None:
        return None
    try:
        s = str(val)
    except Exception:
        return None
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits or s


def is_ad_display_from_item(item: Dict[str, Any]) -> Optional[int]:
    """광고 표시 상태를 숫자로 반환합니다. 0=표시(차단 아님), 1=차단, None=알 수 없음"""
    label_raw = item.get("광고차단")
    label = str(label_raw).strip()
    if label == "":
        return None
    low = label.lower()
    blocked_vals = {"차단", "미표시", "y", "yes", "true", "blocked", "block"}
    display_vals = {"표시", "표시중", "n", "no", "false", "display"}
    if low in blocked_vals:
        return 1
    if low in display_vals:
        return 0
    return None


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """ISO 날짜 문자열 파싱"""
    if not value:
        return None
    try:
        s = str(value).strip()
        # 지원: '...Z' → '+00:00'
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


def parse_sort_spec(sortBy: Optional[str]) -> Optional[Dict[str, Any]]:
    """정렬 스펙 파싱"""
    if not sortBy:
        return None
    try:
        s = str(sortBy).strip()
        field = s
        desc = False
        if ":" in s:
            left, right = s.split(":", 1)
            field = left.strip()
            token = right.strip().lower()
            desc = token in {"desc", "descending", "-1"}
        elif s.startswith("-"):
            field = s[1:].strip()
            desc = True
        else:
            field = s
        return {"field": field, "desc": bool(desc)}
    except Exception:
        return None


def key_for_sort(item: Dict[str, Any], field: str):
    """정렬 키 추출"""
    if field == "createdAt":
        dt = parse_iso_datetime(item.get("createdAt"))
        # 정렬 안정성 보장: 파싱 실패 시 극단값 반환
        return dt or datetime.min
    val = item.get(field)
    # 숫자/문자 자동 캐스팅
    try:
        if val is None:
            return ""
        if isinstance(val, (int, float)):
            return val
        s = str(val)
        if s.lstrip("-+").isdigit():
            return int(s)
        try:
            return float(s)
        except Exception:
            return s
    except Exception:
        return ""


def client_sort_items(items: list, sortBy: Optional[str]) -> list:
    """클라이언트 사이드 정렬"""
    spec = parse_sort_spec(sortBy)
    if not spec:
        return items
    field = spec["field"]
    desc = spec["desc"]
    try:
        return sorted(items, key=lambda it: key_for_sort(it if isinstance(it, dict) else {}, field), reverse=desc)
    except Exception:
        return items


def handle_http_error(e, step: Optional[str] = None) -> Dict[str, Any]:
    """HTTP 에러 처리"""
    try:
        body = e.response.json()
    except Exception:
        body = e.response.text if e.response is not None else None

    result = {
        "error": str(e),
        "status": getattr(e.response, "status_code", None),
        "body": body
    }
    if step:
        result["step"] = step
    return result
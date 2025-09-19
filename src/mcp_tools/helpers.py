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
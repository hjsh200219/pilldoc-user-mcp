"""Pilldoc API 클라이언트 - 리팩토링 버전"""
from typing import Any, Dict, Optional
import requests


class APIClient:
    """API 호출을 위한 베이스 클라이언트"""

    @staticmethod
    def _build_auth_headers(token: str, accept: str = "application/json") -> Dict[str, str]:
        return {"accept": accept, "Authorization": f"Bearer {token}"}

    @staticmethod
    def _parse_response(resp: requests.Response) -> Dict[str, Any]:
        """응답을 파싱하여 JSON 또는 텍스트로 반환"""
        try:
            return resp.json()
        except Exception:
            return {"text": resp.text}

    @staticmethod
    def _build_url(base_url: str, path: str) -> str:
        """URL 빌드"""
        return f"{base_url.rstrip('/')}{path}"


def get_accounts(
    base_url: str,
    token: str,
    accept: str = "application/json",
    timeout: int = 15,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """계정 목록 조회"""
    url = APIClient._build_url(base_url, "/v1/pilldoc/accounts")
    headers = APIClient._build_auth_headers(token, accept)
    headers["Content-Type"] = "application/json"

    resp = requests.post(url, headers=headers, json=(filters or {}), timeout=timeout)
    resp.raise_for_status()
    return APIClient._parse_response(resp)


def get_user(
    base_url: str,
    token: str,
    user_id: str,
    accept: str = "application/json",
    timeout: int = 15
) -> Dict[str, Any]:
    """사용자 정보 조회"""
    url = APIClient._build_url(base_url, f"/v1/pilldoc/user/{user_id}")
    resp = requests.get(url, headers=APIClient._build_auth_headers(token, accept), timeout=timeout)
    resp.raise_for_status()
    return APIClient._parse_response(resp)


def get_pharm(
    base_url: str,
    token: str,
    bizno: str,
    accept: str = "application/json",
    timeout: int = 15
) -> Dict[str, Any]:
    """약국 정보 조회"""
    url = APIClient._build_url(base_url, f"/v1/pilldoc/pharm/{bizno}")
    resp = requests.get(url, headers=APIClient._build_auth_headers(token, accept), timeout=timeout)
    resp.raise_for_status()
    return APIClient._parse_response(resp)


def get_rejected_campaigns(
    base_url: str,
    token: str,
    bizno: str,
    accept: str = "application/json",
    timeout: int = 15
) -> Dict[str, Any]:
    """차단된 캠페인 목록 조회"""
    url = APIClient._build_url(base_url, f"/v1/adps/campain/{bizno}/reject")
    resp = requests.get(url, headers=APIClient._build_auth_headers(token, accept), timeout=timeout)
    resp.raise_for_status()
    return APIClient._parse_response(resp)


def post_rejected_campaign(
    base_url: str,
    token: str,
    bizno: str,
    campaign_id: int,
    comment: str,
    accept: str = "application/json",
    timeout: int = 15,
) -> Dict[str, Any]:
    """캠페인 차단/차단해제"""
    url = APIClient._build_url(base_url, f"/v1/adps/campain/{bizno}/reject")
    headers = APIClient._build_auth_headers(token, accept)
    headers["Content-Type"] = "application/json"
    payload = {"campaignId": int(campaign_id), "comment": str(comment)}

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return APIClient._parse_response(resp)


def update_account(
    base_url: str,
    token: str,
    user_id: str,
    payload: Dict[str, Any],
    accept: str = "application/json",
    timeout: int = 15,
    content_type: str = "application/json",
) -> Dict[str, Any]:
    """계정 정보 업데이트 (다양한 Content-Type 자동 시도)"""
    url = APIClient._build_url(base_url, f"/v1/pilldoc/account/{user_id}")
    headers_base = APIClient._build_auth_headers(token, accept)

    def _do_request(method: str, ct: str) -> requests.Response:
        headers = dict(headers_base)
        # 멀티파트는 requests가 boundary를 포함해 Content-Type을 자동 설정하도록 둡니다.
        if ct == "multipart/form-data":
            files = {k: (None, v if isinstance(v, str) else str(v)) for k, v in (payload or {}).items()}
            return requests.request(method, url, headers=headers, files=files, timeout=timeout)
        if ct == "application/x-www-form-urlencoded":
            headers["Content-Type"] = ct
            return requests.request(method, url, headers=headers, data=payload, timeout=timeout)
        # JSON 계열
        headers["Content-Type"] = ct
        return requests.request(method, url, headers=headers, json=payload, timeout=timeout)

    # Content-Type 자동 재시도 후보
    ct_variants = [content_type]
    if content_type == "application/json":
        ct_variants = [
            "application/json; charset=utf-8",
            "application/json",
            "application/merge-patch+json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]

    # PATCH 메서드만 사용
    methods = ["PATCH"]

    last_err: Optional[Exception] = None
    for method in methods:
        for ct in ct_variants:
            try:
                resp = _do_request(method, ct)
                resp.raise_for_status()
                return APIClient._parse_response(resp)
            except requests.HTTPError as e:
                status = getattr(e.response, "status_code", None)
                # 415이면 다음 조합으로 재시도, 그 외는 즉시 실패
                if status != 415:
                    raise
                last_err = e
                continue

    # 모든 조합 실패
    if last_err:
        raise last_err
    raise RuntimeError("요청을 보낼 수 없습니다. (update_account)")
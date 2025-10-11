"""로그인 및 토큰 관리"""

import json
from typing import Any, Dict, Optional

import requests


def extract_token(data: Any) -> Optional[str]:
    """응답 데이터에서 토큰 추출"""
    if isinstance(data, dict):
        # 토큰 키 검색
        for key in [
            "accessToken",
            "access_token",
            "refreshToken",
            "refresh_token",
            "token",
            "jwt",
            "id_token",
            "idToken",
        ]:
            if key in data and isinstance(data[key], str):
                value = data[key].strip()
                if value:
                    return value

        # 중첩된 객체 검색
        for key in ["data", "result", "payload", "response"]:
            if key in data:
                found = extract_token(data[key])
                if found:
                    return found

    if isinstance(data, list):
        for item in data:
            found = extract_token(item)
            if found:
                return found
    return None


def _is_duplicate_login_error(resp: requests.Response) -> bool:
    """중복 로그인 에러 확인"""
    try:
        data = resp.json()
    except Exception:
        return False
    message = str(data.get("message", ""))
    code = str(data.get("resultCode", ""))
    return ("중복로그인" in message) or (code == "4100")


def login_and_get_token(
    login_url: str,
    user_id: str,
    password: str,
    is_force_login: bool = False,
    timeout: int = 15,
) -> str:
    """로그인하고 토큰 가져오기

    Args:
        login_url: 로그인 API URL
        user_id: 사용자 ID
        password: 비밀번호
        is_force_login: 강제 로그인 여부
        timeout: 타임아웃 (초)

    Returns:
        str: 액세스 토큰

    Raises:
        RuntimeError: 로그인 실패 시
    """
    if not login_url:
        raise RuntimeError("환경변수 EDB_LOGIN_URL 이 설정되지 않았습니다.")

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "userId": user_id,
        "password": password,
        "isForceLogin": bool(is_force_login)
    }

    def _do_login(force_flag: bool) -> requests.Response:
        p = dict(payload)
        p["isForceLogin"] = bool(force_flag)
        return requests.post(login_url, headers=headers, json=p, timeout=timeout)

    resp = _do_login(is_force_login)

    # 중복 로그인 에러 처리
    if not resp.ok:
        if _is_duplicate_login_error(resp) and not is_force_login:
            resp = _do_login(True)

    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError("로그인 응답이 JSON 형식이 아닙니다.")

    token = extract_token(data)
    if not token:
        raise RuntimeError("로그인 응답에서 토큰을 찾지 못했습니다.")

    return token

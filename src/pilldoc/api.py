from typing import Any, Dict, Optional
import os

import requests


def _build_auth_headers(token: str, accept: str = "application/json") -> Dict[str, str]:
    return {"accept": accept, "Authorization": f"Bearer {token}"}


def get_accounts(
    base_url: str,
    token: str,
    accept: str = "application/json",
    timeout: int = 15,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/v1/pilldoc/accounts"
    headers = _build_auth_headers(token, accept)
    headers["Content-Type"] = "application/json"
    resp = requests.post(url, headers=headers, json=(filters or {}), timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text}


def get_user(base_url: str, token: str, user_id: str, accept: str = "application/json", timeout: int = 15) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/v1/pilldoc/user/{user_id}"
    resp = requests.get(url, headers=_build_auth_headers(token, accept), timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text}


def get_pharm(base_url: str, token: str, bizno: str, accept: str = "application/json", timeout: int = 15) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/v1/pilldoc/pharm/{bizno}"
    resp = requests.get(url, headers=_build_auth_headers(token, accept), timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"text": resp.text}



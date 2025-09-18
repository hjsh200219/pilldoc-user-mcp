import os
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

try:
    from src.auth import login_and_get_token
except ModuleNotFoundError:
    import sys as _sys, os as _os
    _sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from src.auth import login_and_get_token


def register_druginfo_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def main_ingredient(
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        Page: int = 1,
        PageSize: int = 20,
        ingredientNameKor: Optional[str] = None,
        IngredientCode: Optional[str] = None,
        drugKind: Optional[str] = None,
        SortBy: Optional[str] = None,
        a4: Optional[str] = None,
        a4Off: Optional[str] = None,
        a5: Optional[str] = None,
        a5Off: Optional[str] = None,
        drugkind: Optional[str] = None,
        drugkindOff: Optional[str] = None,
        effect: Optional[str] = None,
        effectOff: Optional[str] = None,
        showMapped: Optional[str] = None,
    ) -> Dict[str, Any]:
        import requests

        base_url = (baseUrl or os.getenv("EDB_BASE_URL") or "").rstrip("/")
        if not base_url:
            raise RuntimeError("EDB_BASE_URL 이 필요합니다. .env(.local) 설정 또는 baseUrl 인자 사용")
        endpoint = "/v1/druginfo/main-ingredient"

        if token is None:
            # 자동 로그인 캐시 또는 환경변수 토큰 우선 사용
            env_tok = os.getenv("EDB_TOKEN")
            if env_tok:
                token = env_tok
            else:
                uid = userId or os.getenv("EDB_USER_ID")
                pwd = password or os.getenv("EDB_PASSWORD")
                login_url = loginUrl or os.getenv("EDB_LOGIN_URL")
                if not uid or not pwd:
                    raise RuntimeError("token 또는 userId/password 가 필요합니다.")
                token = login_and_get_token(login_url, uid, pwd, bool(force), int(timeout))

        params: Dict[str, Any] = {"Page": int(Page), "PageSize": int(PageSize)}
        if ingredientNameKor:
            params["ingredientNameKor"] = ingredientNameKor
        if IngredientCode:
            params["IngredientCode"] = IngredientCode
        if drugKind:
            params["drugKind"] = drugKind
        if SortBy:
            params["SortBy"] = SortBy
        for k, v in {
            "a4": a4,
            "a4Off": a4Off,
            "a5": a5,
            "a5Off": a5Off,
            "drugkind": drugkind,
            "drugkindOff": drugkindOff,
            "effect": effect,
            "effectOff": effectOff,
            "showMapped": showMapped,
        }.items():
            if v is not None:
                params[k] = v

        headers = {"accept": accept, "Authorization": f"Bearer {token}"}
        url = f"{base_url}{endpoint}"
        resp = requests.get(url, headers=headers, params=params, timeout=int(timeout))
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"text": resp.text}



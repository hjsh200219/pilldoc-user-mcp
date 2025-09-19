import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

try:
    from src.auth import login_and_get_token
except ModuleNotFoundError:
    import sys as _sys, os as _os
    _sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from src.auth import login_and_get_token


_AUTO_TOKEN: Optional[str] = None


def _try_auto_login(timeout: int = 15) -> Optional[str]:
    global _AUTO_TOKEN
    if _AUTO_TOKEN:
        return _AUTO_TOKEN
    uid = os.getenv("EDB_USER_ID")
    pwd = os.getenv("EDB_PASSWORD")
    login_url = os.getenv("EDB_LOGIN_URL")
    if not uid or not pwd or not login_url:
        return None
    try:
        tok = login_and_get_token(login_url, uid, pwd, False, int(timeout))
        _AUTO_TOKEN = tok
        os.environ["EDB_TOKEN"] = tok
        return tok
    except Exception:
        return None


def register_auth_tools(mcp: FastMCP) -> None:
    # 서버 시작 시 1회 자동 로그인 시도 (환경변수가 있는 경우)
    _try_auto_login()
    @mcp.tool()
    def login(
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        timeout: int = 15,
    ) -> str:
        """로그인하여 JWT(또는 refreshToken)를 반환합니다."""
        login_url = loginUrl or os.getenv("EDB_LOGIN_URL")
        uid = userId or os.getenv("EDB_USER_ID")
        pwd = password or os.getenv("EDB_PASSWORD")
        if not uid or not pwd:
            raise RuntimeError("userId/password 가 필요합니다. (또는 EDB_USER_ID/EDB_PASSWORD 설정)")
        token = login_and_get_token(login_url, uid, pwd, bool(force), int(timeout))
        # 최신 토큰을 캐시에 반영해 도구들이 재사용하도록 함
        global _AUTO_TOKEN
        _AUTO_TOKEN = token
        os.environ["EDB_TOKEN"] = token
        return token
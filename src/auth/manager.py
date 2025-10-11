"""인증 관리자"""

import logging
from typing import Optional

from .login import login_and_get_token


logger = logging.getLogger(__name__)


class AuthManager:
    """인증 관리 클래스"""

    def __init__(self, config):
        """초기화

        Args:
            config: 설정 객체
        """
        self.config = config
        self._token: Optional[str] = None

    @property
    def token(self) -> Optional[str]:
        """현재 토큰"""
        return self._token

    async def auto_login(self) -> str:
        """자동 로그인

        환경변수에서 인증 정보를 읽어 자동 로그인을 시도합니다.

        Returns:
            str: 액세스 토큰

        Raises:
            RuntimeError: 로그인 실패 시
        """
        if not self.config.edb_user_id or not self.config.edb_password:
            raise RuntimeError(
                "자동 로그인을 위한 인증 정보가 없습니다. "
                "EDB_USER_ID와 EDB_PASSWORD를 설정하세요."
            )

        login_url = self.config.get_login_url()

        logger.info(f"자동 로그인 시도: {self.config.edb_user_id}")

        token = login_and_get_token(
            login_url=login_url,
            user_id=self.config.edb_user_id,
            password=self.config.edb_password,
            is_force_login=self.config.edb_force_login,
            timeout=self.config.timeout,
        )

        self._token = token
        logger.info("자동 로그인 성공")

        return token

    async def login(
        self,
        user_id: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        login_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> str:
        """수동 로그인

        Args:
            user_id: 사용자 ID (미지정 시 config 사용)
            password: 비밀번호 (미지정 시 config 사용)
            force: 강제 로그인 여부
            login_url: 로그인 URL (미지정 시 config 사용)
            timeout: 타임아웃 (미지정 시 config 사용)

        Returns:
            str: 액세스 토큰

        Raises:
            RuntimeError: 로그인 실패 시
        """
        user_id = user_id or self.config.edb_user_id
        password = password or self.config.edb_password
        login_url = login_url or self.config.get_login_url()
        timeout = timeout or self.config.timeout

        if not user_id or not password:
            raise RuntimeError("사용자 ID와 비밀번호가 필요합니다.")

        logger.info(f"로그인 시도: {user_id}")

        token = login_and_get_token(
            login_url=login_url,
            user_id=user_id,
            password=password,
            is_force_login=force,
            timeout=timeout,
        )

        self._token = token
        logger.info("로그인 성공")

        return token

    def get_token(self) -> Optional[str]:
        """현재 저장된 토큰 가져오기"""
        return self._token

"""설정 관리"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 서버 설정
    server_name: str = Field("pilldoc-user-mcp", description="서버 이름")
    log_level: str = Field("INFO", description="로그 레벨")
    log_file: Optional[str] = Field(None, description="로그 파일 경로")

    # API 설정
    edb_base_url: str = Field(
        "https://dev-adminapi.edbintra.co.kr",
        description="EDB API 기본 URL"
    )
    edb_login_url: Optional[str] = Field(None, description="로그인 URL")
    edb_user_id: Optional[str] = Field(None, description="기본 사용자 ID")
    edb_password: Optional[str] = Field(None, description="기본 비밀번호")
    edb_token: Optional[str] = Field(None, description="기본 토큰")
    edb_force_login: bool = Field(False, description="강제 재로그인")

    # 데이터베이스 설정 (선택적)
    database_url: Optional[str] = Field(None, description="데이터베이스 URL")

    # 성능 설정
    max_connections: int = Field(10, ge=1, description="최대 연결 수")
    timeout: int = Field(15, ge=1, description="기본 타임아웃 (초)")
    max_retries: int = Field(3, ge=0, description="최대 재시도 횟수")

    # 페이지네이션 설정
    default_page_size: int = Field(20, ge=1, le=100, description="기본 페이지 크기")
    max_page_size: int = Field(100, ge=1, description="최대 페이지 크기")

    # 메트릭 설정
    enable_metrics: bool = Field(True, description="메트릭 수집 활성화")
    metrics_export_path: Optional[str] = Field(None, description="메트릭 내보내기 경로")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_login_url(self) -> str:
        """로그인 URL 가져오기"""
        if self.edb_login_url:
            return self.edb_login_url
        return f"{self.edb_base_url.rstrip('/')}/v1/member/sign-in"

    def get_database_config(self) -> Optional[dict]:
        """데이터베이스 설정 파싱"""
        if not self.database_url:
            return None

        # PostgreSQL URL 파싱
        # postgresql://user:password@host:port/database
        import re
        pattern = r'postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<database>.+)'
        match = re.match(pattern, self.database_url)

        if match:
            return match.groupdict()
        return None


# 전역 설정 인스턴스
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """설정 인스턴스 가져오기 (싱글톤)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """설정 다시 로드"""
    global _settings
    _settings = Settings()
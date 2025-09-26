"""로깅 유틸리티"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import time
import json


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """로깅 설정 초기화"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (선택적)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 가져오기"""
    return logging.getLogger(name)


def log_tool_call(tool_name: str):
    """도구 호출 로깅 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()

            # 민감한 정보 마스킹
            safe_kwargs = _mask_sensitive_data(kwargs)

            logger.info(f"Tool call started: {tool_name}", extra={
                "tool": tool_name,
                "arguments": safe_kwargs
            })

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(f"Tool call completed: {tool_name}", extra={
                    "tool": tool_name,
                    "duration": f"{duration:.2f}s",
                    "success": True
                })

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(f"Tool call failed: {tool_name}", extra={
                    "tool": tool_name,
                    "duration": f"{duration:.2f}s",
                    "error": str(e),
                    "success": False
                }, exc_info=True)

                raise

        return wrapper
    return decorator


def _mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """민감한 데이터 마스킹"""
    sensitive_fields = ['password', 'token', 'api_key', 'secret', 'authorization']

    masked_data = {}
    for key, value in data.items():
        if any(field in key.lower() for field in sensitive_fields):
            if isinstance(value, str) and len(value) > 4:
                masked_data[key] = value[:4] + "*" * (len(value) - 4)
            else:
                masked_data[key] = "***"
        else:
            masked_data[key] = value

    return masked_data


class LogContext:
    """로깅 컨텍스트 관리자"""
    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation}", extra=self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type:
            self.logger.error(
                f"Failed {self.operation} after {duration:.2f}s",
                extra={**self.context, "error": str(exc_val)},
                exc_info=True
            )
        else:
            self.logger.info(
                f"Completed {self.operation} in {duration:.2f}s",
                extra={**self.context, "duration": duration}
            )
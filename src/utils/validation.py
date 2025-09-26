"""입력 검증 유틸리티"""
from typing import Any, Dict, Optional, List
from datetime import datetime, date
import re
from .errors import ValidationError


def validate_arguments(args: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """인자 검증 및 변환

    Args:
        args: 검증할 인자 딕셔너리
        schema: 검증 스키마
            - type: 예상 타입
            - required: 필수 여부
            - min/max: 숫자 범위
            - pattern: 정규식 패턴
            - choices: 허용된 값 목록

    Returns:
        검증되고 변환된 인자 딕셔너리
    """
    validated = {}

    for field, rules in schema.items():
        value = args.get(field)

        # 필수 필드 검사
        if rules.get("required", False) and value is None:
            raise ValidationError(f"필수 필드입니다: {field}", field)

        # 값이 없으면 기본값 사용
        if value is None:
            if "default" in rules:
                validated[field] = rules["default"]
            continue

        # 타입 변환 및 검증
        expected_type = rules.get("type")
        if expected_type:
            try:
                if expected_type == "int":
                    value = int(value)
                elif expected_type == "float":
                    value = float(value)
                elif expected_type == "bool":
                    value = _to_bool(value)
                elif expected_type == "date":
                    value = _to_date(value)
                elif expected_type == "list":
                    value = _to_list(value)
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    f"잘못된 타입입니다. {expected_type} 타입이어야 합니다: {field}",
                    field
                )

        # 범위 검사 (숫자)
        if "min" in rules and value < rules["min"]:
            raise ValidationError(
                f"값이 너무 작습니다. 최소값: {rules['min']}: {field}",
                field
            )

        if "max" in rules and value > rules["max"]:
            raise ValidationError(
                f"값이 너무 큽니다. 최대값: {rules['max']}: {field}",
                field
            )

        # 길이 검사 (문자열)
        if isinstance(value, str):
            if "min_length" in rules and len(value) < rules["min_length"]:
                raise ValidationError(
                    f"값이 너무 짧습니다. 최소 길이: {rules['min_length']}: {field}",
                    field
                )

            if "max_length" in rules and len(value) > rules["max_length"]:
                raise ValidationError(
                    f"값이 너무 깁니다. 최대 길이: {rules['max_length']}: {field}",
                    field
                )

        # 패턴 검사
        if "pattern" in rules and isinstance(value, str):
            if not re.match(rules["pattern"], value):
                raise ValidationError(
                    f"올바른 형식이 아닙니다: {field}",
                    field
                )

        # 선택지 검사
        if "choices" in rules:
            choices = rules["choices"]
            if value not in choices:
                raise ValidationError(
                    f"허용된 값이 아닙니다. 선택 가능한 값: {choices}: {field}",
                    field
                )

        validated[field] = value

    return validated


def validate_date_range(
    start_date: Optional[date],
    end_date: Optional[date],
    max_days: int = 365
) -> tuple[Optional[date], Optional[date]]:
    """날짜 범위 검증

    Args:
        start_date: 시작일
        end_date: 종료일
        max_days: 최대 허용 일수

    Returns:
        검증된 (시작일, 종료일) 튜플
    """
    if start_date and end_date:
        if start_date > end_date:
            raise ValidationError("시작일이 종료일보다 늦을 수 없습니다")

        days_diff = (end_date - start_date).days
        if days_diff > max_days:
            raise ValidationError(f"조회 기간은 최대 {max_days}일까지 가능합니다")

    return start_date, end_date


def validate_email(email: str) -> str:
    """이메일 형식 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("올바른 이메일 형식이 아닙니다", "email")
    return email.lower()


def validate_phone(phone: str) -> str:
    """전화번호 형식 검증 및 정규화"""
    # 숫자만 추출
    numbers = re.sub(r'[^0-9]', '', phone)

    # 한국 전화번호 형식 검증
    if len(numbers) < 9 or len(numbers) > 11:
        raise ValidationError("올바른 전화번호 형식이 아닙니다", "phone")

    return numbers


def validate_business_number(biz_no: str) -> str:
    """사업자번호 검증 및 정규화"""
    # 하이픈 제거
    normalized = re.sub(r'[-\s]', '', biz_no)

    # 10자리 숫자 검증
    if not re.match(r'^\d{10}$', normalized):
        raise ValidationError("올바른 사업자번호 형식이 아닙니다 (10자리 숫자)", "biz_no")

    return normalized


def _to_bool(value: Any) -> bool:
    """불리언 변환"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        elif value.lower() in ('false', '0', 'no', 'off'):
            return False
    raise ValueError(f"불리언으로 변환할 수 없습니다: {value}")


def _to_date(value: Any) -> date:
    """날짜 변환"""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(value, "%Y/%m/%d").date()
            except ValueError:
                pass
    raise ValueError(f"날짜로 변환할 수 없습니다: {value}")


def _to_list(value: Any) -> List[Any]:
    """리스트 변환"""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # 콤마로 구분된 문자열
        return [v.strip() for v in value.split(',')]
    return [value]
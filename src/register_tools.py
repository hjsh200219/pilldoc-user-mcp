"""표준 MCP SDK로 도구 등록"""

import logging
from typing import Dict, Any, Optional
from src.tool_registry import ToolRegistry
from src.config import get_settings
from src.utils.errors import ValidationError

logger = logging.getLogger(__name__)


async def register_all_tools(registry: ToolRegistry):
    """모든 도구를 레지스트리에 등록"""

    settings = get_settings()

    # 헬퍼 함수들 임포트
    from src.mcp_tools.helpers import ensure_token, need_base_url

    # 1. 인증 도구 등록
    async def login_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """로그인 도구 핸들러"""
        from src.auth import login_and_get_token

        user_id = args.get("userId") or settings.edb_user_id
        password = args.get("password") or settings.edb_password
        force = args.get("force", False)
        login_url = args.get("loginUrl") or settings.get_login_url()

        if not user_id or not password:
            raise ValidationError("userId와 password가 필요합니다")

        token = login_and_get_token(
            login_url,
            user_id,
            password,
            force,
            args.get("timeout", settings.timeout)
        )

        return {"success": True, "token": token}

    registry.register(
        name="login",
        description="PillDoc 서비스 로그인 및 인증 토큰 획득",
        handler=login_handler,
        input_schema={
            "type": "object",
            "properties": {
                "userId": {"type": "string", "description": "사용자 ID (이메일)"},
                "password": {"type": "string", "description": "비밀번호"},
                "force": {"type": "boolean", "description": "강제 재로그인", "default": False},
                "loginUrl": {"type": "string", "description": "로그인 URL"},
                "timeout": {"type": "integer", "description": "타임아웃(초)", "default": 15}
            },
            "required": []
        }
    )

    # 2. 계정 도구 등록
    async def get_accounts_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """계정 목록 조회 핸들러"""
        from src.pilldoc.api import get_accounts

        token = ensure_token(
            args.get("token"),
            args.get("userId"),
            args.get("password"),
            args.get("loginUrl"),
            args.get("timeout", settings.timeout)
        )
        base_url = need_base_url(args.get("baseUrl"))

        # 필터 구성
        filters = {}
        filter_keys = [
            "page", "pageSize", "erpKind", "salesChannel", "pharmChain",
            "isAdDisplay", "searchKeyword", "accountType", "bizNo"
        ]
        for key in filter_keys:
            if key in args and args[key] is not None:
                filters[key] = args[key]

        return get_accounts(
            base_url,
            token,
            timeout=args.get("timeout", settings.timeout),
            filters=filters
        )

    registry.register(
        name="pilldoc_accounts",
        description="PillDoc 가입 약국 계정 목록 조회",
        handler=get_accounts_handler,
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "인증 토큰"},
                "userId": {"type": "string", "description": "사용자 ID (토큰 없을 시)"},
                "password": {"type": "string", "description": "비밀번호 (토큰 없을 시)"},
                "baseUrl": {"type": "string", "description": "API 기본 URL"},
                "page": {"type": "integer", "description": "페이지 번호", "minimum": 1},
                "pageSize": {"type": "integer", "description": "페이지 크기", "minimum": 1, "maximum": 100},
                "erpKind": {"type": "array", "items": {"type": "string"}, "description": "ERP 종류 필터"},
                "salesChannel": {"type": "array", "items": {"type": "integer"}, "description": "판매 채널 필터"},
                "pharmChain": {"type": "array", "items": {"type": "string"}, "description": "약국 체인 필터"},
                "isAdDisplay": {"type": "integer", "description": "광고 표시 여부 (0: 표시, 1: 차단)"},
                "searchKeyword": {"type": "string", "description": "검색 키워드"},
                "accountType": {"type": "string", "description": "계정 타입"},
                "bizNo": {"type": "string", "description": "사업자번호"},
                "timeout": {"type": "integer", "description": "타임아웃(초)", "default": 15}
            },
            "required": []
        }
    )

    # 3. 통계 도구 등록
    async def accounts_stats_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """계정 통계 조회 핸들러"""
        from src.pilldoc.api import get_accounts

        token = ensure_token(
            args.get("token"),
            args.get("userId"),
            args.get("password"),
            args.get("loginUrl"),
            args.get("timeout", settings.timeout)
        )
        base_url = need_base_url(args.get("baseUrl"))

        # 필터를 사용하여 여러 번 호출하여 통계 생성
        stats = {
            "total": 0,
            "by_erp": {},
            "by_channel": {},
            "by_chain": {},
            "ad_blocked": 0,
            "ad_displayed": 0
        }

        # 전체 카운트
        result = get_accounts(base_url, token, filters={"pageSize": 1})
        stats["total"] = result.get("totalCount", 0)

        # 광고 차단/표시 통계
        if args.get("includeAdStats", True):
            blocked = get_accounts(base_url, token, filters={"pageSize": 1, "isAdDisplay": 1})
            displayed = get_accounts(base_url, token, filters={"pageSize": 1, "isAdDisplay": 0})
            stats["ad_blocked"] = blocked.get("totalCount", 0)
            stats["ad_displayed"] = displayed.get("totalCount", 0)

        return {"success": True, "statistics": stats}

    registry.register(
        name="pilldoc_accounts_stats",
        description="PillDoc 계정 통계 조회",
        handler=accounts_stats_handler,
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "인증 토큰"},
                "userId": {"type": "string", "description": "사용자 ID"},
                "password": {"type": "string", "description": "비밀번호"},
                "baseUrl": {"type": "string", "description": "API 기본 URL"},
                "includeAdStats": {"type": "boolean", "description": "광고 통계 포함", "default": True},
                "timeout": {"type": "integer", "description": "타임아웃(초)", "default": 15}
            },
            "required": []
        }
    )

    # 4. 약국 검색 도구 등록
    async def find_pharm_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """약국 검색 핸들러"""
        from src.pilldoc.api import find_pharm

        token = ensure_token(
            args.get("token"),
            args.get("userId"),
            args.get("password"),
            args.get("loginUrl"),
            args.get("timeout", settings.timeout)
        )
        base_url = need_base_url(args.get("baseUrl"))

        return find_pharm(
            base_url,
            token,
            biz_no=args.get("bizNo"),
            name=args.get("name"),
            pharm_code=args.get("pharmCode"),
            region=args.get("region"),
            page=args.get("page", 1),
            page_size=args.get("pageSize", 20),
            timeout=args.get("timeout", settings.timeout)
        )

    registry.register(
        name="find_pharm",
        description="약국 검색 (사업자번호, 이름, 약국코드, 지역 등)",
        handler=find_pharm_handler,
        input_schema={
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "인증 토큰"},
                "userId": {"type": "string", "description": "사용자 ID"},
                "password": {"type": "string", "description": "비밀번호"},
                "baseUrl": {"type": "string", "description": "API 기본 URL"},
                "bizNo": {"type": "string", "description": "사업자번호"},
                "name": {"type": "string", "description": "약국명"},
                "pharmCode": {"type": "string", "description": "약국코드"},
                "region": {"type": "string", "description": "지역"},
                "page": {"type": "integer", "description": "페이지 번호", "minimum": 1},
                "pageSize": {"type": "integer", "description": "페이지 크기", "minimum": 1, "maximum": 100},
                "timeout": {"type": "integer", "description": "타임아웃(초)", "default": 15}
            },
            "required": []
        }
    )

    # 5. 서버 관리 도구들
    async def get_metrics_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """메트릭 조회 핸들러"""
        from src.utils.metrics import get_global_metrics
        return get_global_metrics()

    registry.register(
        name="get_server_metrics",
        description="서버 운영 메트릭 조회",
        handler=get_metrics_handler,
        input_schema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

    async def reset_metrics_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """메트릭 초기화 핸들러"""
        from src.utils.metrics import reset_global_metrics
        reset_global_metrics()
        return {"success": True, "message": "메트릭이 초기화되었습니다"}

    registry.register(
        name="reset_server_metrics",
        description="서버 메트릭 초기화",
        handler=reset_metrics_handler,
        input_schema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

    async def health_check_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """헬스체크 핸들러"""
        from src.utils.metrics import get_global_metrics
        metrics = get_global_metrics()
        return {
            "status": "healthy",
            "server": settings.server_name,
            "version": "2.0.0",
            "uptime": metrics.get("uptime_formatted", "unknown")
        }

    registry.register(
        name="health_check",
        description="서버 상태 확인",
        handler=health_check_handler,
        input_schema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

    async def get_config_handler(args: Dict[str, Any]) -> Dict[str, Any]:
        """설정 조회 핸들러"""
        return {
            "server_name": settings.server_name,
            "base_url": settings.edb_base_url,
            "timeout": settings.timeout,
            "max_retries": settings.max_retries,
            "default_page_size": settings.default_page_size,
            "max_page_size": settings.max_page_size,
            "metrics_enabled": settings.enable_metrics,
            "log_level": settings.log_level
        }

    registry.register(
        name="get_server_config",
        description="서버 설정 조회 (민감한 정보 제외)",
        handler=get_config_handler,
        input_schema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )

    logger.info(f"Registered {len(registry.tools)} tools")
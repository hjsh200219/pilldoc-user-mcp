"""상품 주문 관리 도구들"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from mcp.server.fastmcp import FastMCP

from src.pilldoc.api import APIClient
from .helpers import need_base_url, ensure_token


# 상태 코드 매핑
ORDER_STATUS = {
    0: "결제진행중",
    1: "결제완료", 
    2: "주문취소 혹은 환불"
}

# 요청사항 코드 매핑
REQUEST_TYPE = {
    0: "디자인동일",
    1: "전화요청",
    2: "최초주문"
}

# 결제타입 코드 매핑
PAYMENT_TYPE = {
    0: "포인트",
    1: "마일리지", 
    2: "카드"
}

# 검색타입 코드 매핑
SEARCH_TYPE = {
    0: "전체검색(사업자등록번호+약국명+약국장)",
    1: "사업자등록번호만",
    2: "약국명만",
    3: "약국장만"
}


def get_product_orders(
    base_url: str,
    token: str,
    status: Optional[int] = None,
    request_type: Optional[int] = None,
    payment_type: Optional[int] = None,
    search_keyword: Optional[str] = None,
    search_type: int = 0,
    order_date_from: Optional[str] = None,
    order_date_to: Optional[str] = None,
    page_size: int = 20,
    page: int = 1,
    sort_by: Optional[str] = None,
    accept: str = "application/json",
    timeout: int = 15
) -> Dict[str, Any]:
    """
    상품 주문 목록 조회
    
    Args:
        base_url: API 베이스 URL
        token: 인증 토큰
        status: 상태 필터 (0=결제진행중, 1=결제완료, 2=주문취소/환불)
        request_type: 요청사항 필터 (0=디자인동일, 1=전화요청, 2=최초주문)
        payment_type: 결제타입 필터 (0=포인트, 1=마일리지, 2=카드)
        search_keyword: 검색어
        search_type: 검색 타입 (0=전체검색, 1=사업자등록번호만, 2=약국명만, 3=약국장만)
        order_date_from: 주문일시From (YYYY-MM-DD 형식)
        order_date_to: 주문일시To (YYYY-MM-DD 형식)
        page_size: 페이지 크기 (기본값: 20)
        page: 현재 페이지 (기본값: 1)
        sort_by: 정렬 (예: -CreatedAt, CreatedAt)
        accept: Accept 헤더
        timeout: 타임아웃
        
    Returns:
        주문 목록 및 페이징 정보
    """
    url = APIClient._build_url(base_url, "/v1/pilldoc/product-orders")
    headers = APIClient._build_auth_headers(token, accept)
    
    # 쿼리 파라미터 구성
    params = {
        "PageSize": page_size,
        "Page": page,
        "검색타입": search_type
    }
    
    # 선택적 파라미터 추가
    if status is not None:
        params["상태"] = status
    if request_type is not None:
        params["요청사항"] = request_type
    if payment_type is not None:
        params["결제타입"] = payment_type
    if search_keyword:
        params["검색어"] = search_keyword
    if order_date_from:
        params["주문일시From"] = order_date_from
    if order_date_to:
        params["주문일시To"] = order_date_to
    if sort_by:
        params["SortBy"] = sort_by
    
    resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    resp.raise_for_status()
    return APIClient._parse_response(resp)


def analyze_order_statistics(orders_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    주문 데이터 통계 분석
    
    Args:
        orders_data: get_product_orders 결과 데이터
        
    Returns:
        통계 분석 결과
    """
    if not orders_data.get("items"):
        return {"error": "주문 데이터가 없습니다"}
    
    items = orders_data["items"]
    
    # 기본 통계
    stats = {
        "총_주문수": len(items),
        "총_페이지수": orders_data.get("totalPage", 0),
        "전체_주문수": orders_data.get("totalCount", 0),
        "현재_페이지": orders_data.get("nowPage", 1)
    }
    
    # 상태별 통계
    status_stats = {}
    for item in items:
        status_code = item.get("상태")
        status_name = ORDER_STATUS.get(status_code, f"알수없음({status_code})")
        status_stats[status_name] = status_stats.get(status_name, 0) + 1
    stats["상태별_통계"] = status_stats
    
    # 결제타입별 통계
    payment_stats = {}
    for item in items:
        payment_code = item.get("결제타입")
        payment_name = PAYMENT_TYPE.get(payment_code, f"알수없음({payment_code})")
        payment_stats[payment_name] = payment_stats.get(payment_name, 0) + 1
    stats["결제타입별_통계"] = payment_stats
    
    # 요청사항별 통계
    request_stats = {}
    for item in items:
        request_code = item.get("요청사항")
        if request_code is not None:
            request_name = REQUEST_TYPE.get(request_code, f"알수없음({request_code})")
            request_stats[request_name] = request_stats.get(request_name, 0) + 1
        else:
            request_stats["없음"] = request_stats.get("없음", 0) + 1
    stats["요청사항별_통계"] = request_stats
    
    # 금액 통계
    amounts = [item.get("총금액", 0) for item in items if item.get("총금액")]
    if amounts:
        stats["금액_통계"] = {
            "총_주문금액": sum(amounts),
            "평균_주문금액": sum(amounts) / len(amounts),
            "최고_주문금액": max(amounts),
            "최저_주문금액": min(amounts)
        }
    
    # 상품별 통계
    product_stats = {}
    for item in items:
        product_name = item.get("상품명", "알수없음")
        if product_name not in product_stats:
            product_stats[product_name] = {
                "주문수": 0,
                "총수량": 0,
                "총금액": 0
            }
        product_stats[product_name]["주문수"] += 1
        product_stats[product_name]["총수량"] += item.get("주문수량", 0)
        product_stats[product_name]["총금액"] += item.get("총금액", 0)
    stats["상품별_통계"] = product_stats
    
    # 지역별 통계 (배송지 기준)
    region_stats = {}
    for item in items:
        address = item.get("배송지주소", "")
        if address:
            # 주소에서 시/도 추출 (첫 번째 공백 전까지)
            region = address.split()[0] if address.split() else "알수없음"
            region_stats[region] = region_stats.get(region, 0) + 1
    stats["지역별_통계"] = region_stats
    
    return stats


def get_recent_orders(
    base_url: str,
    token: str,
    days: int = 7,
    status: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    최근 N일간의 주문 조회
    
    Args:
        base_url: API 베이스 URL
        token: 인증 토큰
        days: 조회할 일수 (기본값: 7일)
        status: 상태 필터
        **kwargs: 기타 get_product_orders 파라미터
        
    Returns:
        최근 주문 목록
    """
    today = datetime.now()
    from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    
    return get_product_orders(
        base_url=base_url,
        token=token,
        status=status,
        order_date_from=from_date,
        order_date_to=to_date,
        sort_by="-주문일시",
        **kwargs
    )


def search_orders_by_pharmacy(
    base_url: str,
    token: str,
    search_keyword: str,
    search_type: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    약국 정보로 주문 검색
    
    Args:
        base_url: API 베이스 URL
        token: 인증 토큰
        search_keyword: 검색어 (사업자등록번호, 약국명, 약국장명)
        search_type: 검색 타입 (0=전체, 1=사업자등록번호, 2=약국명, 3=약국장)
        **kwargs: 기타 get_product_orders 파라미터
        
    Returns:
        검색된 주문 목록
    """
    return get_product_orders(
        base_url=base_url,
        token=token,
        search_keyword=search_keyword,
        search_type=search_type,
        **kwargs
    )


def register_product_orders_tools(mcp: FastMCP):
    """상품 주문 관리 도구들을 MCP 서버에 등록"""
    
    @mcp.tool("get_product_orders")
    def get_orders_tool(
        status: Optional[int] = None,
        request_type: Optional[int] = None,
        payment_type: Optional[int] = None,
        search_keyword: Optional[str] = None,
        search_type: int = 0,
        order_date_from: Optional[str] = None,
        order_date_to: Optional[str] = None,
        page_size: int = 20,
        page: int = 1,
        sort_by: Optional[str] = None,
        baseUrl: Optional[str] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        loginUrl: Optional[str] = None,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        상품 주문 목록 조회
        
        Args:
            status: 상태 필터 (0=결제진행중, 1=결제완료, 2=주문취소/환불)
            request_type: 요청사항 필터 (0=디자인동일, 1=전화요청, 2=최초주문)
            payment_type: 결제타입 필터 (0=포인트, 1=마일리지, 2=카드)
            search_keyword: 검색어
            search_type: 검색 타입 (0=전체검색, 1=사업자등록번호만, 2=약국명만, 3=약국장만)
            order_date_from: 주문일시From (YYYY-MM-DD 형식)
            order_date_to: 주문일시To (YYYY-MM-DD 형식)
            page_size: 페이지 크기 (기본값: 20)
            page: 현재 페이지 (기본값: 1)
            sort_by: 정렬 (예: -CreatedAt, CreatedAt)
            baseUrl: API 베이스 URL
            token: 인증 토큰
            userId: 사용자 ID (토큰이 없을 때)
            password: 비밀번호 (토큰이 없을 때)
            loginUrl: 로그인 URL
            timeout: 타임아웃
            
        Returns:
            주문 목록 및 페이징 정보
        """
        try:
            base_url = need_base_url(baseUrl)
            auth_token = ensure_token(token, userId, password, loginUrl, timeout)
            
            return get_product_orders(
                base_url=base_url,
                token=auth_token,
                status=status,
                request_type=request_type,
                payment_type=payment_type,
                search_keyword=search_keyword,
                search_type=search_type,
                order_date_from=order_date_from,
                order_date_to=order_date_to,
                page_size=page_size,
                page=page,
                sort_by=sort_by
            )
        except Exception as e:
            return {"error": f"주문 목록 조회 실패: {str(e)}"}
    
    @mcp.tool("analyze_order_statistics")
    def analyze_stats_tool(
        status: Optional[int] = None,
        days: Optional[int] = None,
        order_date_from: Optional[str] = None,
        order_date_to: Optional[str] = None,
        baseUrl: Optional[str] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        loginUrl: Optional[str] = None,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        주문 통계 분석
        
        Args:
            status: 상태 필터 (0=결제진행중, 1=결제완료, 2=주문취소/환불)
            days: 최근 N일간 데이터 (order_date_from/to보다 우선)
            order_date_from: 주문일시From (YYYY-MM-DD 형식)
            order_date_to: 주문일시To (YYYY-MM-DD 형식)
            baseUrl: API 베이스 URL
            token: 인증 토큰
            userId: 사용자 ID (토큰이 없을 때)
            password: 비밀번호 (토큰이 없을 때)
            loginUrl: 로그인 URL
            timeout: 타임아웃
            
        Returns:
            주문 통계 분석 결과
        """
        try:
            base_url = need_base_url(baseUrl)
            auth_token = ensure_token(token, userId, password, loginUrl, timeout)
            
            # 날짜 범위 설정
            if days:
                orders_data = get_recent_orders(
                    base_url=base_url,
                    token=auth_token,
                    days=days,
                    status=status,
                    page_size=100  # 통계를 위해 더 많은 데이터 조회
                )
            else:
                orders_data = get_product_orders(
                    base_url=base_url,
                    token=auth_token,
                    status=status,
                    order_date_from=order_date_from,
                    order_date_to=order_date_to,
                    page_size=100
                )
            
            return analyze_order_statistics(orders_data)
        except Exception as e:
            return {"error": f"주문 통계 분석 실패: {str(e)}"}
    
    @mcp.tool("search_orders_by_pharmacy")
    def search_pharmacy_orders_tool(
        search_keyword: str,
        search_type: int = 0,
        status: Optional[int] = None,
        page_size: int = 20,
        page: int = 1,
        baseUrl: Optional[str] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        loginUrl: Optional[str] = None,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        약국 정보로 주문 검색
        
        Args:
            search_keyword: 검색어 (사업자등록번호, 약국명, 약국장명)
            search_type: 검색 타입 (0=전체검색, 1=사업자등록번호만, 2=약국명만, 3=약국장만)
            status: 상태 필터 (0=결제진행중, 1=결제완료, 2=주문취소/환불)
            page_size: 페이지 크기 (기본값: 20)
            page: 현재 페이지 (기본값: 1)
            baseUrl: API 베이스 URL
            token: 인증 토큰
            userId: 사용자 ID (토큰이 없을 때)
            password: 비밀번호 (토큰이 없을 때)
            loginUrl: 로그인 URL
            timeout: 타임아웃
            
        Returns:
            검색된 주문 목록
        """
        try:
            base_url = need_base_url(baseUrl)
            auth_token = ensure_token(token, userId, password, loginUrl, timeout)
            
            return search_orders_by_pharmacy(
                base_url=base_url,
                token=auth_token,
                search_keyword=search_keyword,
                search_type=search_type,
                status=status,
                page_size=page_size,
                page=page
            )
        except Exception as e:
            return {"error": f"약국 주문 검색 실패: {str(e)}"}
    
    @mcp.tool("get_recent_orders")
    def get_recent_orders_tool(
        days: int = 7,
        status: Optional[int] = None,
        page_size: int = 20,
        page: int = 1,
        baseUrl: Optional[str] = None,
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        loginUrl: Optional[str] = None,
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        최근 N일간의 주문 조회
        
        Args:
            days: 조회할 일수 (기본값: 7일)
            status: 상태 필터 (0=결제진행중, 1=결제완료, 2=주문취소/환불)
            page_size: 페이지 크기 (기본값: 20)
            page: 현재 페이지 (기본값: 1)
            baseUrl: API 베이스 URL
            token: 인증 토큰
            userId: 사용자 ID (토큰이 없을 때)
            password: 비밀번호 (토큰이 없을 때)
            loginUrl: 로그인 URL
            timeout: 타임아웃
            
        Returns:
            최근 주문 목록
        """
        try:
            base_url = need_base_url(baseUrl)
            auth_token = ensure_token(token, userId, password, loginUrl, timeout)
            
            return get_recent_orders(
                base_url=base_url,
                token=auth_token,
                days=days,
                status=status,
                page_size=page_size,
                page=page
            )
        except Exception as e:
            return {"error": f"최근 주문 조회 실패: {str(e)}"}
    
    @mcp.tool("get_order_reference_codes")
    def get_reference_codes_tool() -> Dict[str, Any]:
        """
        주문 관련 참조 코드 목록 조회
        
        Returns:
            상태, 요청사항, 결제타입, 검색타입 코드 매핑
        """
        return {
            "상태코드": ORDER_STATUS,
            "요청사항코드": REQUEST_TYPE,
            "결제타입코드": PAYMENT_TYPE,
            "검색타입코드": SEARCH_TYPE,
            "사용법": {
                "상태필터": "0=결제진행중, 1=결제완료, 2=주문취소/환불",
                "요청사항필터": "0=디자인동일, 1=전화요청, 2=최초주문",
                "결제타입필터": "0=포인트, 1=마일리지, 2=카드",
                "검색타입": "0=전체검색, 1=사업자등록번호만, 2=약국명만, 3=약국장만",
                "날짜형식": "YYYY-MM-DD (예: 2025-09-25)",
                "정렬": "-CreatedAt (내림차순), CreatedAt (오름차순)"
            }
        }

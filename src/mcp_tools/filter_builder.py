"""필터 빌더 유틸리티"""
from typing import Any, Dict, Optional


class FilterBuilder:
    """API 필터 빌드를 위한 헬퍼 클래스"""

    @staticmethod
    def build_account_filters(
        pageSize: Optional[int] = None,
        page: Optional[int] = None,
        page_no: Optional[int] = None,
        page_count: Optional[int] = None,
        sortBy: Optional[str] = None,
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        adBlocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """계정 관련 필터 빌드"""
        filters: Dict[str, Any] = {}

        # 페이지네이션 처리
        if page_no is not None and page is None:
            page = page_no
        if page_count is not None and pageSize is None:
            pageSize = page_count

        # 기본 필터들
        if pageSize is not None:
            filters["pageSize"] = int(pageSize)
        if page is not None:
            filters["page"] = int(page)
        if sortBy is not None:
            filters["sortBy"] = str(sortBy)
        if erpKind is not None:
            filters["erpKind"] = list(erpKind)

        # isAdDisplay / adBlocked 처리
        if isAdDisplay is not None:
            filters["isAdDisplay"] = int(isAdDisplay)
        elif adBlocked is not None:
            # Alias 정정: isAdDisplay=1 이 광고 차단, 0 이 광고 표시
            filters["isAdDisplay"] = 1 if bool(adBlocked) else 0

        if salesChannel is not None:
            filters["salesChannel"] = list(salesChannel)
        if pharmChain is not None:
            filters["pharmChain"] = list(pharmChain)
        if currentSearchType is not None:
            filters["currentSearchType"] = list(currentSearchType)
        if searchKeyword is not None:
            filters["searchKeyword"] = str(searchKeyword)
        if accountType is not None:
            filters["accountType"] = str(accountType)

        return filters

    @staticmethod
    def build_search_filters(
        keyword: Optional[str] = None,
        currentSearchType: Optional[list] = None,
        accountType: Optional[str] = None,
        pharmChain: Optional[list] = None,
        salesChannel: Optional[list] = None,
        erpKind: Optional[list] = None,
        pageSize: int = 100,
        page: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """검색용 필터 빌드"""
        filters: Dict[str, Any] = {"page": page, "pageSize": int(pageSize)}

        if keyword:
            filters["searchKeyword"] = keyword
        if currentSearchType is not None:
            filters["currentSearchType"] = list(currentSearchType)
        if accountType is not None:
            filters["accountType"] = str(accountType)
        if pharmChain is not None:
            filters["pharmChain"] = list(pharmChain)
        if salesChannel is not None:
            filters["salesChannel"] = list(salesChannel)
        if erpKind is not None:
            filters["erpKind"] = list(erpKind)

        return filters
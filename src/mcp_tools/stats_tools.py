"""통계 관련 도구들"""
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests as _req

from src.pilldoc.api import get_accounts
from .helpers import need_base_url, ensure_token, items_of, handle_http_error


def register_stats_tools(mcp: FastMCP) -> None:
    """통계 관련 도구들 등록"""

    @mcp.tool()
    def pilldoc_summary(
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        # filters
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
        # summary options
        metric: str = "count",  # supports: count
        splitBy: Optional[str] = None,  # e.g., "isAdDisplay"
        year: Optional[int] = None,  # 연도 필터(YYYY)
        month: Optional[int] = None, # 월 필터(1-12)
        groupBy: Optional[str] = None,  # e.g., "region", "month"
    ) -> Dict[str, Any]:
        """일반화된 최소 응답 요약 도구. 기본은 count만 반환. splitBy 지정 시 분할 카운트.
        - isAdDisplay 규약: 0=표시(차단 아님), 1=차단
        - 최소 토큰 사용을 위해 pageSize=1로 메타 정보만 조회
        """
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        def _count_with(_filters: Dict[str, Any]) -> Optional[int]:
            try:
                r = get_accounts(base_url, tok, accept, timeout, filters=_filters)
                return int(r.get("totalCount")) if isinstance(r, dict) and r.get("totalCount") is not None else None
            except Exception:
                return None

        # 공통 필터(메타만): pageSize=1
        base_filters: Dict[str, Any] = {"page": 1, "pageSize": 1}
        if erpKind is not None:
            base_filters["erpKind"] = list(erpKind)
        if isAdDisplay is not None:
            base_filters["isAdDisplay"] = int(isAdDisplay)
        if salesChannel is not None:
            base_filters["salesChannel"] = list(salesChannel)
        if pharmChain is not None:
            base_filters["pharmChain"] = list(pharmChain)
        if currentSearchType is not None:
            base_filters["currentSearchType"] = list(currentSearchType)
        if searchKeyword is not None:
            base_filters["searchKeyword"] = str(searchKeyword)
        if accountType is not None:
            base_filters["accountType"] = str(accountType)

        if metric != "count":
            return {"error": "unsupported_metric", "metric": metric}

        # 분할 카운트: splitBy가 isAdDisplay이고, 호출자가 isAdDisplay를 지정하지 않은 경우 0/1 두 번만 호출
        if splitBy == "isAdDisplay" and isAdDisplay is None and groupBy is None:
            f0 = dict(base_filters)
            f0["isAdDisplay"] = 0
            f1 = dict(base_filters)
            f1["isAdDisplay"] = 1
            return {"countDisplayed": _count_with(f0), "countBlocked": _count_with(f1)}

        # 연/월 집계: groupBy=month, year 지정 시 해당 연도의 월별 카운트(1..12)
        if groupBy == "month" and year is not None:
            out = []
            for m in range(1, 13):
                f = dict(base_filters)
                f["year"] = int(year)
                f["month"] = int(m)
                out.append({"month": f"{year}-{m:02d}", "count": _count_with(f)})
            return {"monthly": out}

        # 지역 집계: groupBy=region (최소 토큰 위해 accounts API가 region 필터/집계를 직접 제공하지 않으면 count만 반환)
        if groupBy == "region":
            return {"error": "unsupported_groupBy", "groupBy": groupBy}

        # 기본 단일 카운트
        return {"count": _count_with(base_filters)}

    @mcp.tool()
    def pilldoc_accounts_stats(
        token: Optional[str] = None,
        userId: Optional[str] = None,
        password: Optional[str] = None,
        force: bool = False,
        loginUrl: Optional[str] = None,
        baseUrl: Optional[str] = None,
        accept: str = "application/json",
        timeout: int = 15,
        pageSize: int = 200,
        maxPages: int = 0,
        sortBy: Optional[str] = None,
        erpKind: Optional[list] = None,
        isAdDisplay: Optional[int] = None,
        adBlocked: Optional[bool] = None,
        salesChannel: Optional[list] = None,
        pharmChain: Optional[list] = None,
        currentSearchType: Optional[list] = None,
        searchKeyword: Optional[str] = None,
        accountType: Optional[str] = None,
    ) -> Dict[str, Any]:
        """pilldoc 계정 목록을 페이지네이션으로 수집해 통계(월별/지역별/ERP/광고차단)를 집계합니다."""
        base_url = need_base_url(baseUrl)
        tok = ensure_token(token, userId, password, loginUrl, timeout)

        def _region_of(item: Dict[str, Any]) -> Optional[str]:
            for key in ("검색용주소", "주소"):
                val = str(item.get(key) or "").strip()
                if val and val != "None":
                    try:
                        return val.split()[0]
                    except Exception:
                        return None
            return None

        def _month_of(created_at: Optional[str]) -> Optional[str]:
            if not created_at:
                return None
            s = str(created_at)
            # ISO-like: YYYY-MM-... → first 7 chars
            return s[:7] if len(s) >= 7 else None

        def _ad_blocked_of(item: Dict[str, Any]) -> Optional[bool]:
            # 서버 정의: isAdDisplay 0=표시(차단 아님), 1=차단
            isd = item.get("isAdDisplay")
            try:
                if isd is not None:
                    return bool(int(isd) == 1)
            except Exception:
                pass
            # 폴백: 라벨 해석
            label_raw = item.get("광고차단")
            label = str(label_raw).strip()
            if label == "":
                return None
            low = label.lower()
            blocked_true_vals = {"차단", "y", "yes", "true", "blocked", "block"}
            blocked_false_vals = {"표시", "표시중", "n", "no", "false", "display", "미표시"}
            if low in blocked_true_vals:
                return True
            if low in blocked_false_vals:
                return False
            return None

        total_reported: Optional[int] = None
        pages_fetched = 0
        first_created: Optional[str] = None
        last_created: Optional[str] = None

        monthly: Dict[str, int] = {}
        region: Dict[str, int] = {}
        erp: Dict[str, int] = {}
        adstats = {"blocked": 0, "notBlocked": 0, "unknown": 0}

        page = 1
        last_page: Optional[int] = None

        while True:
            filters: Dict[str, Any] = {"page": page, "pageSize": int(pageSize)}
            if sortBy is not None:
                filters["sortBy"] = str(sortBy)
            if erpKind is not None:
                filters["erpKind"] = list(erpKind)
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

            try:
                resp = get_accounts(base_url, tok, accept, timeout, filters=filters)
            except _req.HTTPError as e:
                result = handle_http_error(e, "accounts")
                result["page"] = page
                return result

            if total_reported is None and isinstance(resp, dict):
                try:
                    total_reported = int(resp.get("totalCount")) if resp.get("totalCount") is not None else None
                except Exception:
                    total_reported = None

            if last_page is None and isinstance(resp, dict):
                try:
                    total_page = int(resp.get("totalPage")) if resp.get("totalPage") is not None else None
                except Exception:
                    total_page = None
                if maxPages and maxPages > 0 and total_page is not None:
                    last_page = min(int(maxPages), int(total_page))
                else:
                    last_page = int(maxPages) if maxPages and maxPages > 0 else total_page or 1

            items = items_of(resp)
            if not items:
                break
            pages_fetched += 1

            for it in items:
                if not isinstance(it, dict):
                    continue

                # createdAt range
                created_at = str(it.get("createdAt") or "").strip()
                if created_at:
                    if first_created is None or created_at < first_created:
                        first_created = created_at
                    if last_created is None or created_at > last_created:
                        last_created = created_at

                # monthly
                mkey = _month_of(created_at)
                if mkey:
                    monthly[mkey] = monthly.get(mkey, 0) + 1

                # region
                rkey = _region_of(it)
                if rkey:
                    region[rkey] = region.get(rkey, 0) + 1

                # erp
                ecode = it.get("erpCode")
                ekey = "null" if ecode is None else str(ecode)
                erp[ekey] = erp.get(ekey, 0) + 1

                # ad block
                ab = _ad_blocked_of(it)
                if ab is True:
                    adstats["blocked"] += 1
                elif ab is False:
                    adstats["notBlocked"] += 1
                else:
                    adstats["unknown"] += 1

            if last_page is not None and page >= last_page:
                break
            page += 1

        def _sorted_dict_counts(d: Dict[str, int], by_numeric_key: bool = False) -> Any:
            try:
                if by_numeric_key:
                    items_sorted = sorted(((k, v) for k, v in d.items()), key=lambda kv: (int(kv[0]) if kv[0].lstrip("-+").isdigit() else 10**9, kv[0]))
                else:
                    items_sorted = sorted(d.items(), key=lambda kv: kv[0])
            except Exception:
                items_sorted = sorted(d.items(), key=lambda kv: kv[0])
            return [{"key": k, "count": v} for k, v in items_sorted]

        monthly_sorted = [{"month": k, "count": v} for k, v in sorted(monthly.items(), key=lambda kv: kv[0])]
        region_sorted = _sorted_dict_counts(region)
        erp_sorted = _sorted_dict_counts(erp, by_numeric_key=True)

        return {
            "filters": {
                "pageSize": pageSize,
                "maxPages": maxPages,
                "sortBy": sortBy,
                "erpKind": erpKind,
                "isAdDisplay": isAdDisplay if isAdDisplay is not None else (0 if adBlocked else (1 if adBlocked is False else None)),
                "salesChannel": salesChannel,
                "pharmChain": pharmChain,
                "currentSearchType": currentSearchType,
                "searchKeyword": searchKeyword,
                "accountType": accountType,
            },
            "totalCountReported": total_reported,
            "pagesFetched": pages_fetched,
            "period": {"from": first_created, "to": last_created},
            "stats": {
                "monthly": monthly_sorted,
                "region": region_sorted,
                "erpCode": erp_sorted,
                "adBlocked": adstats,
            },
        }
#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
try:
    from src.auth import extract_token, login_and_get_token
except ModuleNotFoundError:
    import os as _os
    import sys as _sys
    # 프로젝트 루트를 sys.path에 추가하여 'scripts' 패키지를 찾을 수 있게 함
    _sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
    from src.auth import extract_token, login_and_get_token


# 로그인 URL은 환경변수 EDB_LOGIN_URL 로만 설정합니다
ENDPOINT = "/v1/druginfo/main-ingredient"


# Load environment variables from .env and .env.local (if present)
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)


## auth helpers moved to scripts.auth (extract_token, login_and_get_token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="주성분 목록 조회")
    # API target (no hardcoded default; use env only)
    parser.add_argument("--base-url", default=os.getenv("EDB_BASE_URL"), help="API Base URL (env: EDB_BASE_URL)")
    parser.add_argument("--accept", default=os.getenv("EDB_ACCEPT", "application/json"), help="Accept 헤더")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("EDB_TIMEOUT", "15")), help="타임아웃(초)")
    # Query params
    parser.add_argument("--page", type=int, default=int(os.getenv("EDB_PAGE", "1")), help="페이지 번호 (기본 1)")
    parser.add_argument("--pageSize", type=int, default=int(os.getenv("EDB_PAGE_SIZE", "20")), help="페이지 크기 (기본 20)")
    parser.add_argument("--ingredientNameKor", type=str, help="주성분 한글명으로 필터링")
    # Swagger 고정 파라미터들
    parser.add_argument("--IngredientCode", type=str, help="검색 키워드: 주성분코드")
    parser.add_argument("--drugKind", type=str, help="검색 키워드: 약품분류")
    parser.add_argument("--SortBy", type=str, help="정렬 (예: -CreatedAt, CreatedAt)")
    # boolean 파라미터는 tri-state 유지를 위해 문자열 true/false 로 받음
    for _bool_name in [
        "a4", "a4Off", "a5", "a5Off",
        "drugkind", "drugkindOff",
        "effect", "effectOff",
        "showMapped",
    ]:
        parser.add_argument(f"--{_bool_name}", choices=["true", "false"], help=f"{_bool_name} 필터 (true/false)")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="임의의 쿼리 파라미터 추가 (형식: key=value). 여러 번 지정 가능",
    )
    # Auth: token or login
    parser.add_argument("--token", default=os.getenv("EDB_TOKEN"), help="직접 제공할 JWT 토큰 (있으면 로그인 생략)")
    parser.add_argument("--userId", default=os.getenv("EDB_USER_ID"), help="로그인용 사용자 ID")
    parser.add_argument("--password", default=os.getenv("EDB_PASSWORD"), help="로그인용 비밀번호")
    parser.add_argument("--login-url", default=os.getenv("EDB_LOGIN_URL"), help="로그인 엔드포인트 URL (env: EDB_LOGIN_URL)")
    parser.add_argument("--force", action="store_true", default=os.getenv("EDB_FORCE_LOGIN", "false").lower() in ("1", "true", "yes"), help="isForceLogin=true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    # Prepare token
    token = args.token
    if not token:
        if not args.userId or not args.password:
            print("--token 또는 --userId/--password 를 제공해야 합니다.", file=sys.stderr)
            return 2
        try:
            token = login_and_get_token(args.login_url, args.userId, args.password, bool(args.force), int(args.timeout))
        except requests.HTTPError as http_err:
            print(f"HTTP error: {http_err}", file=sys.stderr)
            if http_err.response is not None:
                try:
                    print(json.dumps(http_err.response.json(), ensure_ascii=False, indent=2), file=sys.stderr)
                except Exception:
                    print(http_err.response.text, file=sys.stderr)
            return 1
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 1

    # Build URL with query params
    if not args.base_url:
        print("환경변수 EDB_BASE_URL 가 설정되지 않았습니다. .env(.local)에 EDB_BASE_URL을 설정하거나 --base-url로 지정하세요.", file=sys.stderr)
        return 2
    url = f"{args.base_url.rstrip('/')}{ENDPOINT}"
    params = {"Page": int(args.page), "PageSize": int(args.pageSize)}
    if args.ingredientNameKor:
        params["ingredientNameKor"] = args.ingredientNameKor
    if args.IngredientCode:
        params["IngredientCode"] = args.IngredientCode
    if args.drugKind:
        params["drugKind"] = args.drugKind
    if args.SortBy:
        params["SortBy"] = args.SortBy
    # boolean params 반영 (문자열 그대로 전달: 'true' or 'false')
    for _bool_name in [
        "a4", "a4Off", "a5", "a5Off",
        "drugkind", "drugkindOff",
        "effect", "effectOff",
        "showMapped",
    ]:
        val = getattr(args, _bool_name)
        if val is not None:
            params[_bool_name] = val
    # parse additional arbitrary params
    for kv in args.param:
        if not isinstance(kv, str) or "=" not in kv:
            print(f"무시된 파라미터: {kv!r} (형식: key=value)", file=sys.stderr)
            continue
        k, v = kv.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            print(f"무시된 파라미터: {kv!r} (key가 비어있음)", file=sys.stderr)
            continue
        if v == "":
            # 빈 값도 서버에 넘기고 싶다면 여기서 continue 제거
            continue
        params[k] = v

    headers = {"accept": args.accept, "Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=int(args.timeout))
        resp.raise_for_status()
    except requests.HTTPError as http_err:
        print(f"HTTP error: {http_err}", file=sys.stderr)
        if http_err.response is not None:
            try:
                print(json.dumps(http_err.response.json(), ensure_ascii=False, indent=2), file=sys.stderr)
            except Exception:
                print(http_err.response.text, file=sys.stderr)
        return 1
    except requests.RequestException as req_err:
        print(f"Request error: {req_err}", file=sys.stderr)
        return 1

    # Output
    try:
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except ValueError:
        print(resp.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())



#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
try:
    from src.auth import extract_token
except ModuleNotFoundError:
    import os as _os
    import sys as _sys
    _sys.path.append(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from src.auth import extract_token


# 로그인 URL은 환경변수 EDB_LOGIN_URL 로만 설정합니다

# Load env for convenience
load_dotenv(".env", override=False)
load_dotenv(".env.local", override=False)


## token extraction moved to scripts.auth.extract_token


def fetch_jwt(
    login_url: str,
    user_id: str,
    password: str,
    is_force_login: bool = False,
    timeout: int = 15,
) -> Dict[str, Any]:
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "userId": user_id,
        "password": password,
        "isForceLogin": bool(is_force_login),
    }

    resp = requests.post(
        login_url,
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        # Not JSON; return text under a key
        return {"raw": resp.text}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Login and print JWT token or call API with Bearer")
    # Common options
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("EDB_TIMEOUT", "15")),
        help="Request timeout seconds (default: 15)",
    )
    # Login options
    parser.add_argument(
        "--url",
        default=os.getenv("EDB_LOGIN_URL"),
        help="Login endpoint URL (env: EDB_LOGIN_URL)",
    )
    parser.add_argument(
        "--userId",
        default=os.getenv("EDB_USER_ID"),
        help="User ID (email)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("EDB_PASSWORD"),
        help="Password",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=os.getenv("EDB_FORCE_LOGIN", "false").lower() in ("1", "true", "yes"),
        help="Set isForceLogin=true",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print full JSON response instead of extracting token (login mode)",
    )
    # Bearer GET options
    parser.add_argument(
        "--get",
        dest="get_url",
        help="Perform a GET request with Bearer token to this URL",
    )
    parser.add_argument(
        "--token",
        help="Use this token directly (skips login)",
    )
    parser.add_argument(
        "--accept",
        default=os.getenv("EDB_ACCEPT", "application/json"),
        help="Accept header for GET request (default: application/json)",
    )
    return parser


def perform_get(url: str, token: str, accept: str, timeout: int) -> Dict[str, Any]:
    headers = {
        "accept": accept,
        "Authorization": f"Bearer {token}",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    try:
        return {"json": resp.json()}
    except ValueError:
        return {"text": resp.text}


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    # If GET mode is requested, prepare a token then perform GET
    if args.get_url:
        token = args.token
        if not token:
            # Need to login to obtain token
            if not args.userId or not args.password:
                print("--token 을 제공하거나, --userId 와 --password 로 로그인 후 호출할 수 있습니다.", file=sys.stderr)
                return 2
            try:
                login_data = fetch_jwt(
                    login_url=args.url,
                    user_id=args.userId,
                    password=args.password,
                    is_force_login=bool(args.force),
                    timeout=int(args.timeout),
                )
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
            token = extract_token(login_data)
            if not token:
                print("로그인 응답에서 토큰을 찾지 못했습니다. --raw 로 확인해보세요.", file=sys.stderr)
                print(json.dumps(login_data, ensure_ascii=False, indent=2), file=sys.stderr)
                return 2

        # Perform GET with token
        try:
            result = perform_get(args.get_url, token, args.accept, int(args.timeout))
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

        if "json" in result:
            print(json.dumps(result["json"], ensure_ascii=False, indent=2))
        else:
            print(result["text"])  # text response
        return 0

    # Default behavior: login and output token or full JSON
    try:
        data = fetch_jwt(
            login_url=args.url,
            user_id=args.userId if args.userId is not None else "",
            password=args.password if args.password is not None else "",
            is_force_login=bool(args.force),
            timeout=int(args.timeout),
        )
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

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    token = extract_token(data)
    if token:
        print(token)
        return 0

    print("토큰을 응답에서 찾지 못했습니다. --raw 로 전체 응답을 확인하세요.", file=sys.stderr)
    print(json.dumps(data, ensure_ascii=False, indent=2), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())



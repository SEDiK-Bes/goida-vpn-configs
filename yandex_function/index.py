# ============================================================
# GENERIC DATA PROXY SERVICE v1.0
# (На самом деле - прокси к githubmirror/*.txt)
# ============================================================
#
# Назначение:
# - выдавать данные по параметру ?source=set_a|set_b|set_c
# - URL источников хранить в env (REMOTE_SOURCE_1/2/3)
# - выглядеть как обычный data endpoint (без слов vpn/proxy в ответах)
#
# Требования:
# - requests==2.31.0

import requests
import json
import os
from datetime import datetime

ENDPOINTS = {
    "set_a": os.environ.get("REMOTE_SOURCE_1", ""),
    "set_b": os.environ.get("REMOTE_SOURCE_2", ""),
    "set_c": os.environ.get("REMOTE_SOURCE_3", ""),
}

GENERIC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def log_action(action_code, details=""):
    timestamp = datetime.utcnow().isoformat()
    print(f"[{timestamp}] {action_code} {details}")


def handler(event, context):
    try:
        query = event.get("queryStringParameters", {}) or {}
        source = (query.get("source") or "set_a").lower()

        if source not in ENDPOINTS:
            log_action("ERR_INVALID_SOURCE", source)
            return {
                "statusCode": 400,
                "body": json.dumps({"status": "error", "code": "INVALID_PARAM"}),
            }

        url = ENDPOINTS[source]
        if not url:
            log_action("ERR_MISSING_CONFIG", source)
            return {
                "statusCode": 500,
                "body": json.dumps({"status": "error", "code": "CONFIG_MISSING"}),
            }

        log_action("FETCH_START", f"source={source}")

        r = requests.get(url, headers=GENERIC_HEADERS, timeout=10, allow_redirects=True)
        if r.status_code != 200:
            log_action("FETCH_FAILED", f"http_{r.status_code}")
            return {
                "statusCode": 502,
                "body": json.dumps({"status": "error", "code": "REMOTE_ERROR"}),
            }

        data = r.text
        log_action("FETCH_SUCCESS", f"size={len(data)}")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/plain; charset=utf-8",
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "X-Cache": "BYPASS",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
            "body": data,
        }

    except requests.Timeout:
        log_action("ERR_TIMEOUT")
        return {
            "statusCode": 504,
            "body": json.dumps({"status": "error", "code": "TIMEOUT"}),
        }
    except Exception as e:
        log_action("ERR_EXCEPTION", str(type(e).__name__)[:20])
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "code": "INTERNAL_ERROR"}),
        }

#!/usr/bin/env python3
"""Generate and publish the view-only on-call schedule to Cloudflare Workers KV."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_schedule import build_schedule
import yaml

API_ROOT = "https://api.cloudflare.com/client/v4"


def publish(schedule: dict, account_id: str, namespace_id: str, api_token: str, key: str) -> dict:
    url = f"{API_ROOT}/accounts/{account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
    request = urllib.request.Request(
        url,
        data=json.dumps(schedule, separators=(",", ":")).encode("utf-8"),
        method="PUT",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response.read()
            return {"success": True, "status": response.status}
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cloudflare KV upload failed with HTTP {error.code}: {body}") from error


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="Private authoritative on-call YAML")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--months-ahead", type=int, default=6)
    parser.add_argument("--key", default="schedule")
    args = parser.parse_args()

    source = yaml.safe_load(args.source.read_text(encoding="utf-8"))
    schedule = build_schedule(source, args.today, args.months_ahead)
    result = publish(
        schedule=schedule,
        account_id=required_env("CLOUDFLARE_ACCOUNT_ID"),
        namespace_id=required_env("CLOUDFLARE_KV_NAMESPACE_ID"),
        api_token=required_env("CLOUDFLARE_API_TOKEN"),
        key=args.key,
    )
    print(json.dumps({"status": "published", "blocks": len(schedule["blocks"]), **result}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)

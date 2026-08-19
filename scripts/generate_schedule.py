#!/usr/bin/env python3
"""Generate public, read-only on-call blocks from the approved rotation state."""

from __future__ import annotations

import argparse
import calendar
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


def parse_datetime(value: str, timezone: ZoneInfo) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.astimezone(timezone) if parsed.tzinfo else parsed.replace(tzinfo=timezone)


def end_of_month_months_ahead(today: date, months_ahead: int, timezone: ZoneInfo) -> datetime:
    month_index = today.month - 1 + months_ahead
    year = today.year + month_index // 12
    month = month_index % 12 + 1
    return datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, tzinfo=timezone)


def source_parts(source: dict) -> tuple[str, list[str], datetime, list[dict]]:
    timezone_name = source["timezone"]
    rotation = source["rotation"]
    members = [member["name"] for member in rotation["members"]]
    if not members:
        raise ValueError("rotation.members must contain at least one responder")
    timezone = ZoneInfo(timezone_name)
    anchor_data = rotation["rotation_anchor"]
    anchor = parse_datetime(anchor_data["start"], timezone)
    primary = anchor_data["primary"]
    if primary not in members:
        raise ValueError("rotation anchor primary must be in rotation members")
    return timezone_name, members, anchor, source.get("overrides", [])


def matching_override(block_start: datetime, block_end: datetime, overrides: list[dict], timezone: ZoneInfo) -> dict | None:
    for override in overrides:
        start = parse_datetime(override["start"], timezone)
        end = parse_datetime(override["end"], timezone)
        if start <= block_start and end >= block_end:
            return override
    return None


def build_schedule(source: dict, today: date, months_ahead: int) -> dict:
    timezone_name, members, anchor, overrides = source_parts(source)
    timezone = ZoneInfo(timezone_name)
    target_end = end_of_month_months_ahead(today, months_ahead, timezone)
    primary_index = members.index(source["rotation"]["rotation_anchor"]["primary"])
    blocks = []
    current = anchor
    block_number = 0

    while current <= target_end:
        end = current + timedelta(days=7)
        override = matching_override(current, end, overrides, timezone)
        primary = override.get("coverer") if override else members[(primary_index + block_number) % len(members)]
        blocks.append(
            {
                "start": current.isoformat(),
                "end": end.isoformat(),
                "primary": primary,
                "override": bool(override),
                "note": (override or {}).get("reason", ""),
            }
        )
        current = end
        block_number += 1

    return {
        "service": source.get("service", "ISCO After-Hours On-Call"),
        "timezone": timezone_name,
        "generated_at": today.isoformat(),
        "coverage_through": target_end.isoformat(),
        "blocks": blocks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--months-ahead", type=int, default=6)
    args = parser.parse_args()

    if args.months_ahead < 1:
        raise SystemExit("--months-ahead must be at least 1")
    source = yaml.safe_load(args.source.read_text(encoding="utf-8"))
    schedule = build_schedule(source, args.today, args.months_ahead)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schedule, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

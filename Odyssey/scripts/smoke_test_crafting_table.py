#!/usr/bin/env python3
"""Craft a table with Odyssey's existing skills through Mineflayer."""

from __future__ import annotations

import argparse
import json
from http.client import RemoteDisconnected
from pathlib import Path
from urllib import error, request


ODYSSEY_ROOT = Path(__file__).resolve().parent.parent
CONTROL_PRIMITIVES = ODYSSEY_ROOT / "odyssey" / "control_primitives"
SKILL_ROOT = ODYSSEY_ROOT / "skill_library" / "skill"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def post_json(url: str, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bridge", default="http://127.0.0.1:3000")
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    programs = "\n\n".join(
        [
            read_text(CONTROL_PRIMITIVES / "exploreUntil.js"),
            read_text(CONTROL_PRIMITIVES / "mineBlock.js"),
            read_text(CONTROL_PRIMITIVES / "craftItem.js"),
            read_text(SKILL_ROOT / "primitive" / "getPlanksCount.js"),
            read_text(SKILL_ROOT / "compositional" / "mineWoodLog.js"),
            read_text(SKILL_ROOT / "compositional" / "craftWoodenPlanks.js"),
            read_text(SKILL_ROOT / "compositional" / "craftCraftingTable.js"),
        ]
    )
    payload = {
        "programs": programs,
        "code": "await craftCraftingTable(bot);",
    }

    try:
        observation = post_json(
            f"{args.bridge.rstrip('/')}/step", payload, args.timeout
        )
    except (error.URLError, RemoteDisconnected, TimeoutError) as exc:
        print(f"Mineflayer request failed: {exc}")
        return 2

    # The bridge JSON-serializes observations before Express serializes them.
    if isinstance(observation, str):
        observation = json.loads(observation)

    observe_events = [
        event for event_type, event in observation if event_type == "observe"
    ]
    if not observe_events:
        print(json.dumps(observation, indent=2))
        print("FAIL: the bridge returned no final observe event")
        return 1

    inventory = observe_events[-1].get("inventory", {})
    crafting_tables = inventory.get("crafting_table", 0)
    materials = {
        name: count
        for name, count in inventory.items()
        if name.endswith("_log") or name.endswith("_planks")
    }
    print(
        json.dumps(
            {
                "crafting_table": crafting_tables,
                "materials": materials,
                "inventory": inventory,
            },
            indent=2,
        )
    )
    if crafting_tables < 1:
        print("FAIL: no crafting table was produced")
        return 1

    print("PASS: craftCraftingTable produced at least one crafting table")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

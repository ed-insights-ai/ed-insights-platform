#!/usr/bin/env python3
"""Regenerate ROADMAP.md from the beads issue database.

ROADMAP.md is a *derived* file. Beads is the source of truth — edit issues with
`bd`, then run this to refresh the committed view:

    uv run scripts/roadmap.py     # or: python3 scripts/roadmap.py

Why a generated markdown at all, when `bd` already answers every question:
GitHub renders it, a reviewer without `bd` installed can read it, and it diffs
in a PR. Nothing reads it back.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "ROADMAP.md"

# Epics in delivery order. Beads has no ordering field, and priority alone
# collapses S6/S7 together, so the sequence lives here.
EPIC_ORDER = [
    "S0 — Pipeline hardening",
    "S0.5 — Repair the existing data",
    "S1 — The canon and the first Observation",
    "S2 — Feed Health, the first board",
    "S3 — The Table and The Slate",
    "S4 — The refresh DAG and the wall clock",
    "S5 — Tools and chat ◆ v1",
    "API correctness",
    "S6 — The Match Page and the Dispatch",
    "S7 — The Race",
    "S8 — Form, the clock, per-team panels, game_id fix",
    "S9 — Post-season and deferred correctness",
]

STATUS_MARK = {
    "open": " ",
    "in_progress": "~",
    "closed": "x",
    "blocked": " ",
    "deferred": "-",
}


def load() -> list[dict]:
    raw = subprocess.run(
        ["bd", "list", "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    data = json.loads(raw)
    return data if isinstance(data, list) else data.get("issues", data)


def blockers(issue: dict) -> list[str]:
    """Real blocking deps only — parent-child is structure, not sequence."""
    return [
        d["depends_on_id"]
        for d in issue.get("dependencies") or []
        if d.get("type") != "parent-child"
    ]


def main() -> int:
    issues = load()
    by_id = {i["id"]: i for i in issues}

    epics = [i for i in issues if i["issue_type"] == "epic"]
    tasks = [i for i in issues if i["issue_type"] != "epic"]

    children: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        children[t.get("parent") or ""].append(t)

    # An issue is actionable when every blocker is closed.
    def ready(t: dict) -> bool:
        if t["status"] not in ("open",):
            return False
        return all(by_id.get(b, {}).get("status") == "closed" for b in blockers(t))

    open_tasks = [t for t in tasks if t["status"] != "closed"]
    ready_now = sorted(
        (t for t in open_tasks if ready(t)),
        key=lambda t: (t["priority"], t["id"]),
    )

    order = {name: n for n, name in enumerate(EPIC_ORDER)}
    epics.sort(key=lambda e: order.get(e["title"], 99))

    L: list[str] = []
    add = L.append

    add("# Touchline — Roadmap")
    add("")
    add(
        f"*Generated from beads on {date.today().isoformat()} by "
        "`scripts/roadmap.py`. Do not edit — edit the issues with `bd` and "
        "regenerate.*"
    )
    add("")
    add(
        "The goal: turn an amnesiac dataset into a season you can ask questions "
        "about. See [`docs/specs/touchline-rib.md`](docs/specs/touchline-rib.md) "
        "for the build plan and "
        "[`ADR-008`](docs/decisions/ADR-008-touchline-keelson-rib.md) for why."
    )
    add("")

    done = sum(1 for t in tasks if t["status"] == "closed")
    add(
        f"**{done}/{len(tasks)} tasks complete** across {len(epics)} epics · "
        f"**{len(ready_now)} ready to start** · "
        f"{len(open_tasks) - len(ready_now)} waiting on a blocker"
    )
    add("")

    add("## Start here")
    add("")
    add("Work with no unmet blockers, highest priority first:")
    add("")
    add("| | Issue | Task | Epic |")
    add("|---|---|---|---|")
    for t in ready_now[:12]:
        epic = by_id.get(t.get("parent") or "", {}).get("title", "—")
        ref = f" ([#{t['external_ref'].split('-')[1]}]" \
              f"(https://github.com/ed-insights-ai/ed-insights-platform/issues/" \
              f"{t['external_ref'].split('-')[1]}))" if t.get("external_ref") else ""
        add(f"| P{t['priority']} | `{t['id']}` | {t['title']}{ref} | {epic.split(' — ')[0]} |")
    add("")
    add("```bash")
    add("bd ready --exclude-type=epic   # the live version of this table")
    add("bd show <id>                   # full mechanism, evidence, acceptance")
    add("bd update <id> --claim         # take it")
    add("```")
    add("")

    add("## Epics")
    add("")

    for e in epics:
        kids = sorted(children.get(e["id"], []), key=lambda t: (t["priority"], t["id"]))
        kdone = sum(1 for t in kids if t["status"] == "closed")
        add(f"### {e['title']}")
        add("")
        add(f"`{e['id']}` · {kdone}/{len(kids)} complete")
        add("")
        # First paragraph of the epic description carries the "why".
        lead = (e.get("description") or "").split("\n\n")[0].strip()
        if lead:
            add(lead)
            add("")
        if not kids:
            add("*No tasks.*")
            add("")
            continue
        for t in kids:
            mark = STATUS_MARK.get(t["status"], " ")
            blocked = [
                b for b in blockers(t)
                if by_id.get(b, {}).get("status") != "closed"
            ]
            bits = [f"- [{mark}] `{t['id']}` **P{t['priority']}** {t['title']}"]
            if t.get("external_ref", "").startswith("gh-"):
                n = t["external_ref"].split("-")[1]
                bits.append(
                    f" ([#{n}](https://github.com/ed-insights-ai/"
                    f"ed-insights-platform/issues/{n}))"
                )
            if blocked:
                names = ", ".join(f"`{b}`" for b in blocked)
                bits.append(f" — *blocked by {names}*")
            add("".join(bits))
        add("")

    add("## How this is tracked")
    add("")
    add(
        "Issues live in [beads](https://github.com/gastownhall/beads) under "
        "`.beads/` — a dependency-aware tracker, so `bd ready` only ever shows "
        "work whose prerequisites are actually done. `.beads/issues.jsonl` is "
        "the committed export; the Dolt database itself is gitignored."
    )
    add("")
    add(
        "The Keelson `bead-work` workflow claims the next ready issue and drives "
        "it to a draft PR without being told which one to pick."
    )
    add("")
    add(
        "GitHub issues are kept for the ones that already had a written-up "
        "mechanism; the bead carries `external_ref: gh-N` and the two stay "
        "linked. New work goes in beads only."
    )
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} — {len(tasks)} tasks, {len(epics)} epics, {len(ready_now)} ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())

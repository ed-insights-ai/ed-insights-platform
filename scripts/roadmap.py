#!/usr/bin/env python3
"""Regenerate ROADMAP.md from the beads issue database.

ROADMAP.md is a *derived* file. Beads is the source of truth — edit issues with
`bd`, then run this to refresh the committed view:

    python3 scripts/roadmap.py

Division of labour between the three documents, so they stop duplicating:

    STATUS.md   why we are doing this, in plain language. Narrative. Hand-written.
    ROADMAP.md  what is left and what to pick up next. Precise. Generated (this file).
    docs/specs/ how it works. Design. Hand-written.

So this file deliberately carries no explanation of the project — it links to
STATUS.md for that and spends its space on state.
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
GH = "https://github.com/ed-insights-ai/ed-insights-platform/issues"

SEASON_START = date(2026, 8, 27)

# The three phases from STATUS.md. Epics are grouped under these rather than
# listed flat, because "13 epics" tells you nothing about what to do next and
# "you cannot start phase 2 until phase 1 is trustworthy" tells you everything.
PHASES = [
    (
        "Trust the instruments",
        "Every acceptance number in this plan is a reading off these checks. "
        "A check that is wrong, or that says *ok* when it could not run, makes the "
        "rest of the plan unfalsifiable — so this comes first.",
        ["The measuring instrument — fix the harness before it grades the repair"],
    ),
    (
        "Repair the data",
        "The scores are right; almost everything labelling them is wrong. Nearly "
        "every fix here is a parser or loader change — the database is derived from "
        "1.1 GB of cached pages, so we fix the code and re-read, rather than patching rows.",
        [
            "S0 — Pipeline hardening",
            "S0.5 — Repair the existing data",
            "API correctness",
        ],
    ),
    (
        "Build Touchline",
        "The rib itself: an immutable observation per refresh, boards that are pure "
        "functions of it, scheduled freshness, and a season you can ask questions about.",
        [
            "S1 — The canon and the first Observation",
            "S2 — Feed Health, the first board",
            "S3 — The Table and The Slate",
            "S4 — The refresh DAG and the wall clock",
            "S5 — Tools and chat ◆ v1",
            "S6 — The Match Page and the Dispatch",
            "S7 — The Race",
            "S8 — Form, the clock, per-team panels, game_id fix",
            "S9 — Post-season and deferred correctness",
        ],
    ),
]

# Short labels so tables stay narrow.
SHORT = {
    "The measuring instrument — fix the harness before it grades the repair": "Instrument",
    "S0 — Pipeline hardening": "S0",
    "S0.5 — Repair the existing data": "S0.5",
    "API correctness": "API",
    "S1 — The canon and the first Observation": "S1",
    "S2 — Feed Health, the first board": "S2",
    "S3 — The Table and The Slate": "S3",
    "S4 — The refresh DAG and the wall clock": "S4",
    "S5 — Tools and chat ◆ v1": "S5",
    "S6 — The Match Page and the Dispatch": "S6",
    "S7 — The Race": "S7",
    "S8 — Form, the clock, per-team panels, game_id fix": "S8",
    "S9 — Post-season and deferred correctness": "S9",
}

MARK = {"open": " ", "in_progress": "~", "closed": "x", "blocked": " ", "deferred": "-"}


def load() -> list[dict]:
    # --all, not the default: `bd list` hides closed issues, and a roadmap that
    # cannot show what is finished reports 0/63 forever.
    raw = subprocess.run(
        ["bd", "list", "--all", "--json"], cwd=REPO, capture_output=True, text=True, check=True
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


def gh_link(t: dict) -> str:
    ref = t.get("external_ref") or ""
    if not ref.startswith("gh-"):
        return ""
    n = ref.split("-", 1)[1]
    return f" ([#{n}]({GH}/{n}))"


def main() -> int:
    issues = load()
    by_id = {i["id"]: i for i in issues}

    epics = [i for i in issues if i["issue_type"] == "epic"]
    tasks = [i for i in issues if i["issue_type"] != "epic"]
    by_epic: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        by_epic[t.get("parent") or ""].append(t)

    def unmet(t: dict) -> list[str]:
        return [b for b in blockers(t) if by_id.get(b, {}).get("status") != "closed"]

    def ready(t: dict) -> bool:
        return t["status"] == "open" and not unmet(t)

    open_tasks = [t for t in tasks if t["status"] != "closed"]
    ready_now = sorted((t for t in open_tasks if ready(t)), key=lambda t: (t["priority"], t["id"]))
    active = sorted((t for t in tasks if t["status"] == "in_progress"), key=lambda t: t["priority"])
    closed = [t for t in tasks if t["status"] == "closed"]

    epic_by_title = {e["title"]: e for e in epics}

    L: list[str] = []
    add = L.append

    days = (SEASON_START - date.today()).days
    add("# Touchline — Roadmap")
    add("")
    add(
        f"*Generated from beads on {date.today().isoformat()} by `scripts/roadmap.py`. "
        "Do not edit this file — edit issues with `bd` and regenerate.*"
    )
    add("")
    add(
        "**[STATUS.md](STATUS.md) is the plain-language version — read that first if you "
        "have been away.** This page is the state of the work: what is done, what is "
        "actionable, and what is waiting on what."
    )
    add("")

    when = f"**{days} days** to the season" if days > 0 else "**the season has started**"
    add(
        f"{len(closed)}/{len(tasks)} tasks complete · **{len(ready_now)} actionable now** · "
        f"{len(open_tasks) - len(ready_now) - len(active)} blocked · "
        f"{len(active)} in progress · {when} ({SEASON_START.isoformat()})"
    )
    add("")

    if active:
        add("## In progress")
        add("")
        for t in active:
            e = by_id.get(t.get("parent") or "", {})
            add(f"- `{t['id']}` **{SHORT.get(e.get('title',''), '—')}** · {t['title']}{gh_link(t)}")
        add("")

    add("## Pick up next")
    add("")
    if ready_now:
        add("Nothing blocks these. Highest priority first.")
        add("")
        add("| | Issue | Task | Phase |")
        add("|---|---|---|---|")
        for t in ready_now[:14]:
            e = by_id.get(t.get("parent") or "", {})
            add(
                f"| P{t['priority']} | `{t['id']}` | {t['title']}{gh_link(t)} "
                f"| {SHORT.get(e.get('title',''), '—')} |"
            )
        if len(ready_now) > 14:
            add(f"| | | *…and {len(ready_now) - 14} more* | |")
    else:
        add("*Nothing is actionable — everything open is waiting on a blocker.*")
    add("")
    add("```bash")
    add("bd ready --exclude-type=epic   # the live version of this table")
    add("bd show <id>                   # mechanism, evidence, acceptance criteria")
    add("bd update <id> --claim         # take it")
    add("```")
    add("")

    # ---- phases ----------------------------------------------------------
    for n, (name, why, titles) in enumerate(PHASES, start=1):
        present = [epic_by_title[t] for t in titles if t in epic_by_title]
        if not present:
            continue
        ptasks = [t for e in present for t in by_epic.get(e["id"], [])]
        pdone = sum(1 for t in ptasks if t["status"] == "closed")
        bar = "▰" * round(10 * pdone / len(ptasks)) + "▱" * (10 - round(10 * pdone / len(ptasks))) if ptasks else ""

        add(f"## Phase {n} — {name}")
        add("")
        add(f"`{bar}` **{pdone}/{len(ptasks)}**")
        add("")
        add(why)
        add("")

        for e in present:
            kids = sorted(by_epic.get(e["id"], []), key=lambda t: (t["priority"], t["id"]))
            kdone = sum(1 for t in kids if t["status"] == "closed")
            add(f"### {e['title']}")
            add("")
            add(f"`{e['id']}` · {kdone}/{len(kids)} complete")
            add("")
            lead = (e.get("description") or "").split("\n\n")[0].strip()
            if lead:
                add(lead)
                add("")
            if not kids:
                add("*No tasks.*")
                add("")
                continue
            for t in kids:
                bits = [f"- [{MARK.get(t['status'], ' ')}] `{t['id']}` **P{t['priority']}** {t['title']}"]
                bits.append(gh_link(t))
                u = unmet(t)
                if u:
                    bits.append(" — *blocked by " + ", ".join(f"`{b}`" for b in u) + "*")
                elif t["status"] == "in_progress":
                    bits.append(" — *in progress*")
                add("".join(bits))
            add("")

    # ---- what's been decided --------------------------------------------
    if closed:
        add("## Closed")
        add("")
        add(
            "Kept rather than deleted — a task closed with its reasoning is a decision "
            "record, and reads the same in six months."
        )
        add("")
        for t in sorted(closed, key=lambda t: t["id"]):
            e = by_id.get(t.get("parent") or "", {})
            add(f"- [x] `{t['id']}` {t['title']} · *{SHORT.get(e.get('title',''), '—')}*")
        add("")

    add("---")
    add("")
    add(
        "Issues live in [beads](https://github.com/gastownhall/beads) under `.beads/` — "
        "dependency-aware, so `bd ready` only shows work whose prerequisites are actually "
        "done. That matters here: the repair has a strict order, and doing it out of order "
        "produces plausible-looking wrong answers. `.beads/issues.jsonl` is the committed "
        "export; the database itself is gitignored."
    )
    add("")
    add(
        "The GitHub issue tracker is retired — all 13 issues were closed on 2026-08-08, each "
        "pointing at its bead. The `#N` links above go to those closed issues, which still "
        "hold the original mechanism write-ups and are worth reading. File new work in beads."
    )
    add("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT.relative_to(REPO)} — {len(tasks)} tasks, {len(epics)} epics, "
        f"{len(ready_now)} ready, {len(active)} in progress, {len(closed)} closed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

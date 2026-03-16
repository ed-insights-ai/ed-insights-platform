"""Unified CLI entry point: scrape → load → backfill → audit.

Usage:
    uv run pipeline-run --all-enabled
    uv run pipeline-run --school HU
    uv run pipeline-run --all-enabled --skip-scrape   # load + audit only
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for ``uv run pipeline-run``."""
    parser = argparse.ArgumentParser(
        description="Run the full pipeline: scrape → load → backfill → audit",
    )
    parser.add_argument(
        "--all-enabled",
        action="store_true",
        help="Scrape all enabled schools from schools.toml",
    )
    parser.add_argument(
        "--school",
        type=str,
        default=None,
        help="Single school abbreviation (e.g. HU)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Single season year",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping, only load existing parquets",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip database loading",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass HTML cache during scraping",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/schools.toml",
        help="Path to schools.toml",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if not args.all_enabled and not args.school:
        parser.error("Specify --all-enabled or --school ABBREV")

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # --- Step 1: Scrape ---
    if not args.skip_scrape:
        console.rule("[bold blue]Step 1: Scrape")
        scrape_argv = ["scrape", "--config", args.config]
        if args.school:
            scrape_argv.extend(["--school", args.school])
        if args.year:
            scrape_argv.extend(["--year", str(args.year)])
        if args.no_cache:
            scrape_argv.append("--no-cache")
        if args.verbose:
            scrape_argv.append("-v")

        old_argv = sys.argv
        sys.argv = scrape_argv
        try:
            from scripts.scrape import main as scrape_main
            scrape_main()
        finally:
            sys.argv = old_argv
        console.print("[bold green]Scrape complete.\n")
    else:
        console.print("[yellow]Skipping scrape (--skip-scrape).\n")

    # --- Step 2: Load into database ---
    if not args.skip_load:
        console.rule("[bold blue]Step 2: Load into database")
        load_argv = ["load-db"]
        if args.school:
            load_argv.extend(["--school", args.school])
        if args.database_url:
            load_argv.extend(["--database-url", args.database_url])

        old_argv = sys.argv
        sys.argv = load_argv
        try:
            from scripts.load_db import main as load_main
            load_main()
        finally:
            sys.argv = old_argv
        console.print("[bold green]Load complete.\n")
    else:
        console.print("[yellow]Skipping database load (--skip-load).\n")

    # --- Step 3: Export parquets ---
    console.rule("[bold blue]Step 3: Export parquet files")
    old_argv = sys.argv
    sys.argv = ["export", "--output", "data"]
    try:
        from scripts.export import main as export_main
        export_main()
    except SystemExit as e:
        if e.code:
            console.print("[yellow]Export skipped (no merged data yet).")
    finally:
        sys.argv = old_argv

    # --- Step 4: Audit ---
    if not args.skip_load:
        console.rule("[bold blue]Step 4: Completeness audit")
        audit_argv = ["audit"]
        if args.database_url:
            audit_argv.extend(["--database-url", args.database_url])

        old_argv = sys.argv
        sys.argv = audit_argv
        try:
            from scripts.audit import main as audit_main
            audit_main()
        finally:
            sys.argv = old_argv


if __name__ == "__main__":
    main()

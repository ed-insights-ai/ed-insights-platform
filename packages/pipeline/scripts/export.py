"""CLI entry point: export merged parquet files to a flat output directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from rich.console import Console

console = Console()

STRUCTURED_DIR = Path("data/structured/all")
DEFAULT_OUTPUT = Path("data")

EXPECTED_FILES = [
    "games.parquet",
    "player_stats.parquet",
    "team_stats.parquet",
    "events.parquet",
]


def export(output: Path) -> list[Path]:
    """Copy merged parquet files from data/structured/all/ to *output*.

    Returns list of exported file paths.
    """
    output.mkdir(parents=True, exist_ok=True)
    exported: list[Path] = []

    for name in EXPECTED_FILES:
        src = STRUCTURED_DIR / name
        if not src.exists():
            console.print(f"  [yellow]Missing: {src}")
            continue
        dest = output / name
        shutil.copy2(src, dest)
        size_mb = dest.stat().st_size / (1024 * 1024)
        console.print(f"  [green]{dest}  ({size_mb:.2f} MB)")
        exported.append(dest)

    return exported


def main() -> None:
    """Entry point for ``uv run export``."""
    parser = argparse.ArgumentParser(description="Export merged parquet files")
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Output directory (default: data/)",
    )
    args = parser.parse_args()

    output = Path(args.output)

    if not STRUCTURED_DIR.exists():
        console.print(
            "[red]No merged data found at data/structured/all/. "
            "Run 'uv run scrape' first."
        )
        raise SystemExit(1)

    console.print("[bold blue]Exporting parquet files...")
    exported = export(output)

    if not exported:
        console.print("[red]No files exported.")
        raise SystemExit(1)

    console.print(f"\n[bold green]Exported {len(exported)} files to {output}/")


if __name__ == "__main__":
    main()

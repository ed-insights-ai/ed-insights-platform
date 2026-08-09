"""Rebuild parquet outputs from the committed HTML archive without network access."""

from __future__ import annotations

import argparse
import csv
import logging
import re
import shutil
from collections import defaultdict
from contextlib import chdir
from pathlib import Path

from src.config import DEFAULT_CONFIG, SchoolConfig, load_schools
from src.parser import parse_game
from src.sidearm_parser import parse_sidearm_game
from src.storage import merge_all_schools, merge_all_seasons, save_season

logger = logging.getLogger(__name__)

PIPELINE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_HTML = PIPELINE_ROOT / "data" / "raw_html"
DEFAULT_SOURCE_URLS = PIPELINE_ROOT / "data" / "source_urls.csv"
GAME_FILE_PATTERN = re.compile(r"game_(\d+)\.html")


def _parse_archive_path(path: Path, raw_html_dir: Path) -> tuple[str, int, int]:
    """Return the school abbreviation, season, and game number encoded by a cache path."""
    try:
        school_abbrev, year_text, filename = path.relative_to(raw_html_dir).parts
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid raw HTML path: {path}") from exc

    match = GAME_FILE_PATTERN.fullmatch(filename)
    if not year_text.isdigit() or match is None:
        raise ValueError(f"Invalid raw HTML path: {path}")

    game_num = int(match.group(1))
    if not 1 <= game_num <= 99:
        raise ValueError(f"Game number must be between 1 and 99: {path}")

    return school_abbrev, int(year_text), game_num


def _build_game_id(school: SchoolConfig, year: int, game_num: int) -> int:
    """Build the same stable game identifier used by the online scraper."""
    return school.ordinal * 1_000_000 + year * 100 + game_num


def _load_source_urls(path: Path) -> dict[int, str]:
    """Load the exact URL manifest, rejecting incomplete or ambiguous mappings."""
    source_urls: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8") as manifest:
        reader = csv.DictReader(manifest)
        if reader.fieldnames != ["game_id", "source_url"]:
            raise ValueError(
                f"{path} must have exactly the columns game_id,source_url"
            )

        for line_number, row in enumerate(reader, start=2):
            try:
                game_id = int(row["game_id"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid game_id at {path}:{line_number}"
                ) from exc

            source_url = row["source_url"]
            if not source_url or not source_url.strip():
                raise ValueError(f"Blank source_url at {path}:{line_number}")
            if game_id in source_urls:
                raise ValueError(f"Duplicate game_id {game_id} at {path}:{line_number}")
            source_urls[game_id] = source_url

    if not source_urls:
        raise ValueError(f"No source URLs found in {path}")
    return source_urls


def _parse_cached_game(
    html: str,
    school: SchoolConfig,
    year: int,
    game_id: int,
    source_url: str,
) -> dict:
    """Route one cached page through its configured parser."""
    if school.scraper == "sidearm":
        return parse_sidearm_game(
            html,
            game_id,
            source_url,
            year,
            school_abbrev=school.abbreviation,
            school_name=school.name,
        )
    if school.scraper == "statcrew":
        return parse_game(
            html,
            game_id,
            source_url,
            year,
            school_name=school.name,
        )
    raise ValueError(
        f"Unsupported scraper {school.scraper!r} for {school.abbreviation}"
    )


def reparse_archive(
    *,
    raw_html_dir: str | Path = DEFAULT_RAW_HTML,
    source_urls_path: str | Path = DEFAULT_SOURCE_URLS,
    config_path: str | Path = DEFAULT_CONFIG,
    output_root: str | Path = PIPELINE_ROOT,
) -> int:
    """Parse the complete HTML archive and replace the derived parquet tree."""
    raw_html_dir = Path(raw_html_dir).resolve()
    source_urls_path = Path(source_urls_path).resolve()
    config_path = Path(config_path).resolve()
    output_root = Path(output_root).resolve()

    schools = {
        school.abbreviation.casefold(): school for school in load_schools(config_path)
    }
    source_urls = _load_source_urls(source_urls_path)
    archive_paths = sorted(raw_html_dir.glob("*/*/game_*.html"))
    if not archive_paths:
        raise FileNotFoundError(f"No cached games found under {raw_html_dir}")

    parsed_by_season: dict[tuple[str, int], list[dict]] = defaultdict(list)
    encountered_game_ids: set[int] = set()

    for path in archive_paths:
        school_abbrev, year, game_num = _parse_archive_path(path, raw_html_dir)
        school = schools.get(school_abbrev.casefold())
        if school is None:
            raise ValueError(f"No school configuration found for {school_abbrev}")

        game_id = _build_game_id(school, year, game_num)
        source_url = source_urls.get(game_id)
        if source_url is None:
            raise ValueError(f"No source_url mapping for game_id {game_id} ({path})")
        if game_id in encountered_game_ids:
            raise ValueError(f"Duplicate archived game_id {game_id} ({path})")

        html = path.read_text(encoding="utf-8")
        try:
            parsed = _parse_cached_game(
                html,
                school,
                year,
                game_id,
                source_url,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to parse game_id {game_id} from {path}: {exc}"
            ) from exc

        encountered_game_ids.add(game_id)
        parsed_by_season[(school.abbreviation, year)].append(parsed)

    unused_game_ids = set(source_urls) - encountered_game_ids
    if unused_game_ids:
        sample = ", ".join(str(game_id) for game_id in sorted(unused_game_ids)[:5])
        raise ValueError(
            f"Source URL manifest contains {len(unused_game_ids)} games absent from "
            f"the archive (first: {sample})"
        )

    output_root.mkdir(parents=True, exist_ok=True)
    structured_dir = output_root / "data" / "structured"
    if structured_dir.exists():
        shutil.rmtree(structured_dir)

    with chdir(output_root):
        school_abbreviations: set[str] = set()
        for (school_abbrev, year), parsed_games in sorted(parsed_by_season.items()):
            save_season(parsed_games, year, school_abbrev=school_abbrev)
            school_abbreviations.add(school_abbrev)
        for school_abbrev in sorted(school_abbreviations):
            merge_all_seasons(school_abbrev=school_abbrev)
        merge_all_schools(config=config_path)

    logger.info(
        "Reparsed %d cached games into %s",
        len(encountered_game_ids),
        structured_dir,
    )
    return len(encountered_game_ids)


def main() -> None:
    """Run the offline archive reparse."""
    parser = argparse.ArgumentParser(
        description="Rebuild parquet data from the committed HTML archive (offline)"
    )
    parser.add_argument(
        "--raw-html-dir",
        type=Path,
        default=DEFAULT_RAW_HTML,
        help="Cached HTML root (default: data/raw_html)",
    )
    parser.add_argument(
        "--source-urls",
        type=Path,
        default=DEFAULT_SOURCE_URLS,
        help="Exact game source URL manifest (default: data/source_urls.csv)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="School configuration (default: config/schools.toml)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PIPELINE_ROOT,
        help="Root under which data/structured is rebuilt",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    count = reparse_archive(
        raw_html_dir=args.raw_html_dir,
        source_urls_path=args.source_urls,
        config_path=args.config,
        output_root=args.output_root,
    )
    print(f"Reparsed {count} cached games into {args.output_root / 'data/structured'}")


if __name__ == "__main__":
    main()

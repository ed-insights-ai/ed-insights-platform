"""CLI entry point: discover → fetch → parse → save for config-driven soccer scraping."""

from __future__ import annotations

import argparse
import logging

from rich.console import Console
from rich.progress import Progress

from src.config import SchoolConfig, load_schools
from src.discovery import discover_season_games
from src.fetcher import GameFetcher
from src.parser import log_parse_error, parse_game
from src.storage import merge_all_schools, merge_all_seasons, save_season

console = Console()
logger = logging.getLogger(__name__)


def _scrape_season(
    year: int,
    school: SchoolConfig,
    fetcher: GameFetcher,
    *,
    use_cache: bool = True,
    progress: Progress,
) -> list[dict]:
    """Scrape a single season for a school, returning a list of parsed-game dicts."""
    urls = discover_season_games(year, base_url_template=school.base_url, prefix=school.prefix)
    task = progress.add_task(f"[cyan]{school.abbreviation} {year}", total=len(urls))
    parsed: list[dict] = []

    for gu in urls:
        game_id = int(f"{year}{gu.game_num:02d}")
        html: str | None = None
        try:
            html = fetcher.fetch(gu.url, year, gu.game_num, use_cache=use_cache)
            result = parse_game(html, game_id, gu.url, year)
            parsed.append(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error parsing game %s: %s", game_id, exc)
            log_parse_error(game_id, year, exc, html)
        progress.advance(task)

    return parsed


def main() -> None:
    """Entry point for ``uv run scrape``."""
    parser = argparse.ArgumentParser(description="Scrape men's soccer stats")
    parser.add_argument("--year", type=int, default=None, help="Single season year (default: all)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass HTML cache")
    parser.add_argument("--school", type=str, default=None, help="School abbreviation (e.g. HU)")
    parser.add_argument(
        "--config", type=str, default="config/schools.toml", help="Path to schools.toml"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    schools = load_schools(args.config)
    enabled = [s for s in schools if s.enabled]

    if args.school:
        enabled = [s for s in enabled if s.abbreviation.upper() == args.school.upper()]
        if not enabled:
            console.print(f"[red]No enabled school found with abbreviation '{args.school}'")
            return

    fetcher = GameFetcher()

    with Progress(console=console) as progress:
        for school in enabled:
            years = [args.year] if args.year else school.years
            console.rule(f"[bold blue]{school.name}")
            for year in years:
                parsed = _scrape_season(
                    year, school, fetcher, use_cache=not args.no_cache, progress=progress
                )
                if parsed:
                    save_season(parsed, year, school_abbrev=school.abbreviation)
                    console.print(f"  [green]Saved {len(parsed)} games for {year}")
                else:
                    console.print(f"  [yellow]No games found for {year}")

            if len(years) > 1:
                merge_all_seasons(years, school_abbrev=school.abbreviation)
                console.print(f"[bold green]Merged {school.name} seasons.")

    # Final cross-school merge
    if len(enabled) > 1:
        merge_all_schools()
        console.print("[bold green]Merged all schools into data/structured/all/")


if __name__ == "__main__":
    main()

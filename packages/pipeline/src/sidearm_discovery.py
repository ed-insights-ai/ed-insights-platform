"""SideArm Sports season discovery — scrape schedule page for boxscore URLs."""

from __future__ import annotations

import logging
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.models import GameURL

logger = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Educational/Research Scraper)"})
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def discover_sidearm_season(year: int, base_url: str) -> list[GameURL]:
    """Fetch the SideArm schedule page and extract all boxscore URLs.

    Parameters
    ----------
    year : int
        Season year.
    base_url : str
        Sport base URL, e.g. ``https://obutigers.com/sports/mens-soccer``.

    Returns
    -------
    list[GameURL]
        One entry per discovered boxscore, numbered sequentially starting at 1.
    """
    schedule_url = f"{base_url}/schedule/{year}"
    session = _build_session()

    try:
        resp = session.get(schedule_url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch schedule %s: %s", schedule_url, exc)
        return []

    html = resp.text

    # Extract sport path from base_url for the regex pattern
    # e.g. "https://obutigers.com/sports/mens-soccer" -> "mens-soccer"
    sport_slug = base_url.rstrip("/").rsplit("/", 1)[-1]
    pattern = rf"/sports/{re.escape(sport_slug)}/stats/(\d+)/[^/]+/boxscore/\d+"
    matches = list(re.finditer(pattern, html))
    if not matches:
        logger.info("[%d] No boxscore links present for that year", year)
        return []

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_paths: list[str] = []
    rejected = 0
    observed_years: set[int] = set()
    for match in matches:
        path = match.group(0)
        found_year = int(match.group(1))
        if found_year != year:
            rejected += 1
            observed_years.add(found_year)
            continue
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)

    total = len(matches)
    if rejected == total:
        if len(observed_years) == 1:
            served_year = next(iter(observed_years))
            logger.error(
                "[%d] Rejected %d of %d boxscore URLs — schedule page served season %d. "
                "Not ingesting.",
                year,
                rejected,
                total,
                served_year,
            )
        else:
            served_years = ", ".join(str(value) for value in sorted(observed_years))
            logger.error(
                "[%d] Rejected %d of %d boxscore URLs — schedule page served seasons %s. "
                "Not ingesting.",
                year,
                rejected,
                total,
                served_years,
            )
        return []
    if rejected:
        logger.warning(
            "[%d] Rejected %d of %d boxscore URLs with a different season",
            year,
            rejected,
            total,
        )

    # Build the host from base_url
    # e.g. "https://obutigers.com/sports/mens-soccer" -> "https://obutigers.com"
    host = base_url.split("/sports/")[0]

    games: list[GameURL] = []
    for i, path in enumerate(unique_paths, start=1):
        url = f"{host}{path}"
        games.append(GameURL(year=year, game_num=i, url=url))
        logger.info("[%d] game %02d: %s", year, i, url)

    logger.info("[%d] Found %d boxscore URLs on SideArm schedule", year, len(games))
    return games

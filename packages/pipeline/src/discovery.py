"""Season URL discovery — probe school sports sites for valid game pages."""

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.models import GameURL

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = (
    "https://static.hardingsports.com/custompages/msoc/{year}/{prefix}-{num:02d}.htm"
)
_DEFAULT_PREFIX = "hu"


def _build_url(
    year: int,
    game_num: int,
    base_url_template: str = _DEFAULT_BASE_URL,
    prefix: str = _DEFAULT_PREFIX,
) -> str:
    return base_url_template.format(year=year, prefix=prefix, num=game_num)


def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Educational/Research Scraper)"})
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def discover_season_games(
    year: int,
    max_probe: int = 50,
    base_url_template: str = _DEFAULT_BASE_URL,
    prefix: str = _DEFAULT_PREFIX,
) -> list[GameURL]:
    """Probe URLs sequentially; stop when content < 1000 bytes."""
    session = _build_session()
    games: list[GameURL] = []

    for game_num in range(1, max_probe + 1):
        url = _build_url(year, game_num, base_url_template, prefix)
        try:
            resp = session.get(url, timeout=30)
            size = len(resp.content)
            if size < 1000:
                logger.info("[%d] %02d: empty (%d bytes) — stopping", year, game_num, size)
                break
            logger.info("[%d] %02d: valid (%d bytes)", year, game_num, size)
            games.append(GameURL(year=year, game_num=game_num, url=url))
        except requests.RequestException as exc:
            logger.warning("[%d] %02d: network error (%s) — stopping", year, game_num, exc)
            break

    return games

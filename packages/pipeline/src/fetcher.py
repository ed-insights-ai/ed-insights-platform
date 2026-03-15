"""GameFetcher — HTTP fetch with disk cache and polite delays."""

import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class GameFetcher:
    """Fetch and cache game HTML pages."""

    def __init__(self, cache_dir: str = "data/raw_html") -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Educational/Research Scraper)"})
        self.cache_dir = Path(cache_dir)

    def __enter__(self) -> "GameFetcher":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def fetch(self, url: str, year: int, game_num: int, *, use_cache: bool = True) -> str:
        """Fetch HTML with optional disk caching and polite delay."""
        year_dir = self.cache_dir / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        cache_path = year_dir / f"game_{game_num:02d}.html"

        if use_cache and cache_path.exists():
            return cache_path.read_text(encoding="utf-8")

        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        html = resp.text

        cache_path.write_text(html, encoding="utf-8")
        time.sleep(0.5)  # polite delay
        return html

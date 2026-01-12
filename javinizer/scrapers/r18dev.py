"""R18Dev JSON API scraper for metadata"""

import re
from datetime import datetime
from typing import Optional
from functools import lru_cache

import httpx

from javinizer.models import Actress, MovieMetadata, ProxyConfig, Rating
from javinizer.scrapers.base import BaseScraper
from javinizer.scrapers.utils import normalize_id_variants
from javinizer.logger import get_logger

logger = get_logger(__name__)


class R18DevScraper(BaseScraper):
    """
    Scraper for R18.dev API

    R18.dev provides a JSON API which is much cleaner to parse than HTML.
    This is the preferred source for English metadata.
    """

    name = "r18dev"
    base_url = "https://r18.dev"
    api_url = "https://r18.dev/videos/vod/movies/detail/-/combined="

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        cookies: Optional[dict[str, str]] = None,
        user_agent: Optional[str] = None,
    ):
        super().__init__(
            timeout=timeout,
            proxy=proxy,
            cookies=cookies,
            user_agent=user_agent,
        )

    @property
    def client(self) -> httpx.Client:
        """Override client to use minimal headers - R18.dev API blocks certain headers"""
        if self._client is None:
            proxy_url = self._get_proxy_url()

            # R18.dev API requires minimal headers - blocks requests with Accept/Accept-Language
            client_kwargs = {
                "timeout": self.timeout,
                "follow_redirects": True,
            }

            if proxy_url:
                client_kwargs["proxy"] = proxy_url

            self._client = httpx.Client(**client_kwargs)

        return self._client

    @staticmethod
    def get_id_variants(movie_id: str) -> list[str]:
        """Generate possible content ID formats for a movie ID"""
        return normalize_id_variants(movie_id)

    @staticmethod
    def normalize_id(movie_id: str) -> str:
        """Normalize movie ID to primary content ID format (backward compatible)"""
        return normalize_id_variants(movie_id)[0]

    def get_search_url(self, movie_id: str) -> str:
        """Build API URL for movie ID"""
        content_id = self.normalize_id(movie_id)
        return f"{self.api_url}{content_id}/json"

    def get_movie_url(self, movie_id: str) -> Optional[str]:
        """
        Try multiple content ID formats to find the movie

        Returns the first URL that returns valid data
        """
        variants = normalize_id_variants(movie_id)

        for content_id in variants:
            url = f"{self.api_url}{content_id}/json"
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # Handle dict response
                    if isinstance(data, dict) and data.get("dvd_id"):
                        return url
                    # Handle list response (some endpoints return list of results)
                    elif isinstance(data, list) and len(data) > 0 and data[0].get("dvd_id"):
                        return url
            except Exception:
                continue

        return None

    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from R18.dev JSON API"""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error(f"Error fetching R18Dev API: {e}", exc_info=True)
            return None

        # Handle list response (extract first item)
        if isinstance(data, list):
            if len(data) == 0:
                return None
            data = data[0]

        # Check if we got valid data
        if not isinstance(data, dict) or not data.get("dvd_id"):
            return None

        # Parse metadata
        metadata = MovieMetadata(
            id=data.get("dvd_id", "UNKNOWN"),
            content_id=data.get("content_id"),
            title=self._get_title(data),
            original_title=data.get("title_ja"),
            description=data.get("comment_en") or data.get("comment"),
            release_date=self._parse_date(data.get("release_date")),
            runtime=data.get("runtime_mins"),
            director=self._get_director(data),
            maker=data.get("maker_name_en") or data.get("maker_name_ja"),
            label=data.get("label_name_en") or data.get("label_name_ja"),
            series=data.get("series_name_en") or data.get("series_name_ja"),
            actresses=self._parse_actresses(data),
            genres=self._parse_genres(data),
            rating=None,  # R18Dev doesn't provide ratings
            cover_url=self._get_cover_url(data),
            screenshot_urls=self._parse_screenshot_urls(data),
            trailer_url=data.get("sample_url"),
            source="r18dev",
        )

        return metadata

    def _get_title(self, data: dict) -> str:
        """Get best available title"""
        return (
            data.get("title_en") or
            data.get("title") or
            data.get("title_ja") or
            "Unknown"
        )

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse release date string"""
        if not date_str:
            return None
        try:
            # Format: "2020-09-12 00:00:00" or "2020-09-12"
            date_part = date_str.split(" ")[0]
            return datetime.strptime(date_part, "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            return None

    def _get_director(self, data: dict) -> Optional[str]:
        """Get director name"""
        directors = data.get("directors", [])
        if directors and len(directors) > 0:
            return directors[0].get("name_romaji") or directors[0].get("name_kanji")
        return None

    def _parse_actresses(self, data: dict) -> list[Actress]:
        """Parse actress information from JSON"""
        actresses = []

        for actress_data in data.get("actresses", []):
            name_romaji = actress_data.get("name_romaji", "")
            name_parts = name_romaji.split(" ") if name_romaji else []

            # Get thumb URL
            thumb_url = actress_data.get("image_url")
            if thumb_url and not thumb_url.startswith("http"):
                thumb_url = f"https://pics.dmm.co.jp/mono/actjpgs/{thumb_url}"

            actress = Actress(
                first_name=name_parts[0] if name_parts else None,
                last_name=name_parts[1] if len(name_parts) > 1 else None,
                japanese_name=actress_data.get("name_kanji", "").replace("（.*）", "").replace("&amp;", "&"),
                thumb_url=thumb_url,
            )
            actresses.append(actress)

        return actresses

    def _parse_genres(self, data: dict) -> list[str]:
        """Parse genre list from categories"""
        genres = []
        for category in data.get("categories", []):
            name = category.get("name_en") or category.get("name_ja")
            if name:
                genres.append(name)
        return genres

    def _get_cover_url(self, data: dict) -> Optional[str]:
        """Get cover image URL, prioritizing high-quality awsimgsrc.dmm.co.jp domain"""
        cover = data.get("jacket_full_url")
        if cover:
            # Swap ps.jpg (poster small) with pl.jpg (poster large)
            cover = cover.replace("ps.jpg", "pl.jpg")

            # Convert to high-quality awsimgsrc.dmm.co.jp domain
            # Only for digital/video or digital/amateur paths (mono/movie/adult not compatible)
            # Pattern: https://pics.dmm.co.jp/digital/video/xxx/xxx.jpg
            # -> https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/xxx/xxx.jpg
            if "pics.dmm.co.jp" in cover and "/digital/" in cover:
                cover = cover.replace("pics.dmm.co.jp", "awsimgsrc.dmm.co.jp/pics_dig")

            return cover
        return None

    def _parse_screenshot_urls(self, data: dict) -> list[str]:
        """Parse screenshot URLs from gallery"""
        gallery = data.get("gallery")
        if not gallery:
            return []

        # gallery can be a dict with image_full/image_thumb, or a list of URLs
        if isinstance(gallery, list):
            # Gallery is a list of URLs
            images = gallery
        elif isinstance(gallery, dict):
            # Prefer full images, fallback to thumbnails
            images = gallery.get("image_full") or gallery.get("image_thumb") or []
        else:
            return []

        # Convert to full size URLs
        return [
            url.replace("-", "jp-") if isinstance(url, str) and (not url.startswith("http") or "jp-" not in url) else url
            for url in images
            if isinstance(url, str)
        ]


# Example usage
if __name__ == "__main__":
    with R18DevScraper() as scraper:
        metadata = scraper.find("IPX-486")
        if metadata:
            print(f"Title: {metadata.title}")
            print(f"ID: {metadata.id}")
            print(f"Maker: {metadata.maker}")
            print(f"Actresses: {[a.japanese_name or a.full_name for a in metadata.actresses]}")
        else:
            print("No results found")

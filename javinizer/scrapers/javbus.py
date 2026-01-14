"""JavBus HTML scraper for metadata

JavBus provides movie metadata in multiple languages (EN, JP, CN).
This scraper parses HTML content since no official API is available.
"""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from javinizer.models import Actress, MovieMetadata, ProxyConfig
from javinizer.scrapers.base import BaseScraper
from javinizer.logger import get_logger

logger = get_logger(__name__)


class JavBusScraper(BaseScraper):
    """
    Scraper for JavBus

    JavBus is a popular JAV database with EN/JP/CN support.
    This scraper parses HTML pages to extract metadata.
    
    Note: JavBus uses age/region verification. This scraper
    automatically sets cookies to bypass verification.
    """

    name = "javbus"
    base_url = "https://www.javbus.com"

    # Language-specific base URLs
    LANG_URLS = {
        "en": "https://www.javbus.com",
        "ja": "https://www.javbus.com/ja",
        "zh": "https://www.javbus.com/zh",
    }

    # Age verification bypass cookies
    AGE_COOKIES = {
        "existmag": "all",
        "age": "verified",
    }

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        cookies: Optional[dict[str, str]] = None,
        user_agent: Optional[str] = None,
        language: str = "en",
    ):
        # Merge age bypass cookies with any user-provided cookies
        merged_cookies = {**self.AGE_COOKIES}
        if cookies:
            merged_cookies.update(cookies)
        
        super().__init__(
            timeout=timeout,
            proxy=proxy,
            cookies=merged_cookies,
            user_agent=user_agent,
        )
        self.language = language
        self.base_url = self.LANG_URLS.get(language, self.LANG_URLS["en"])

    def get_search_url(self, movie_id: str) -> str:
        """Build search URL for movie ID"""
        # Normalize ID: remove spaces, uppercase
        normalized_id = movie_id.strip().upper().replace(" ", "-")
        return f"{self.base_url}/{normalized_id}"

    def get_movie_url(self, movie_id: str) -> Optional[str]:
        """Find the direct movie page URL from ID"""
        url = self.get_search_url(movie_id)
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                # Check if page has valid movie content
                html = response.text
                if self._is_valid_movie_page(html):
                    return url
        except Exception as e:
            logger.debug(f"[{self.name}] Error checking URL {url}: {e}")

        return None

    def _is_valid_movie_page(self, html: str) -> bool:
        """Check if HTML contains valid movie content"""
        # JavBus movie pages have specific structure
        return (
            '<div class="container"' in html and 
            '<div class="movie"' in html or
            '<span class="header">' in html
        )

    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from JavBus movie page"""
        try:
            response = self.client.get(url)
            response.raise_for_status()
            html = response.text
        except Exception as e:
            logger.error(f"[{self.name}] Error fetching page: {e}")
            return None

        return self._parse_html(html, url)

    def _parse_html(self, html: str, url: str) -> Optional[MovieMetadata]:
        """Parse HTML to extract movie metadata"""
        try:
            # Extract movie ID from page
            movie_id = self._extract_id(html)
            if not movie_id:
                logger.debug(f"[{self.name}] Could not extract movie ID from {url}")
                return None

            metadata = MovieMetadata(
                id=movie_id,
                title=self._extract_title(html),
                original_title=self._extract_original_title(html),
                description=None,  # JavBus doesn't provide descriptions
                release_date=self._extract_date(html),
                runtime=self._extract_runtime(html),
                director=self._extract_director(html),
                maker=self._extract_maker(html),
                label=self._extract_label(html),
                series=self._extract_series(html),
                actresses=self._extract_actresses(html),
                genres=self._extract_genres(html),
                rating=None,
                cover_url=self._extract_cover(html),
                screenshot_urls=self._extract_screenshots(html),
                trailer_url=None,
                source=self.name,
            )

            return metadata

        except Exception as e:
            logger.error(f"[{self.name}] Error parsing HTML: {e}", exc_info=True)
            return None

    def _extract_id(self, html: str) -> Optional[str]:
        """Extract movie ID from HTML"""
        # Pattern: <span style="color:#CC0000;">ABC-123</span>
        match = re.search(
            r'<span style="color:#CC0000;">([A-Z0-9]+-[A-Z0-9]+)</span>',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).upper()

        # Alternative: look in URL-like patterns
        match = re.search(r'/([A-Z]{2,6}-\d{3,5})(?:\?|$|")', html, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return None

    def _extract_title(self, html: str) -> str:
        """Extract movie title"""
        # Pattern: <h3>Title Text</h3>
        match = re.search(r'<h3[^>]*>([^<]+)</h3>', html)
        if match:
            title = match.group(1).strip()
            # Remove ID prefix if present
            title = re.sub(r'^[A-Z0-9]+-[A-Z0-9]+\s*', '', title)
            return title if title else "Unknown"
        return "Unknown"

    def _extract_original_title(self, html: str) -> Optional[str]:
        """Extract original Japanese title"""
        # On Japanese version, title is already in Japanese
        if self.language == "ja":
            return self._extract_title(html)
        return None

    def _extract_date(self, html: str) -> Optional[datetime]:
        """Extract release date"""
        # Pattern: >發行日期:</span> 2024-01-15
        match = re.search(
            r'>(?:發行日期|Release Date|发行日期):</span>\s*(\d{4}-\d{2}-\d{2})',
            html,
        )
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y-%m-%d").date()
            except ValueError:
                pass
        return None

    def _extract_runtime(self, html: str) -> Optional[int]:
        """Extract runtime in minutes"""
        # Pattern: >長度:</span> 120分鐘
        match = re.search(
            r'>(?:長度|Length|时长):</span>\s*(\d+)\s*(?:分鐘|min|分钟)',
            html,
        )
        if match:
            return int(match.group(1))
        return None

    def _extract_director(self, html: str) -> Optional[str]:
        """Extract director name"""
        match = re.search(
            r'>(?:導演|Director|导演):</span>\s*<a[^>]*>([^<]+)</a>',
            html,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_maker(self, html: str) -> Optional[str]:
        """Extract studio/maker name"""
        match = re.search(
            r'>(?:製作商|Studio|制作商):</span>\s*<a[^>]*>([^<]+)</a>',
            html,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_label(self, html: str) -> Optional[str]:
        """Extract label name"""
        match = re.search(
            r'>(?:發行商|Label|发行商):</span>\s*<a[^>]*>([^<]+)</a>',
            html,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_series(self, html: str) -> Optional[str]:
        """Extract series name"""
        match = re.search(
            r'>(?:系列|Series):</span>\s*<a[^>]*>([^<]+)</a>',
            html,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_actresses(self, html: str) -> list[Actress]:
        """Extract actress information"""
        actresses = []

        # Pattern: <a class="avatar-box" href="..."><img src="thumb.jpg"/><span>Name</span></a>
        pattern = re.compile(
            r'<a class="avatar-box"[^>]*href="[^"]*"[^>]*>'
            r'.*?<img[^>]*src="([^"]*)"[^>]*/?>.*?'
            r'<span>([^<]+)</span>.*?</a>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in pattern.finditer(html):
            thumb_url = match.group(1)
            name = match.group(2).strip()

            # Make thumb URL absolute
            if thumb_url and not thumb_url.startswith("http"):
                thumb_url = urljoin(self.base_url, thumb_url)

            # Parse name (could be Japanese or Romanized)
            name_parts = name.split(" ")

            actress = Actress(
                first_name=name_parts[0] if name_parts else None,
                last_name=name_parts[1] if len(name_parts) > 1 else None,
                japanese_name=name if self._is_japanese(name) else None,
                thumb_url=thumb_url,
            )
            actresses.append(actress)

        return actresses

    def _is_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        # Check for Hiragana, Katakana, or Kanji
        return bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]', text))

    def _extract_genres(self, html: str) -> list[str]:
        """Extract genre tags"""
        genres = []

        # Pattern: <span class="genre"><a href="...">Genre Name</a></span>
        pattern = re.compile(
            r'<span class="genre"[^>]*>\s*<a[^>]*>([^<]+)</a>\s*</span>',
            re.IGNORECASE,
        )

        for match in pattern.finditer(html):
            genre = match.group(1).strip()
            if genre and genre not in genres:
                genres.append(genre)

        return genres

    def _extract_cover(self, html: str) -> Optional[str]:
        """Extract cover image URL"""
        # Pattern: <a class="bigImage" href="cover.jpg">
        match = re.search(
            r'<a class="bigImage"[^>]*href="([^"]+)"',
            html,
        )
        if match:
            cover_url = match.group(1)
            if not cover_url.startswith("http"):
                cover_url = urljoin(self.base_url, cover_url)
            return cover_url
        return None

    def _extract_screenshots(self, html: str) -> list[str]:
        """Extract screenshot/sample image URLs"""
        screenshots = []

        # Pattern: <a class="sample-box" href="screenshot.jpg">
        pattern = re.compile(
            r'<a class="sample-box"[^>]*href="([^"]+)"',
            re.IGNORECASE,
        )

        for match in pattern.finditer(html):
            url = match.group(1)
            if not url.startswith("http"):
                url = urljoin(self.base_url, url)
            screenshots.append(url)

        return screenshots


# Example usage
if __name__ == "__main__":
    with JavBusScraper() as scraper:
        metadata = scraper.find("IPX-486")
        if metadata:
            print(f"Title: {metadata.title}")
            print(f"ID: {metadata.id}")
            print(f"Maker: {metadata.maker}")
            print(f"Actresses: {[a.japanese_name or a.full_name for a in metadata.actresses]}")
            print(f"Genres: {metadata.genres}")
        else:
            print("No results found")

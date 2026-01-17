"""Javlibrary scraper for metadata"""

import re
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import urljoin

import click
from bs4 import BeautifulSoup

from javinizer.models import Actress, MovieMetadata, ProxyConfig, Rating
from javinizer.scrapers.base import BaseScraper
from javinizer.logger import get_logger

logger = get_logger(__name__)


class JavlibraryScraper(BaseScraper):
    """
    Scraper for Javlibrary.com

    Note: Javlibrary uses Cloudflare protection. You may need to:
    1. Use a proxy from Japan IP
    2. Provide Cloudflare cookies (cf_clearance, __cf_bm)
    3. Use the correct User-Agent that matches the cookies
    """

    name = "javlibrary"
    base_url = "https://www.javlibrary.com"

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        cookies: Optional[dict[str, str]] = None,
        user_agent: Optional[str] = None,
        language: str = "en",  # en, ja, cn, tw
    ):
        super().__init__(
            timeout=timeout,
            proxy=proxy,
            cookies=cookies,
            user_agent=user_agent,
        )
        self.language = language

        # Explicitly set cookies with domain for curl_cffi
        if self.cookies and hasattr(self.client, "cookies"):
            # If using curl_cffi session, clear first to avoid duplicates (no-domain vs domain)
            self.client.cookies.clear()
            for name, value in self.cookies.items():
                self.client.cookies.set(name, value, domain=".javlibrary.com")

    def get_search_url(self, movie_id: str) -> str:
        """Build search URL for movie ID"""
        movie_id = movie_id.upper().strip()
        return f"{self.base_url}/{self.language}/vl_searchbyid.php?keyword={movie_id}"

    def _check_cloudflare(self, response: Any) -> bool:
        """Check if response is a Cloudflare challenge"""
        if response.status_code == 403:
            headers = dict(response.headers)
            if "cf-ray" in headers or "cf-cache-status" in headers:
                return True
        if response.status_code == 503:
            if "challenge" in response.text.lower() or "cf-" in response.text.lower():
                return True
        return False

    def _print_cf_help(self) -> None:
        """Print helpful message for Cloudflare issues"""
        cmd = "javinizer config get-javlibrary-cookies"
        proxy_url = self._get_proxy_url()
        if proxy_url:
            cmd += f" --proxy {proxy_url}"

        msg = (
            "Javlibrary is protected by Cloudflare.\n"
            "   Your cookies may be expired or missing.\n"
            "   Please run the following command to refresh them:\n\n"
            f"       {cmd}\n"
        )
        logger.warning(f"Javlibrary Cloudflare challenge detected. Run '{cmd}' to fix.")
        click.echo(f"\n⚠️  {msg}", err=True)

    def get_movie_url(self, movie_id: str) -> Optional[str]:
        """Find direct movie page URL by searching"""
        search_url = self.get_search_url(movie_id)

        try:
            response = self.client.get(search_url)

            # Check for Cloudflare
            # Check for Cloudflare
            if self._check_cloudflare(response):
                self._print_cf_help()
                return None

            response.raise_for_status()
        except Exception as e:
            if "403" in str(e):
                logger.warning(
                    "Javlibrary returned 403 Forbidden (Cloudflare protection likely)."
                )
            else:
                logger.error(f"Error searching Javlibrary: {e}", exc_info=True)
            return None

        # Check if we got redirected directly to movie page
        if "/?v=" in str(response.url):
            return str(response.url)

        # Parse search results
        soup = BeautifulSoup(response.content, "lxml")

        # Look for exact match in results
        # movie_id_upper = movie_id.upper().replace("-", "")

        # Use response URL as base for relative links (handles ./? correctly)
        base_for_join = str(response.url)

        for link in soup.select(".video a[href*='?v=']"):
            title = link.get("title", "")
            # Check if this result matches our ID
            if movie_id.upper() in title.upper():
                href = link.get("href")
                if href:
                    return urljoin(base_for_join, href)

        # Get first result if no exact match
        first_result = soup.select_one(".video a[href*='?v=']")
        if first_result:
            href = first_result.get("href")
            if href:
                return urljoin(base_for_join, href)

        return None

    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from Javlibrary movie page"""
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error fetching Javlibrary page: {e}", exc_info=True)
            return None

        soup = BeautifulSoup(response.content, "lxml")
        html = response.text

        # Check for Cloudflare challenge - real challenge pages are short and have specific markers
        # Normal pages may have "challenge-platform" in Cloudflare scripts but are NOT challenge pages
        is_cf_challenge = (
            len(html) < 10000  # Challenge pages are typically short
            and ("cf-browser-verification" in html or "Just a moment" in html)
        )
        if is_cf_challenge:
            self._print_cf_help()
            return None

        # Parse metadata
        metadata = MovieMetadata(
            id=self._parse_id(soup),
            title=self._parse_title(soup),
            original_title=self._parse_title(soup),  # Same for now
            release_date=self._parse_release_date(soup),
            runtime=self._parse_runtime(soup),
            director=self._parse_director(soup),
            maker=self._parse_maker(soup),
            label=self._parse_label(soup),
            actresses=self._parse_actresses(soup, url),
            genres=self._parse_genres(soup),
            rating=self._parse_rating(soup),
            cover_url=self._parse_cover_url(soup),
            screenshot_urls=self._parse_screenshot_urls(soup),
            source="javlibrary",
        )

        return metadata

    def _parse_id(self, soup: BeautifulSoup) -> str:
        """Parse movie ID"""
        id_div = soup.select_one("#video_id .text")
        if id_div:
            return id_div.get_text(strip=True)
        return "UNKNOWN"

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Parse movie title"""
        title_tag = soup.select_one("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove " - JAVLibrary" suffix and ID prefix
            title = re.sub(r"\s*-\s*JAVLibrary.*$", "", title, flags=re.IGNORECASE)
            # Remove ID prefix (first word)
            parts = title.split(" ", 1)
            if len(parts) > 1:
                return parts[1].strip()
            return title.strip()
        return "Unknown"

    def _parse_release_date(self, soup: BeautifulSoup) -> Optional[date]:
        """Parse release date"""
        date_div = soup.select_one("#video_date .text")
        if date_div:
            date_str = date_div.get_text(strip=True)
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                pass
        return None

    def _parse_runtime(self, soup: BeautifulSoup) -> Optional[int]:
        """Parse runtime in minutes"""
        length_div = soup.select_one("#video_length .text")
        if length_div:
            try:
                return int(length_div.get_text(strip=True))
            except ValueError:
                pass
        return None

    def _parse_director(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse director name"""
        director_div = soup.select_one("#video_director .text a")
        if director_div:
            return director_div.get_text(strip=True)
        return None

    def _parse_maker(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse maker/studio name"""
        maker_div = soup.select_one("#video_maker .text a")
        if maker_div:
            return maker_div.get_text(strip=True)
        return None

    def _parse_label(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse label name"""
        label_div = soup.select_one("#video_label .text a")
        if label_div:
            return label_div.get_text(strip=True)
        return None

    def _parse_actresses(self, soup: BeautifulSoup, url: str) -> list[Actress]:
        """Parse actress information"""
        actresses = []

        # Find all actress links
        for star in soup.select("#video_cast .star a"):
            name = star.get_text(strip=True)
            if not name:
                continue

            # Check if name is Japanese
            is_japanese = bool(
                re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]", name)
            )

            if is_japanese:
                actress = Actress(japanese_name=name)
            else:
                parts = name.split(" ")
                actress = Actress(
                    first_name=parts[1] if len(parts) > 1 else parts[0],
                    last_name=parts[0] if len(parts) > 1 else None,
                )

            actresses.append(actress)

        return actresses

    def _parse_genres(self, soup: BeautifulSoup) -> list[str]:
        """Parse genre list"""
        genres = []
        for genre_link in soup.select("#video_genres .genre a"):
            genre = genre_link.get_text(strip=True)
            if genre:
                genres.append(genre)
        return genres

    def _parse_rating(self, soup: BeautifulSoup) -> Optional[Rating]:
        """Parse rating"""
        rating_span = soup.select_one("#video_review .score")
        if rating_span:
            rating_text = rating_span.get_text(strip=True)
            # Remove parentheses: "(8.5)" -> "8.5"
            rating_text = rating_text.strip("()")
            try:
                rating_value = float(rating_text)
                return Rating(rating=rating_value, votes=0)
            except ValueError:
                pass
        return None

    def _parse_cover_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse cover image URL, prioritizing high-quality awsimgsrc.dmm.co.jp domain"""
        cover_img = soup.select_one("#video_jacket_img")
        if cover_img:
            src = cover_img.get("src")
            if src:
                if src.startswith("//"):
                    src = f"https:{src}"

                # Convert small image to large
                src = src.replace("ps.jpg", "pl.jpg")

                # Convert to high-quality awsimgsrc.dmm.co.jp domain
                # Only for digital/video or digital/amateur paths (mono/movie/adult not compatible)
                if "pics.dmm.co.jp" in src and "/digital/" in src:
                    src = src.replace("pics.dmm.co.jp", "awsimgsrc.dmm.co.jp/pics_dig")

                # Remove query parameters for clean URL
                if "?" in src:
                    src = src.split("?")[0]

                return src
        return None

    def _parse_screenshot_urls(self, soup: BeautifulSoup) -> list[str]:
        """Parse screenshot URLs"""
        urls = []
        for img in soup.select(".previewthumbs img"):
            src = img.get("src")
            if src and "pics.dmm" in src:
                # Convert thumbnail to full size
                full_url = src.replace("-", "jp-")
                if full_url.startswith("//"):
                    full_url = f"https:{full_url}"
                urls.append(full_url)
        return urls


# Example usage
if __name__ == "__main__":
    # Note: This may fail due to Cloudflare protection without valid cookies
    with JavlibraryScraper() as scraper:
        metadata = scraper.find("IPX-486")
        if metadata:
            print(f"Title: {metadata.title}")
            print(f"ID: {metadata.id}")
            print(f"Maker: {metadata.maker}")
        else:
            print("No results found (may need Cloudflare cookies)")

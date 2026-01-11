"""DMM/Fanza scraper for Japanese metadata"""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote
from functools import lru_cache

from bs4 import BeautifulSoup, Tag

from javinizer.models import Actress, MovieMetadata, ProxyConfig, Rating
from javinizer.scrapers.base import BaseScraper
from javinizer.logger import get_logger

logger = get_logger(__name__)


class DMMScraper(BaseScraper):
    """Scraper for DMM.co.jp (Fanza)"""

    name = "dmm"
    base_url = "https://www.dmm.co.jp"

    # Cookies for age verification
    AGE_CHECK_COOKIES = {
        "age_check_done": "1",
    }

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        cookies: Optional[dict[str, str]] = None,
        user_agent: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        # Merge age check cookies with any provided cookies
        all_cookies = {**self.AGE_CHECK_COOKIES, **(cookies or {})}
        super().__init__(
            timeout=timeout,
            proxy=proxy,
            cookies=all_cookies,
            user_agent=user_agent,
            verify_ssl=verify_ssl,
        )


    @property
    def client(self):
        """Override client to use Japanese Accept-Language for DMM"""
        client = super().client
        # DMM requires Japanese language header
        client.headers["Accept-Language"] = "ja-JP,ja;q=0.9,en;q=0.8"
        return client

    @staticmethod
    @lru_cache(maxsize=128)
    def normalize_id_variants(movie_id: str) -> list[str]:
        """
        Generate possible content ID formats for a movie ID

        Some IDs have digit prefixes: START-422 -> 1start422
        Some use padding: IPX-486 -> ipx00486

        Returns list of possible content IDs to try
        """
        movie_id = movie_id.upper().strip()

        match = re.match(r"([A-Z]+)-?(\d+)", movie_id)
        if not match:
            return [movie_id.lower()]

        prefix, number = match.groups()
        prefix_lower = prefix.lower()

        # Generate multiple possible formats
        variants = []

        # Format 1: prefix + padded number (ipx00486)
        variants.append(f"{prefix_lower}{number.zfill(5)}")

        # Format 2: digit prefix + prefix + number (1start422)
        variants.append(f"1{prefix_lower}{number}")

        # Format 3: prefix + number without padding
        variants.append(f"{prefix_lower}{number}")

        # Format 4: digit prefix + prefix + padded number
        variants.append(f"1{prefix_lower}{number.zfill(5)}")

        # Format 5: h_ prefix for amateur content
        variants.append(f"h_{prefix_lower}{number.zfill(5)}")

        return variants

    @staticmethod
    @lru_cache(maxsize=128)
    def normalize_id(movie_id: str) -> tuple[str, str]:
        """
        Convert movie ID to DMM content ID format (primary format)

        Example: IPX-486 -> ipx00486
        Returns: (normalized_id, display_id)
        """
        movie_id = movie_id.upper().strip()

        match = re.match(r"([A-Z]+)-?(\d+)", movie_id)
        if not match:
            return movie_id.lower(), movie_id

        prefix, number = match.groups()
        content_id = f"{prefix.lower()}{number.zfill(5)}"
        display_id = f"{prefix}-{number.zfill(3)}"

        return content_id, display_id

    def get_search_url(self, movie_id: str) -> str:
        """Build DMM search URL"""
        content_id, _ = self.normalize_id(movie_id)
        return f"{self.base_url}/search/?searchstr={quote(content_id)}"

    def get_movie_url(self, movie_id: str) -> Optional[str]:
        """Find direct movie page URL by trying multiple content ID formats

        Note: New video.dmm.co.jp site is a React SPA that requires JavaScript.
        We only support the old www.dmm.co.jp format. If content redirects
        to new site, return None and let R18Dev handle it.
        """
        variants = self.normalize_id_variants(movie_id)

        # Try each variant with direct URLs
        for content_id in variants:
            direct_urls = [
                f"{self.base_url}/digital/videoa/-/detail/=/cid={content_id}/",
                f"{self.base_url}/mono/dvd/-/detail/=/cid={content_id}/",
            ]

            for url in direct_urls:
                try:
                    response = self.client.get(url)
                    if response.status_code == 200:
                        final_url = str(response.url)

                        # Skip new video.dmm.co.jp site (React SPA, needs JS)
                        if "video.dmm.co.jp" in final_url:
                            continue

                        # Check if we landed on old site detail page
                        if "detail" in final_url and "www.dmm.co.jp" in final_url:
                            return final_url
                except Exception:
                    continue

        # Fallback to search on old site
        try:
            response = self.client.get(self.get_search_url(movie_id))

            # Skip if redirected to new site
            if "video.dmm.co.jp" in str(response.url):
                return None

            soup = BeautifulSoup(response.content, "lxml")

            # Find first result link
            result = soup.select_one('a[href*="/detail/"]')
            if result and isinstance(result, Tag):
                href = result.get("href")
                if href and "video.dmm.co.jp" not in str(href):
                    return str(href)
        except Exception:
            pass

        return None

    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from DMM movie page (old www.dmm.co.jp format only)"""
        # Skip new site
        if "video.dmm.co.jp" in url:
            return None

        try:
            response = self.client.get(url)
            response.raise_for_status()

            # Check if redirected to new site
            if "video.dmm.co.jp" in str(response.url):
                return None

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}", exc_info=True)
            return None

        soup = BeautifulSoup(response.content, "lxml")
        html = response.text

        # Extract content ID from URL
        content_id = self._extract_content_id(url)
        movie_id = self._content_id_to_movie_id(content_id) if content_id else "UNKNOWN"

        # Parse all fields
        metadata = MovieMetadata(
            id=movie_id,
            content_id=content_id,
            title=self._parse_title(soup) or movie_id,
            original_title=self._parse_title(soup),  # Same for Japanese source
            description=self._parse_description(html),
            release_date=self._parse_release_date(html),
            runtime=self._parse_runtime(html),
            director=self._parse_director(html),
            maker=self._parse_maker(html),
            label=self._parse_label(html),
            series=self._parse_series(html),
            actresses=self._parse_actresses(soup, html),
            genres=self._parse_genres(html),
            rating=self._parse_rating(html),
            cover_url=self._parse_cover_url(html),
            screenshot_urls=self._parse_screenshot_urls(soup),
            trailer_url=self._parse_trailer_url(html),
            source="dmm",
        )

        return metadata

    def _extract_content_id(self, url: str) -> Optional[str]:
        """Extract content ID from URL"""
        match = re.search(r"cid=([^/&]+)", url)
        return match.group(1) if match else None

    def _content_id_to_movie_id(self, content_id: str) -> str:
        """Convert DMM content ID to standard movie ID"""
        # Pattern: letters followed by digits
        match = re.match(r"(\d*)([a-z]+)(\d+)(.*)$", content_id, re.IGNORECASE)
        if not match:
            return content_id.upper()

        _, prefix, number, suffix = match.groups()
        # Remove leading zeros but keep at least 3 digits
        number = number.lstrip("0").zfill(3)
        return f"{prefix.upper()}-{number}{suffix.upper()}"

    def _parse_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Parse movie title"""
        title_elem = soup.select_one('h1#title, h1.item')
        if title_elem:
            return title_elem.get_text(strip=True)
        return None

    def _parse_description(self, html: str) -> Optional[str]:
        """Parse movie description"""
        # Try different patterns - use non-greedy matching with proper end markers
        patterns = [
            r'<p class="mg-b20">\s*(.*?)</p>',
            r'<div class="mg-b20 lh4">(.*?)</div>',
            # Common description container
            r'<div[^>]*class="[^"]*txt[^"]*"[^>]*>(.*?)</div>',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                desc = match.group(1)
                # Clean HTML tags
                desc = re.sub(r'<[^>]+>', '', desc)
                # Clean up whitespace
                desc = re.sub(r'\s+', ' ', desc)
                desc = desc.strip()
                # Only return if it looks like actual content (not JS/CSS)
                if desc and not desc.startswith('{') and 'function' not in desc.lower():
                    return desc[:2000]  # Limit to reasonable length
        return None

    def _parse_release_date(self, html: str) -> Optional[datetime]:
        """Parse release date"""
        match = re.search(r"(\d{4})/(\d{2})/(\d{2})", html)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day)).date()
            except ValueError:
                pass
        return None

    def _parse_runtime(self, html: str) -> Optional[int]:
        """Parse runtime in minutes"""
        match = re.search(r"(\d{2,3})\s*(?:minutes|分)", html)
        return int(match.group(1)) if match else None

    def _parse_director(self, html: str) -> Optional[str]:
        """Parse director name"""
        match = re.search(r'href="[^"]*\?director=\d+"[^>]*>([^<]+)</a>', html)
        return match.group(1).strip() if match else None

    def _parse_maker(self, html: str) -> Optional[str]:
        """Parse maker/studio name"""
        match = re.search(
            r'href="[^"]*(?:\?maker=|/article=maker/id=)\d+[^"]*"[^>]*>([\s\S]*?)</a>',
            html
        )
        return match.group(1).strip() if match else None

    def _parse_label(self, html: str) -> Optional[str]:
        """Parse label name"""
        match = re.search(
            r'href="[^"]*(?:\?label=|/article=label/id=)\d+[^"]*"[^>]*>([\s\S]*?)</a>',
            html
        )
        return match.group(1).strip() if match else None

    def _parse_series(self, html: str) -> Optional[str]:
        """Parse series name"""
        match = re.search(
            r'href="[^"]*/article=series/id=\d+/?"[^>]*>(.*?)</a>',
            html
        )
        return match.group(1).strip() if match else None

    def _parse_actresses(self, soup: BeautifulSoup, html: str) -> list[Actress]:
        """Parse actress information"""
        actresses = []
        seen_names = set()  # Track unique names

        # Find actress links - multiple patterns for different DMM page formats
        patterns = [
            # New format: /list/=/article=actress/id=1031805/
            r'href="[^"]*article=actress/id=(\d+)[^"]*"[^>]*>([^<]+)</a>',
            # Old format: ?actress=12345
            r'href="[^"]*\?actress=(\d+)"[^>]*>([^<]+)</a>',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html)
            if matches:
                for actress_id, name in matches:
                    name = name.strip()
                    if not name:
                        continue

                    # Skip invalid actress names (promotional text, ads, etc.)
                    if not self._is_valid_actress_name(name):
                        continue

                    # Skip duplicates
                    if name in seen_names:
                        continue
                    seen_names.add(name)

                    # Check if name is Japanese
                    is_japanese = bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', name))

                    actress = Actress(
                        japanese_name=name if is_japanese else None,
                        first_name=name if not is_japanese else None,
                    )
                    actresses.append(actress)
                break  # Use first pattern that matches

        return actresses

    def _is_valid_actress_name(self, name: str) -> bool:
        """
        Check if a string is a valid actress name.
        
        Filters out promotional text, ads, and other invalid entries.
        """
        # Names should be reasonable length (most Japanese names < 20 chars)
        if len(name) > 30:
            return False
        
        # Skip if contains promotional markers
        invalid_markers = [
            '★', '☆', '●', '◆', '■',  # Special markers
            'ご購入', '商品', 'こちら',  # Purchase/product text
            'アダルトブック', '写真集',  # Book/photobook promo
            'http', 'www', '.com', '.jp',  # URLs
            '限定', '特典', 'キャンペーン',  # Limited/bonus/campaign
            '配信', 'ダウンロード',  # Distribution/download
        ]
        
        for marker in invalid_markers:
            if marker in name:
                return False
        
        # Name should contain at least some Japanese or Latin characters
        # (not just numbers or special characters)
        has_valid_chars = bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf a-zA-Z]', name))

        if not has_valid_chars:
            return False
        
        return True


    def _parse_genres(self, html: str) -> list[str]:
        """Parse genre list"""
        genres = []

        # Find genre section
        genre_section = re.search(r'>(Genre:|ジャンル：)</td>(.*?)</tr>', html, re.DOTALL)
        if genre_section:
            # Extract genre links
            matches = re.findall(r'>([^<]+)</a>', genre_section.group(2))
            genres = [g.strip() for g in matches if g.strip()]

        return genres

    def _parse_rating(self, html: str) -> Optional[Rating]:
        """Parse rating and vote count"""
        match = re.search(r'<strong>([\d.]+)\s*(?:points|点)</strong>', html)
        if not match:
            return None

        try:
            rating_value = float(match.group(1))
            # Convert 5-point scale to 10-point scale
            rating_10 = rating_value * 2

            # Try to find vote count
            votes_match = re.search(r'<strong>(\d+)</strong>\s*(?:reviews|件)', html)
            votes = int(votes_match.group(1)) if votes_match else 0

            return Rating(rating=rating_10, votes=votes)
        except (ValueError, TypeError):
            return None

    def _parse_cover_url(self, html: str) -> Optional[str]:
        """Parse cover image URL, prioritizing high-quality awsimgsrc.dmm.co.jp domain"""
        match = re.search(
            r'(https://pics\.dmm\.co\.jp/(?:mono/movie/adult|digital/(?:video|amateur))/[^"]+\.jpg)',
            html
        )
        if match:
            cover = match.group(1)
            # Convert small image to large
            cover = cover.replace("ps.jpg", "pl.jpg")

            # Convert to high-quality awsimgsrc.dmm.co.jp domain
            # Only for digital/video or digital/amateur paths (mono/movie/adult not compatible)
            if "pics.dmm.co.jp" in cover and "/digital/" in cover:
                cover = cover.replace("pics.dmm.co.jp", "awsimgsrc.dmm.co.jp/pics_dig")

            return cover
        return None

    def _parse_screenshot_urls(self, soup: BeautifulSoup) -> list[str]:
        """Parse screenshot image URLs"""
        urls = []

        for img in soup.select('a[name="sample-image"] img[data-lazy]'):
            url = img.get("data-lazy")
            if url and isinstance(url, str):
                # Convert to full size
                url = url.replace("-", "jp-")
                urls.append(url)

        return urls

    def _parse_trailer_url(self, html: str) -> Optional[str]:
        """Parse trailer video URL"""
        match = re.search(r"sampleplay\('([^']+)'\)", html)
        if match:
            iframe_path = match.group(1)
            # Would need additional request to get actual video URL
            # For POC, just return the iframe path indicator
            return f"{self.base_url}{iframe_path}"
        return None


# Example usage
if __name__ == "__main__":
    with DMMScraper() as scraper:
        metadata = scraper.find("IPX-486")
        if metadata:
            print(f"Title: {metadata.title}")
            print(f"ID: {metadata.id}")
            print(f"Maker: {metadata.maker}")
            print(f"Actresses: {[a.japanese_name or a.full_name for a in metadata.actresses]}")
            print(f"Genres: {metadata.genres}")

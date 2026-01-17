"""MGStage HTML scraper for metadata

MGStage is a Japanese JAV publisher/distributor requiring Japan IP to access.
This scraper parses HTML content from MGStage product pages.

NOTE: Requires Japan proxy to access. Configure proxy in settings.
"""

import re
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

from javinizer.models import Actress, MovieMetadata, ProxyConfig
from javinizer.scrapers.base import BaseScraper
from javinizer.logger import get_logger

logger = get_logger(__name__)


class MGStageScraper(BaseScraper):
    """
    Scraper for MGStage

    MGStage is an official JAV distributor in Japan.
    Requires Japan proxy to access.

    Usage:
        proxy = ProxyConfig(enabled=True, url="socks5://japan-proxy:1080")
        scraper = MGStageScraper(proxy=proxy)
        metadata = scraper.find("SIRO-5000")
    """

    name = "mgstage"
    base_url = "https://www.mgstage.com"

    # Age verification cookie required
    AGE_CHECK_COOKIE = {"adc": "1"}

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        cookies: Optional[dict[str, str]] = None,
        user_agent: Optional[str] = None,
    ):
        # Merge age verification cookie with user cookies
        merged_cookies = {**self.AGE_CHECK_COOKIE}
        if cookies:
            merged_cookies.update(cookies)

        super().__init__(
            timeout=timeout,
            proxy=proxy,
            cookies=merged_cookies,
            user_agent=user_agent,
        )

    def get_search_url(self, movie_id: str) -> str:
        """Build search URL for movie ID"""
        return f"{self.base_url}/search/cSearch.php?search_word={movie_id.strip()}&sort=new"

    def get_movie_url(self, movie_id: str) -> Optional[str]:
        """Get movie URL from movie ID"""
        # 1. Try direct URL first (most common case is exact match or simple prefix)
        url = f"{self.base_url}/product/product_detail/{movie_id}/"
        try:
            response = self.client.get(url, follow_redirects=True)
            if response.status_code == 200 and self._is_valid_movie_page(response.text):
                return str(response.url)
        except Exception:
            pass

        # 2. Try searching if direct access fails
        return self._find_movie_url(movie_id)

    def _find_movie_url(self, movie_id: str) -> Optional[str]:
        """Search for movie ID and return product URL"""
        search_term = movie_id
        
        # Search strategy 1: Exact ID search
        url = self._search_and_find(search_term, movie_id)
        if url:
            return url
            
        # Search strategy 2: Numeric part search (robust for prefixed/suffixed IDs)
        # e.g. START-469 -> search 469, match START
        match = re.search(r'([A-Z]+)[-_]?(\d+)', movie_id, re.IGNORECASE)
        if match:
            alpha = match.group(1)
            num = match.group(2)
            url = self._search_and_find(num, alpha)
            if url:
                return url
                
        return None

    def _search_and_find(self, query: str, filter_text: str) -> Optional[str]:
        """Search not finding the query, but filtering results"""
        search_url = f"{self.base_url}/search/cSearch.php?search_word={query}&sort=new"
        try:
            response = self.client.get(search_url)
            if response.status_code != 200:
                return None
                
            # Parse results
            found_ids = list(set(re.findall(r'/product/product_detail/([A-Z0-9-]+)/', response.text)))
            
            clean_filter = filter_text.replace("-", "").upper()
            
            for fid in found_ids:
                clean_fid = fid.replace("-", "").upper()
                # Check if filter is in ID
                if clean_filter in clean_fid:
                    return f"{self.base_url}/product/product_detail/{fid}/"
                    
        except Exception:
            pass
        return None
        
    def _is_valid_movie_page(self, html: str) -> bool:
        """Check if HTML contains valid movie content"""
        return (
            '<div class="common_detail_cover"' in html or
            'class="detail_data"' in html or
            '<h1 class="tag">' in html
        )

    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from MGStage movie page"""
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
            # Extract movie ID from URL or page
            movie_id = self._extract_id(html, url)
            if not movie_id:
                logger.debug(f"[{self.name}] Could not extract movie ID from {url}")
                return None

            metadata = MovieMetadata(
                id=movie_id,
                title=self._extract_title(html),
                original_title=self._extract_title(html),  # MGStage is Japanese only
                description=self._extract_description(html),
                release_date=self._extract_date(html),
                runtime=self._extract_runtime(html),
                director=None,  # MGStage rarely shows director
                maker=self._extract_maker(html),
                label=self._extract_label(html),
                series=self._extract_series(html),
                actresses=self._extract_actresses(html),
                genres=self._extract_genres(html),
                rating=None,
                cover_url=self._extract_cover(html),
                screenshot_urls=self._extract_screenshots(html),
                trailer_url=self._extract_trailer(html),
                source=self.name,
            )

            return metadata

        except Exception as e:
            logger.error(f"[{self.name}] Error parsing HTML: {e}", exc_info=True)
            return None

    def _extract_id(self, html: str, url: str) -> Optional[str]:
        """Extract movie ID from HTML or URL"""
        # Try to get from URL first
        match = re.search(r'/product_detail/([A-Z0-9-]+)/?', url, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Try from page content
        # Pattern: 品番: ABC-123
        match = re.search(
            r'>(?:品番|Product ID)[：:]?\s*</th>\s*<td[^>]*>([A-Z0-9-]+)</td>',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).upper()

        return None

    def _extract_title(self, html: str) -> str:
        """Extract movie title"""
        # Pattern: <h1 class="tag">Title</h1>
        match = re.search(r'<h1[^>]*class="tag"[^>]*>([^<]+)</h1>', html)
        if match:
            return match.group(1).strip()

        # Alternative: <title> tag
        match = re.search(r'<title>([^<]+)</title>', html)
        if match:
            title = match.group(1).strip()
            # Remove site name suffix
            title = re.sub(r'\s*[-|]\s*MGステージ.*$', '', title)
            title = re.sub(r'\s*[-|]\s*MGS.*$', '', title)
            return title

        return "Unknown"

    def _extract_description(self, html: str) -> Optional[str]:
        """Extract movie description"""
        # Pattern: <p class="introduction">Description</p>
        match = re.search(
            r'<p[^>]*class="[^"]*introduction[^"]*"[^>]*>(.*?)</p>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            desc = match.group(1)
            # Clean HTML tags
            desc = re.sub(r'<[^>]+>', '', desc)
            desc = desc.strip()
            return desc if desc else None
        return None

    def _extract_date(self, html: str) -> Optional[date]:
        """Extract release date"""
        # Pattern: 配信開始日: 2024/01/15
        match = re.search(
            r'>(?:配信開始日|配信日|発売日|Release)[：:]?\s*</th>\s*<td[^>]*>(\d{4}/\d{2}/\d{2})</td>',
            html,
        )
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y/%m/%d").date()
            except ValueError:
                pass

        # Alternative format: 2024-01-15
        match = re.search(
            r'>(?:配信開始日|配信日|発売日)[：:]?\s*</th>\s*<td[^>]*>(\d{4}-\d{2}-\d{2})</td>',
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
        # Pattern: 収録時間: 120分
        match = re.search(
            r'>(?:収録時間|再生時間|Duration)[：:]?\s*</th>\s*<td[^>]*>(\d+)\s*分</td>',
            html,
        )
        if match:
            return int(match.group(1))
        return None

    def _extract_maker(self, html: str) -> Optional[str]:
        """Extract studio/maker name"""
        # Search within the table row for Maker
        match = re.search(
            r'<th>(?:メーカー|Maker|Studio)[：:]?</th>\s*<td>\s*<a[^>]*>([^<]+)</a>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_label(self, html: str) -> Optional[str]:
        """Extract label name"""
        match = re.search(
            r'<th>(?:レーベル|Label)[：:]?</th>\s*<td>\s*<a[^>]*>([^<]+)</a>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_series(self, html: str) -> Optional[str]:
        """Extract series name"""
        match = re.search(
            r'<th>(?:シリーズ|Series)[：:]?</th>\s*<td>\s*<a[^>]*>([^<]+)</a>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_actresses(self, html: str) -> list[Actress]:
        """Extract actress information"""
        actresses = []
        
        # Find the row containing actresses
        # <tr><th>出演：</th><td>...</td></tr>
        row_match = re.search(
            r'<th>(?:出演|Actresses|Cast)[：:]?</th>\s*<td>(.*?)</td>',
            html,
            re.IGNORECASE | re.DOTALL
        )
        
        if not row_match:
            return []

        content = row_match.group(1)
        
        # Extract links from the cell content
        # Pattern: <a href="/actress/...">Name</a> or /search/cSearch.php?actor[]=...
        pattern = re.compile(
            r'<a[^>]*href="[^"]*(?:/actress/|/talent/|actor\[\])[^"]*"[^>]*>([^<]+)</a>',
            re.IGNORECASE,
        )

        found_names = set()
        for match in pattern.finditer(content):
            name = match.group(1).strip()
            if not name or name in ("---", "----") or name in found_names:
                continue

            found_names.add(name)
            actress = Actress(
                first_name=None,
                last_name=None,
                japanese_name=name,
                thumb_url=None,
            )
            actresses.append(actress)

        return actresses

    def _extract_genres(self, html: str) -> list[str]:
        """Extract genre tags"""
        genres = []

        # Find the row containing genres
        row_match = re.search(
            r'<th>(?:ジャンル|Genre)[：:]?</th>\s*<td>(.*?)</td>',
            html,
            re.IGNORECASE | re.DOTALL
        )
        
        if not row_match:
            return []

        content = row_match.group(1)
        
        # Extract links from the cell content
        pattern = re.compile(
            r'<a[^>]*href="[^"]*(?:/genre/|genre\[\])[^"]*"[^>]*>([^<]+)</a>',
            re.IGNORECASE,
        )

        for match in pattern.finditer(content):
            genre = match.group(1).strip()
            if genre and genre not in genres:
                genres.append(genre)

        return genres

    def _extract_cover(self, html: str) -> Optional[str]:
        """Extract cover image URL"""
        # Pattern: <a ... class="link_magnify" ... href="url" ...>
        # Handles class before href or href before class via alternation or check
        
        # Unified regex for link_magnify (common case)
        # Matches <a ... href="..." ... class="link_magnify" ...> or <a ... class="link_magnify" ... href="..." ...>
        match = re.search(
            r'<a[^>]+(?:class="[^"]*link_magnify[^"]*"[^>]+href="([^"]+)"|href="([^"]+)"[^>]+class="[^"]*link_magnify[^"]*")',
            html,
            re.IGNORECASE
        )
        if match:
            # Group 1 is from class...href, Group 2 is from href...class
            url = match.group(1) or match.group(2)
            return self._normalize_url(url)

        # Pattern: <a href="large_cover.jpg" class="sample_image"> (Old)
        match = re.search(
            r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*sample_image[^"]*"',
            html,
            re.IGNORECASE
        )
        if match:
            return self._normalize_url(match.group(1))

        # Alternative: main image (enlarge_image or detail_img)
        match = re.search(
            r'<img[^>]*class="[^"]*(?:detail_img|enlarge_image)[^"]*"[^>]*src="([^"]+)"',
            html,
            re.IGNORECASE
        )
        if match:
             # This is usually a smaller image or package shot, but better than nothing
            return self._normalize_url(match.group(1))

        return None

    def _normalize_url(self, url: str) -> str:
        """Helper to qualify relative URLs"""
        if not url.startswith("http"):
            return urljoin(self.base_url, url)
        return url

    def _extract_screenshots(self, html: str) -> list[str]:
        """Extract screenshot/sample image URLs"""
        screenshots = []

        # Pattern: sample images in gallery
        pattern = re.compile(
            r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*sample[^"]*"[^>]*>',
            re.IGNORECASE,
        )

        for match in pattern.finditer(html):
            url = match.group(1)
            if not url.startswith("http"):
                url = urljoin(self.base_url, url)
            if url not in screenshots:
                screenshots.append(url)

        return screenshots

    def _extract_trailer(self, html: str) -> Optional[str]:
        """Extract trailer/sample video URL"""
        # Pattern: sample movie URL
        match = re.search(
            r'sampleMovie["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            html,
        )
        if match:
            return match.group(1)

        # Alternative: data-video attribute
        match = re.search(
            r'data-video\s*=\s*["\']([^"\']+)["\']',
            html,
        )
        if match:
            return match.group(1)

        return None


# Example usage


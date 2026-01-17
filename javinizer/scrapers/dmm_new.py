"""DMM New Site (video.dmm.co.jp) scraper using Playwright for JavaScript rendering

This scraper handles the new React SPA version of DMM/Fanza that requires
JavaScript execution to render content.

Installation:
    pip install javinizer[browser]
    playwright install chromium
"""

import re
from datetime import datetime
from typing import Any, Optional

from javinizer.models import Actress, MovieMetadata, ProxyConfig
from javinizer.logger import get_logger

logger = get_logger(__name__)


def is_playwright_available() -> bool:
    """Check if Playwright is installed"""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401

        return True
    except ImportError:
        return False


class DMMNewScraper:
    """
    Scraper for the new video.dmm.co.jp React SPA site

    This uses Playwright to render JavaScript and extract data from the DOM.
    Falls back gracefully if Playwright is not installed.
    """

    name = "dmm_new"
    base_url = "https://video.dmm.co.jp"

    def __init__(
        self,
        timeout: float = 30.0,
        proxy: Optional[ProxyConfig] = None,
        headless: bool = True,
    ):
        self.timeout = timeout
        self.proxy = proxy
        self.headless = headless
        self._browser: Optional[Any] = None
        self._playwright: Optional[Any] = None

    def __enter__(self) -> "DMMNewScraper":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close browser and playwright"""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def _get_browser(self) -> Any:
        """Lazily initialize Playwright browser

        Tries to use system Chrome first, falls back to Chromium if available.
        """
        if not is_playwright_available():
            raise ImportError(
                "Playwright is required for new DMM site scraping. "
                "Install with: pip install javinizer[browser]"
            )

        if self._browser is None:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()

            # Setup proxy if configured
            proxy_config: Any = None
            if self.proxy and self.proxy.enabled and self.proxy.url:
                proxy_config = {"server": self.proxy.url}

            # Try to use system Chrome first (no download needed)
            try:
                self._browser = self._playwright.chromium.launch(
                    headless=self.headless,
                    proxy=proxy_config,
                    channel="chrome",  # Use system Chrome
                )
            except Exception:
                # Fall back to Playwright's Chromium
                try:
                    self._browser = self._playwright.chromium.launch(
                        headless=self.headless,
                        proxy=proxy_config,
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"Cannot launch browser. Either install Chrome or run: playwright install chromium. Error: {e}"
                    )

        return self._browser

    @staticmethod
    def normalize_id_variants(movie_id: str) -> list[str]:
        """
        Generate possible content ID formats for a movie ID
        """
        movie_id = movie_id.upper().strip()

        match = re.match(r"([A-Z]+)-?(\d+)", movie_id)
        if not match:
            return [movie_id.lower()]

        prefix, number = match.groups()
        prefix_lower = prefix.lower()

        variants = []

        # Format 1: prefix + padded number (ipx00486) - Common format
        variants.append(f"{prefix_lower}{number.zfill(5)}")

        # Format 2: digit prefix + prefix + padded number (1start00422) - For some series
        variants.append(f"1{prefix_lower}{number.zfill(5)}")

        # Format 3: prefix + number without padding
        variants.append(f"{prefix_lower}{number}")

        # Format 4: digit prefix + prefix + number (1start422)
        variants.append(f"1{prefix_lower}{number}")

        # Format 5: h_ prefix for amateur content
        variants.append(f"h_{prefix_lower}{number.zfill(5)}")

        return variants

    def get_movie_url(self, content_id: str) -> str:
        """Get movie URL for new DMM site with specific content ID"""
        return f"{self.base_url}/av/content/?id={content_id}"

    def find(self, movie_id: str) -> Optional[MovieMetadata]:
        """Find and scrape movie metadata using multiple ID variants"""
        variants = self.normalize_id_variants(movie_id)

        for content_id in variants:
            url = self.get_movie_url(content_id)
            meta = self.scrape(url)
            if meta:
                return meta
        return None

    def scrape(self, url: str) -> Optional[MovieMetadata]:
        """Scrape metadata from new DMM site using Playwright"""
        try:
            browser = self._get_browser()
        except (ImportError, RuntimeError) as e:
            print(f"DMM New Scraper: {e}")
            return None

        page = browser.new_page()

        try:
            # Set cookies for age verification on multiple domains
            page.context.add_cookies(
                [
                    {
                        "name": "age_check_done",
                        "value": "1",
                        "domain": ".dmm.co.jp",
                        "path": "/",
                    },
                    {
                        "name": "age_check_done",
                        "value": "1",
                        "domain": "video.dmm.co.jp",
                        "path": "/",
                    },
                    {
                        "name": "age_check_done",
                        "value": "1",
                        "domain": "www.dmm.co.jp",
                        "path": "/",
                    },
                ]
            )

            # Navigate and wait for content to load
            try:
                page.goto(
                    url, timeout=int(self.timeout * 1000), wait_until="networkidle"
                )
            except Exception:
                pass

            # Check for 404 immediately
            if self._is_404(page):
                return None

            # Check if we got redirected to age check page
            if "age_check" in page.url:
                try:
                    age_button = page.query_selector(
                        'a:has-text("はい"), a[href*="age_check"], input[type="submit"]'
                    )
                    if age_button:
                        age_button.click()
                        page.wait_for_load_state("networkidle")
                except Exception:
                    pass

            # Also check for overlay/modal age check
            try:
                age_button = page.query_selector(
                    'button:has-text("はい"), button:has-text("Enter"), [class*="age"] button'
                )
                if age_button:
                    age_button.click()
                    page.wait_for_timeout(1000)
            except Exception:
                pass

            # Check for 404 again after potential redirects
            if self._is_404(page):
                return None

            # Wait for content
            try:
                page.wait_for_selector(
                    'h1, img[src*="pics.dmm"], [class*="content"]', timeout=10000
                )
            except Exception:
                pass

            # Check for 404 one last time
            if self._is_404(page):
                return None

            # Wait a bit more for dynamic content to settle
            page.wait_for_timeout(2000)

            # Extract data from rendered page
            return self._extract_metadata(page, page.url)

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
        finally:
            page.close()

    def _is_404(self, page: Any) -> bool:
        """Check if page is 404 Not Found"""
        try:
            # Check title
            title = page.title().lower()
            if (
                "404" in title
                or "not found" in title
                or "ページが見つかりません" in title
            ):
                return True

            # Check h1
            h1 = page.query_selector("h1")
            if h1:
                text = h1.inner_text().strip().lower()
                if "404" in text or "not found" in text:
                    return True

            return False
        except Exception:
            return False

    def _extract_metadata(self, page: Any, url: str) -> Optional[MovieMetadata]:
        """Extract metadata from rendered page"""
        try:
            # Check 404 (redundant but safe)
            if self._is_404(page):
                return None

            # Extract content ID from URL
            content_id_match = re.search(r"id=([^&]+)", url)
            content_id = content_id_match.group(1) if content_id_match else ""

            # Convert content ID to display ID
            movie_id = self._content_id_to_movie_id(content_id)

            # Extract title - try multiple selectors
            title = None
            for selector in ["h1", '[class*="title" i]', "title"]:
                try:
                    elem = page.query_selector(selector)
                    if elem:
                        title = elem.inner_text().strip()
                        if title and len(title) > 5:
                            break
                except Exception:
                    continue

            # Extract data table values
            data = {}

            # Try to find data rows (dt/dd pairs or table rows)
            rows = page.query_selector_all("dt, th")
            for row in rows:
                try:
                    row_label = row.inner_text().strip()
                    # Find corresponding value
                    value_elem = row.evaluate("el => el.nextElementSibling")
                    if value_elem:
                        value = page.evaluate("el => el.innerText", value_elem)
                        data[row_label] = value.strip() if value else ""
                except Exception:
                    continue

            # Extract actresses - only from main content table, avoid sidebar
            actresses = []
            # Look for actress links within the main content table (links with ?actress= pattern)
            main_table = page.query_selector("main table")
            if main_table:
                actress_links = main_table.query_selector_all('a[href*="?actress="]')
                for link in actress_links:
                    try:
                        name = link.inner_text().strip()
                        # Skip empty or placeholder values
                        if not name or name == "-" or name == "----" or len(name) > 30:
                            continue

                        skip_keywords = [
                            "一覧",
                            "リスト",
                            "もっと",
                            "作品",
                            "すべて",
                            "検索",
                            "AV女優",
                            "ランキング",
                        ]
                        if any(k in name for k in skip_keywords):
                            continue

                        is_japanese = bool(
                            re.search(
                                r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]", name
                            )
                        )
                        actresses.append(
                            Actress(
                                japanese_name=name if is_japanese else None,
                                first_name=name if not is_japanese else None,
                            )
                        )
                    except Exception:
                        continue

            # Extract maker from main table
            maker = ""
            maker_link = page.query_selector('main table a[href*="?maker="]')
            if maker_link:
                maker = maker_link.inner_text().strip()

            # Extract label from main table
            label = ""
            label_link = page.query_selector('main table a[href*="?label="]')
            if label_link:
                label = label_link.inner_text().strip()

            # Extract genres - from main content table only
            genres = []
            if main_table:
                # Get genre links from table
                genre_links = main_table.query_selector_all('a[href*="?genre="]')
                for link in genre_links:
                    try:
                        genre = link.inner_text().strip()
                        if genre and genre not in genres and len(genre) < 30:
                            genres.append(genre)
                    except Exception:
                        continue

            # Extract cover image - prioritize awsimgsrc.dmm.co.jp with pl.jpg pattern
            cover_url = None
            cover_selectors = [
                'img[src*="awsimgsrc.dmm.co.jp"][src*="pl.jpg"]',  # High quality poster
                'img[src*="awsimgsrc.dmm.co.jp"]',
                'img[src*="pics.dmm.co.jp"][src*="pl.jpg"]',
                'img[src*="cdn.dap.dmm.co.jp"]',
                'img[src*="pics.dmm.co.jp"]',
            ]
            for selector in cover_selectors:
                try:
                    imgs = page.query_selector_all(selector)
                    for img in imgs:
                        src = img.get_attribute("src")
                        if src and (".jpg" in src.lower() or ".webp" in src.lower()):
                            # Remove all query params to get full resolution image
                            if "?" in src:
                                src = src.split("?")[0]
                            cover_url = src
                            break
                    if cover_url:
                        break
                except Exception:
                    continue

            # If no cover found with selectors, construct URL from content_id
            if not cover_url and content_id:
                cover_url = f"https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/{content_id}/{content_id}pl.jpg"

            # Parse release date and runtime from table rows in main table
            release_date = None
            runtime = None

            if main_table:
                # Get all table rows
                rows = main_table.query_selector_all("tr")
                for row in rows:
                    try:
                        th = row.query_selector("th")
                        td = row.query_selector("td span, td")
                        if th and td:
                            row_label = th.inner_text().strip()
                            value = td.inner_text().strip()

                            # Release date
                            if "配信開始日" in row_label or "発売日" in row_label:
                                date_match = re.search(
                                    r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", value
                                )
                                if date_match:
                                    try:
                                        y, m, d = date_match.groups()
                                        release_date = datetime(
                                            int(y), int(m), int(d)
                                        ).date()
                                    except Exception:
                                        pass

                            # Runtime
                            if "収録時間" in row_label:
                                runtime_match = re.search(r"(\d+)", value)
                                if runtime_match:
                                    runtime = int(runtime_match.group(1))
                    except Exception:
                        continue

            # Fallback to data dict if table parsing failed
            if not release_date:
                for key in ["発売日", "配信開始日", "Release Date"]:
                    if key in data:
                        date_match = re.search(
                            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", data[key]
                        )
                        if date_match:
                            try:
                                y, m, d = date_match.groups()
                                release_date = datetime(int(y), int(m), int(d)).date()
                            except Exception as e:
                                logger.debug(f"Failed to parse release date: {e}")
                                pass
                        break

            if not runtime:
                for key in ["収録時間", "Runtime"]:
                    if key in data:
                        runtime_match = re.search(r"(\d+)", data[key])
                        if runtime_match:
                            runtime = int(runtime_match.group(1))
                        break

            return MovieMetadata(
                id=movie_id,
                content_id=content_id,
                title=title or movie_id,
                original_title=title,
                description=data.get("商品説明", ""),
                release_date=release_date,
                runtime=runtime,
                director=data.get("監督", ""),
                maker=maker or data.get("メーカー", "") or data.get("Maker", ""),
                label=label or data.get("レーベル", "") or data.get("Label", ""),
                series=data.get("シリーズ", "") or data.get("Series", ""),
                actresses=actresses,
                genres=genres,
                cover_url=cover_url,
                source="dmm_new",
            )

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return None

    def _content_id_to_movie_id(self, content_id: str) -> str:
        """Convert content ID to display format"""
        # Pattern: optional digit + letters + digits
        match = re.match(r"(\d?)([a-z]+)(\d+)", content_id, re.IGNORECASE)
        if not match:
            return content_id.upper()

        _, prefix, number = match.groups()
        return f"{prefix.upper()}-{number.lstrip('0').zfill(3)}"


# Example usage
if __name__ == "__main__":
    if not is_playwright_available():
        print("Playwright not installed!")
        print("Install with: pip install playwright && playwright install chromium")
    else:
        with DMMNewScraper() as scraper:
            meta = scraper.find("START-422")
            if meta:
                print(f"Title: {meta.title}")
                print(f"ID: {meta.id}")
                print(
                    f"Actresses: {[a.japanese_name or a.full_name for a in meta.actresses]}"
                )
            else:
                print("No results found")

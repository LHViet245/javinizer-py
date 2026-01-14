"""Scrapers package"""

from .base import BaseScraper
from .dmm import DMMScraper
from .r18dev import R18DevScraper
from .javlibrary import JavlibraryScraper
from .javbus import JavBusScraper

# Optional: DMMNewScraper requires playwright
try:
    from .dmm_new import DMMNewScraper, is_playwright_available
except ImportError:
    DMMNewScraper = None

    def is_playwright_available():
        return False


__all__ = [
    "BaseScraper",
    "DMMScraper",
    "R18DevScraper",
    "JavlibraryScraper",
    "JavBusScraper",
    "DMMNewScraper",
    "is_playwright_available",
]

"""Scrapers package"""

from .base import BaseScraper
from .dmm import DMMScraper
from .r18dev import R18DevScraper
from .javlibrary import JavlibraryScraper

# Optional: DMMNewScraper requires playwright
try:
    from .dmm_new import DMMNewScraper, is_playwright_available
except ImportError:
    DMMNewScraper = None
    is_playwright_available = lambda: False

__all__ = [
    "BaseScraper",
    "DMMScraper",
    "R18DevScraper",
    "JavlibraryScraper",
    "DMMNewScraper",
    "is_playwright_available",
]

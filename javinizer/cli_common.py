"""Shared CLI utilities and constants"""

from typing import Optional
from rich.console import Console

from javinizer.models import ProxyConfig
from javinizer.scrapers import DMMScraper, R18DevScraper, JavlibraryScraper, DMMNewScraper

# Global console instance
console = Console()

# Mapping of scraper names to classes
SCRAPERS = {
    "dmm": DMMScraper,
    "dmmja": DMMScraper,
    "r18dev": R18DevScraper,
    "r18": R18DevScraper,
    "javlibrary": JavlibraryScraper,
    "jav": JavlibraryScraper,
}

# Add dmm_new if playwright is available
if DMMNewScraper is not None:
    SCRAPERS["dmm_new"] = DMMNewScraper

# Alias expansion: when user specifies "dmm", try dmm_new first then dmm
SCRAPER_ALIASES = {
    "dmm": ["dmm_new", "dmm"] if DMMNewScraper else ["dmm"],
}


def expand_sources(source_list: list[str]) -> list[str]:
    """Expand source aliases to actual scraper names"""
    expanded = []
    for source in source_list:
        source_lower = source.strip().lower()
        if source_lower in SCRAPER_ALIASES:
            for alias in SCRAPER_ALIASES[source_lower]:
                if alias not in expanded:
                    expanded.append(alias)
        else:
            if source_lower not in expanded:
                expanded.append(source_lower)
    return expanded


def get_scraper(
    name: str,
    proxy: Optional[ProxyConfig] = None,
    cookies: Optional[dict[str, str]] = None,
    user_agent: Optional[str] = None,
):
    """Get scraper instance by name"""
    name_lower = name.lower()
    scraper_class = SCRAPERS.get(name_lower)

    if scraper_class is None:
        return None

    # DMMNewScraper has different signature (no cookies/user_agent)
    if name_lower == "dmm_new":
        return scraper_class(proxy=proxy)

    return scraper_class(
        proxy=proxy,
        cookies=cookies,
        user_agent=user_agent,
    )

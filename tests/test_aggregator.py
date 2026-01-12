# File: tests/test_aggregator.py
"""Tests for metadata aggregation module"""

import pytest
from datetime import date

from javinizer.aggregator import aggregate_metadata, merge_two
from javinizer.models import (
    MovieMetadata,
    Actress,
    Rating,
    ScraperPriority,
)


@pytest.fixture
def dmm_metadata() -> MovieMetadata:
    """Sample metadata from DMM scraper"""
    return MovieMetadata(
        id="IPX-486",
        content_id="ipx00486",
        title="DMM Title (Japanese)",
        original_title="IPX-486 日本語タイトル",
        description="DMM description in Japanese",
        release_date=date(2024, 1, 15),
        runtime=120,
        maker="Idea Pocket",
        label="IP Label",
        actresses=[
            Actress(
                japanese_name="桜もも",
            )
        ],
        genres=["美少女", "女優"],
        rating=Rating(rating=8.5, votes=100),
        cover_url="https://pics.dmm.co.jp/dmm/cover.jpg",
        source="dmm",
    )


@pytest.fixture
def r18dev_metadata() -> MovieMetadata:
    """Sample metadata from R18Dev scraper"""
    return MovieMetadata(
        id="IPX-486",
        content_id="ipx00486",
        title="R18Dev English Title",
        original_title="IPX-486 日本語タイトル",
        description="R18Dev English description",
        release_date=date(2024, 1, 15),
        runtime=120,
        maker="Idea Pocket",
        label="IP Label",
        actresses=[
            Actress(
                first_name="Momo",
                last_name="Sakura",
                japanese_name="桜もも",
                thumb_url="https://r18.dev/thumb.jpg",
            )
        ],
        genres=["Beautiful Girl", "Featured Actress"],
        cover_url="https://r18.dev/cover.jpg",
        source="r18dev",
    )


@pytest.fixture
def javlibrary_metadata() -> MovieMetadata:
    """Sample metadata from Javlibrary scraper"""
    return MovieMetadata(
        id="IPX-486",
        title="Javlibrary Title",
        description=None,  # Javlibrary often lacks description
        release_date=date(2024, 1, 15),
        runtime=119,  # Slightly different runtime
        maker="Idea Pocket Studio",  # Different maker name
        actresses=[
            Actress(
                first_name="Momo",
                last_name="Sakura",
            )
        ],
        genres=["Idol", "Solo", "Beautiful Girl"],
        rating=Rating(rating=9.0, votes=250),
        source="javlibrary",
    )


class TestAggregateMetadata:
    """Test aggregate_metadata function"""

    def test_empty_results_returns_none(self):
        """Test empty results dict returns None"""
        result = aggregate_metadata({})
        assert result is None

    def test_single_source(self, dmm_metadata):
        """Test aggregation with single source"""
        result = aggregate_metadata({"dmm": dmm_metadata})
        assert result is not None
        assert result.id == "IPX-486"
        assert result.title == "DMM Title (Japanese)"
        assert result.source == "aggregated"

    def test_priority_title_from_r18dev(self, dmm_metadata, r18dev_metadata):
        """Test that title is taken from r18dev by default priority"""
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        })
        # Default priority: r18dev > javlibrary > dmm for title
        assert result.title == "R18Dev English Title"

    def test_priority_cover_from_r18dev(self, dmm_metadata, r18dev_metadata):
        """Test that cover URL is taken from r18dev by default priority"""
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        })
        assert result.cover_url == "https://r18.dev/cover.jpg"

    def test_priority_description_from_dmm(self, dmm_metadata, r18dev_metadata):
        """Test that description is taken from dmm by default priority"""
        priority = ScraperPriority(description=["dmm", "r18dev"])
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        }, priority=priority)
        assert result.description == "DMM description in Japanese"

    def test_merge_actresses_unique(self, dmm_metadata, r18dev_metadata):
        """Test that actresses are merged uniquely"""
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        })
        # Should have 1 actress (same person, deduplicated by japanese_name)
        assert len(result.actresses) == 1
        assert result.actresses[0].japanese_name == "桜もも"

    def test_merge_genres_union(self, dmm_metadata, r18dev_metadata):
        """Test that genres are merged as union"""
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        })
        # Should include genres from both sources
        assert "Beautiful Girl" in result.genres
        assert "Featured Actress" in result.genres

    def test_custom_priority(self, dmm_metadata, r18dev_metadata):
        """Test custom priority configuration"""
        priority = ScraperPriority(
            title=["dmm"],
            cover_url=["dmm"],
        )
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        }, priority=priority)
        assert result.title == "DMM Title (Japanese)"
        assert result.cover_url == "https://pics.dmm.co.jp/dmm/cover.jpg"

    def test_alias_expansion_dmm(self, dmm_metadata):
        """Test that 'dmm' alias works for dmm_new."""
        # The aggregator should recognize 'dmm' alias
        priority = ScraperPriority(title=["dmm"])
        result = aggregate_metadata({"dmm": dmm_metadata}, priority=priority)
        assert result.title == "DMM Title (Japanese)"

    def test_fallback_when_primary_empty(self, dmm_metadata, r18dev_metadata):
        """Test fallback to next priority when primary has empty value"""
        dmm_metadata.description = None  # Empty description
        priority = ScraperPriority(description=["dmm", "r18dev"])
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
        }, priority=priority)
        # Should fall back to r18dev
        assert result.description == "R18Dev English description"

    def test_three_sources(self, dmm_metadata, r18dev_metadata, javlibrary_metadata):
        """Test aggregation with three sources"""
        result = aggregate_metadata({
            "dmm": dmm_metadata,
            "r18dev": r18dev_metadata,
            "javlibrary": javlibrary_metadata,
        })
        assert result is not None
        assert result.source == "aggregated"
        # Rating should come from javlibrary (higher votes)
        # Genres should be union of all


class TestMergeTwo:
    """Test merge_two function"""

    def test_merge_prefers_primary(self, dmm_metadata, r18dev_metadata):
        """Test that primary values are preferred"""
        result = merge_two(r18dev_metadata, dmm_metadata)
        assert result.title == "R18Dev English Title"
        assert result.cover_url == "https://r18.dev/cover.jpg"

    def test_merge_fills_missing(self, r18dev_metadata, javlibrary_metadata):
        """Test that missing primary values are filled from secondary"""
        r18dev_metadata.description = None
        javlibrary_metadata.description = "Javlib description"
        result = merge_two(r18dev_metadata, javlibrary_metadata)
        assert result.description == "Javlib description"

    def test_merge_genres_combined(self, dmm_metadata, r18dev_metadata):
        """Test that genres are combined"""
        result = merge_two(dmm_metadata, r18dev_metadata)
        # Should have genres from both
        assert len(result.genres) >= len(dmm_metadata.genres)

    def test_merge_source_combined(self, dmm_metadata, r18dev_metadata):
        """Test that source shows both scrapers"""
        result = merge_two(dmm_metadata, r18dev_metadata)
        assert "dmm" in result.source
        assert "r18dev" in result.source

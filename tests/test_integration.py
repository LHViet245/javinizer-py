"""Integration tests for end-to-end workflows.

These tests verify that components work together correctly.
They use mocked network responses to avoid external dependencies.
"""

import pytest
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from javinizer.models import MovieMetadata, Actress, Settings
from javinizer.aggregator import aggregate_metadata
from javinizer.scrapers.r18dev import R18DevScraper
from javinizer.scrapers.dmm import DMMScraper
from javinizer.exceptions import NetworkError, ScraperError


class TestAggregatorIntegration:
    """Test aggregator with multiple scraper results."""

    def test_aggregate_from_multiple_sources(self):
        """Test that aggregator correctly merges data from multiple sources."""
        # Simulate results from R18Dev
        r18dev_result = MovieMetadata(
            id="IPX-486",
            title="English Title from R18Dev",
            original_title="日本語タイトル",
            release_date=date(2024, 1, 15),
            runtime=120,
            maker="Studio A",
            actresses=[
                Actress(
                    first_name="Momo",
                    last_name="Sakura",
                    japanese_name="桜もも",
                )
            ],
            genres=["Beautiful Girl"],
            cover_url="https://r18.dev/cover.jpg",
            source="r18dev",
        )

        # Simulate results from DMM (different data)
        dmm_result = MovieMetadata(
            id="IPX-486",
            title="Japanese Title from DMM",
            description="Detailed description from DMM",
            runtime=125,
            maker="Studio B",
            actresses=[
                Actress(japanese_name="桜もも"),
                Actress(japanese_name="新垣結衣"),  # Extra actress from DMM
            ],
            genres=["Featured Actress", "HD"],
            cover_url="https://dmm.co.jp/cover_high.jpg",
            source="dmm",
        )

        results = {
            "r18dev": r18dev_result,
            "dmm": dmm_result,
        }

        aggregated = aggregate_metadata(results)

        assert aggregated is not None
        # Title should come from r18dev (higher priority by default)
        assert aggregated.title == "English Title from R18Dev"
        # Description should come from dmm (only source with description)
        assert aggregated.description == "Detailed description from DMM"
        # Genres should be merged from all sources
        assert "Beautiful Girl" in aggregated.genres
        assert "Featured Actress" in aggregated.genres
        assert "HD" in aggregated.genres
        # Actresses should be merged (unique by japanese_name)
        assert len(aggregated.actresses) == 2

    def test_aggregate_single_source(self):
        """Test aggregation with single source returns that source's data."""
        single_result = MovieMetadata(
            id="ABC-123",
            title="Only Title",
            source="r18dev",
        )

        results = {"r18dev": single_result}
        aggregated = aggregate_metadata(results)

        assert aggregated is not None
        assert aggregated.title == "Only Title"
        assert aggregated.id == "ABC-123"

    def test_aggregate_empty_results(self):
        """Test aggregation with empty results returns None."""
        assert aggregate_metadata({}) is None


class TestScraperMocking:
    """Test scrapers with mocked HTTP responses."""

    def test_r18dev_scraper_with_mocked_response(self):
        """Test R18Dev scraper parsing with mocked JSON response."""
        mock_json = {
            "dvd_id": "IPX-486",
            "title": "Test Movie",
            "title_ja": "テスト映画",
            "release_date": "2024-01-15",
            "runtime": 120,
            "maker": {"name_en": "Test Studio"},
            "label": {"name_en": "Test Label"},
            "actresses": [
                {
                    "name_romaji": "Kana Momonogi",
                    "name_kanji": "桃乃木かな",
                    "image_url": "https://example.com/thumb.jpg",
                }
            ],
            "categories": [
                {"name_en": "Beautiful Girl", "name_ja": "美少女"}
            ],
            "jacket_full_url": "https://example.com/cover.jpg",
        }

        scraper = R18DevScraper()

        # Create mock client and response
        mock_response = Mock()
        mock_response.json.return_value = mock_json
        mock_response.status_code = 200

        mock_client = Mock()
        mock_client.get.return_value = mock_response

        # Directly set the private _client attribute
        scraper._client = mock_client

        # Test the parsing logic
        result = scraper.scrape("https://r18.dev/videos/vod/movies/detail/-/id=ipx00486/")

        assert result is not None
        assert result.id == "IPX-486"
        assert result.title == "Test Movie"
        assert len(result.actresses) == 1
        assert result.actresses[0].japanese_name == "桃乃木かな"


class TestExceptionHandling:
    """Test that exceptions are properly raised and handled."""

    def test_network_error_contains_context(self):
        """Test that NetworkError contains useful context."""
        error = NetworkError(
            "Connection failed",
            scraper_name="r18dev",
            movie_id="IPX-486",
            status_code=503,
            url="https://r18.dev/api/test",
        )

        assert error.scraper_name == "r18dev"
        assert error.movie_id == "IPX-486"
        assert error.status_code == 503
        assert error.url == "https://r18.dev/api/test"
        assert "Connection failed" in str(error)

    def test_scraper_error_inheritance(self):
        """Test that all scraper errors inherit from ScraperError."""
        from javinizer.exceptions import (
            ParseError,
            RateLimitError,
            CloudflareError,
            MovieNotFoundError,
        )

        assert issubclass(NetworkError, ScraperError)
        assert issubclass(ParseError, ScraperError)
        assert issubclass(RateLimitError, ScraperError)
        assert issubclass(CloudflareError, ScraperError)
        assert issubclass(MovieNotFoundError, ScraperError)


class TestSettingsValidation:
    """Test settings loading and validation."""

    def test_default_settings_valid(self):
        """Test that default settings are valid."""
        settings = Settings()

        assert settings.timeout > 0
        assert settings.max_concurrent_downloads >= 1
        assert settings.max_concurrent_scrapers >= 1

    def test_settings_scraper_priorities(self):
        """Test that scraper priorities are properly configured."""
        settings = Settings()

        # Default priorities should include main scrapers
        assert "r18dev" in settings.priority.actress
        assert "dmm" in settings.priority.actress
        assert "javlibrary" in settings.priority.actress


class TestFileOperations:
    """Test file-related operations with temporary directories."""

    def test_temp_directory_creation(self):
        """Test that we can create and cleanup temp directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            assert test_file.exists()
            assert test_file.read_text() == "test content"

        # After context manager, temp dir should be cleaned up
        assert not Path(tmpdir).exists()

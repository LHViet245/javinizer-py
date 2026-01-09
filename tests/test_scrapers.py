"""Tests for scraper modules - uses saved HTML fixtures, no live network"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import date

from javinizer.scrapers.dmm import DMMScraper
from javinizer.scrapers.r18dev import R18DevScraper
from javinizer.models import Actress


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDMMScraper:
    """Test DMM scraper parsing logic"""

    def test_normalize_id_variants_standard(self):
        """Test ID normalization for standard DMM content IDs"""
        variants = DMMScraper.normalize_id_variants("IPX-486")
        assert "ipx00486" in variants
        assert "1ipx00486" in variants

    def test_normalize_id_variants_short_number(self):
        """Test ID normalization with short numbers"""
        variants = DMMScraper.normalize_id_variants("ABC-12")
        assert "abc00012" in variants

    def test_normalize_id_variants_fc2(self):
        """Test that FC2 IDs are handled correctly"""
        variants = DMMScraper.normalize_id_variants("FC2-PPV-123456")
        # FC2 should be in variants
        assert any("fc2" in v.lower() for v in variants)

    def test_normalize_id_returns_list(self):
        """Test that normalize_id_variants returns a list"""
        variants = DMMScraper.normalize_id_variants("SSNI-123")
        assert isinstance(variants, list)
        assert len(variants) > 0

    def test_content_id_to_movie_id_basic(self):
        """Test conversion from DMM content ID to standard format"""
        scraper = DMMScraper()
        assert scraper._content_id_to_movie_id("ipx00486") == "IPX-486"

    def test_content_id_to_movie_id_with_prefix(self):
        """Test conversion with numeric prefix"""
        scraper = DMMScraper()
        # The method should strip leading digits
        result = scraper._content_id_to_movie_id("1ipx00486")
        assert "IPX" in result.upper()

    def test_get_search_url(self):
        """Test search URL generation"""
        scraper = DMMScraper()
        url = scraper.get_search_url("IPX-486")
        assert "dmm.co.jp" in url
        assert "ipx" in url.lower() or "486" in url

    def test_is_valid_actress_name_accepts_valid_names(self):
        """Test that valid actress names are accepted"""
        scraper = DMMScraper()
        assert scraper._is_valid_actress_name("桃乃木かな") is True
        assert scraper._is_valid_actress_name("Kana Momonogi") is True
        assert scraper._is_valid_actress_name("明日花キララ") is True

    def test_is_valid_actress_name_rejects_promotional_text(self):
        """Test that promotional text is rejected"""
        scraper = DMMScraper()
        # Reject promotional markers
        assert scraper._is_valid_actress_name("★アダルトブック「桃乃木かな写真集」の商品ご購入はこちらから★") is False
        # Reject text with purchase links
        assert scraper._is_valid_actress_name("商品ご購入はこちら") is False
        # Reject very long strings
        assert scraper._is_valid_actress_name("A" * 50) is False

class TestR18DevScraper:
    """Test R18Dev JSON API scraper"""

    def test_normalize_id_variants(self):
        """Test ID normalization for R18Dev"""
        variants = R18DevScraper.normalize_id_variants("SSNI-123")
        assert "ssni00123" in variants

    def test_normalize_id_variants_four_digit(self):
        """Test with 4-digit number"""
        variants = R18DevScraper.normalize_id_variants("IPX-1234")
        assert "ipx01234" in variants or "ipx1234" in variants

    def test_normalize_id_basic(self):
        """Test basic normalize_id method"""
        result = R18DevScraper.normalize_id("ABC-123")
        assert result is not None
        assert isinstance(result, str)

    def test_get_search_url(self):
        """Test API URL generation"""
        scraper = R18DevScraper()
        url = scraper.get_search_url("IPX-486")
        assert "r18.dev" in url

    def test_parse_actresses_from_json(self):
        """Test actress parsing from JSON response"""
        scraper = R18DevScraper()
        # Mock data matches actual R18Dev API structure
        mock_data = {
            "actresses": [
                {
                    "name_romaji": "Momo Sakura",
                    "name_kanji": "桜もも",
                    "image_url": "http://example.com/thumb.jpg"
                }
            ]
        }
        actresses = scraper._parse_actresses(mock_data)
        assert len(actresses) == 1
        assert actresses[0].japanese_name == "桜もも"
        assert actresses[0].first_name == "Momo"
        assert actresses[0].last_name == "Sakura"


    def test_parse_actresses_empty(self):
        """Test actress parsing with no actresses"""
        scraper = R18DevScraper()
        actresses = scraper._parse_actresses({})
        assert actresses == []

    def test_parse_genres_from_json(self):
        """Test genre parsing from categories"""
        scraper = R18DevScraper()
        # Mock data matches actual R18Dev API structure
        mock_data = {
            "categories": [
                {"name_en": "Beautiful Girl", "name_ja": "美少女"},
                {"name_en": "Featured Actress", "name_ja": "出演女優"}
            ]
        }
        genres = scraper._parse_genres(mock_data)
        assert "Beautiful Girl" in genres
        assert "Featured Actress" in genres


    def test_get_title_prefers_english(self):
        """Test title extraction prefers English"""
        scraper = R18DevScraper()
        mock_data = {
            "title": "English Title",
            "title_ja": "日本語タイトル"
        }
        title = scraper._get_title(mock_data)
        assert title == "English Title"

    def test_get_title_fallback_to_japanese(self):
        """Test title fallback to Japanese when English not available"""
        scraper = R18DevScraper()
        mock_data = {
            "title": "",
            "title_ja": "日本語タイトル"
        }
        title = scraper._get_title(mock_data)
        assert title == "日本語タイトル"

    def test_parse_date_valid(self):
        """Test date parsing with valid date string"""
        scraper = R18DevScraper()
        result = scraper._parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_date_invalid(self):
        """Test date parsing with invalid input"""
        scraper = R18DevScraper()
        result = scraper._parse_date("not-a-date")
        assert result is None

    def test_parse_date_none(self):
        """Test date parsing with None input"""
        scraper = R18DevScraper()
        result = scraper._parse_date(None)
        assert result is None


class TestScraperBaseClass:
    """Test BaseScraper functionality"""

    def test_dmm_scraper_has_name(self):
        """Test that DMMScraper has correct name"""
        scraper = DMMScraper()
        assert scraper.name == "dmm"

    def test_r18dev_scraper_has_name(self):
        """Test that R18DevScraper has correct name"""
        scraper = R18DevScraper()
        assert scraper.name == "r18dev"

    def test_context_manager_closes_client(self):
        """Test that context manager closes client"""
        with DMMScraper() as scraper:
            # Access client to initialize it
            _ = scraper.timeout
        # After exiting context, client should be closed (None)
        assert scraper._client is None

    def test_verify_ssl_default_true(self):
        """Test that SSL verification is enabled by default"""
        scraper = DMMScraper()
        assert scraper.verify_ssl is True

    def test_verify_ssl_can_be_disabled(self):
        """Test that SSL verification can be disabled"""
        scraper = DMMScraper(verify_ssl=False)
        assert scraper.verify_ssl is False

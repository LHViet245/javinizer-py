# File: tests/test_utils.py
"""Tests for shared scraper utilities"""


from javinizer.scrapers.utils import (
    normalize_id_variants,
    normalize_id,
    content_id_to_movie_id,
    is_valid_actress_name,
)


class TestNormalizeIdVariants:
    """Test normalize_id_variants function"""

    def test_standard_id(self):
        """Test normalization of standard movie ID"""
        variants = normalize_id_variants("IPX-486")
        assert "ipx00486" in variants
        assert "1ipx486" in variants
        assert "ipx486" in variants

    def test_short_number(self):
        """Test ID with short number"""
        variants = normalize_id_variants("ABC-12")
        assert "abc00012" in variants

    def test_no_hyphen(self):
        """Test ID without hyphen"""
        variants = normalize_id_variants("SSNI123")
        assert "ssni00123" in variants

    def test_four_digit_number(self):
        """Test ID with 4-digit number"""
        variants = normalize_id_variants("IPX-1234")
        assert "ipx01234" in variants

    def test_case_insensitive(self):
        """Test case insensitivity"""
        upper = normalize_id_variants("IPX-486")
        lower = normalize_id_variants("ipx-486")
        assert upper == lower

    def test_h_prefix_variant(self):
        """Test h_ prefix variant for amateur content"""
        variants = normalize_id_variants("ABC-123")
        assert any("h_" in v for v in variants)

    def test_non_standard_id(self):
        """Test non-standard ID returns lowercased"""
        variants = normalize_id_variants("SPECIAL_ID")
        assert "special_id" in variants


class TestNormalizeId:
    """Test normalize_id function"""

    def test_basic_normalization(self):
        """Test basic ID normalization"""
        content_id, display_id = normalize_id("IPX-486")
        assert content_id == "ipx00486"
        assert display_id == "IPX-486"

    def test_short_number_display(self):
        """Test display ID has at least 3 digits"""
        _, display_id = normalize_id("ABC-1")
        assert display_id == "ABC-001"


class TestContentIdToMovieId:
    """Test content_id_to_movie_id function"""

    def test_basic_conversion(self):
        """Test basic content ID to movie ID"""
        result = content_id_to_movie_id("ipx00486")
        assert result == "IPX-486"

    def test_with_digit_prefix(self):
        """Test content ID with digit prefix"""
        result = content_id_to_movie_id("1start422")
        assert result == "START-422"

    def test_with_h_prefix(self):
        """Test content ID with h_ prefix"""
        result = content_id_to_movie_id("h_abc00123")
        # h_ prefix is stripped, letters extracted
        assert "ABC" in result or "abc" in result.lower()


class TestIsValidActressName:
    """Test is_valid_actress_name function"""

    def test_valid_japanese_name(self):
        """Test valid Japanese actress names"""
        assert is_valid_actress_name("桜もも") is True
        assert is_valid_actress_name("明日花キララ") is True

    def test_valid_english_name(self):
        """Test valid English actress names"""
        assert is_valid_actress_name("Momo Sakura") is True
        assert is_valid_actress_name("Kirara Asuka") is True

    def test_rejects_promotional_markers(self):
        """Test rejection of promotional markers"""
        assert is_valid_actress_name("★特別出演★") is False
        assert is_valid_actress_name("☆新人デビュー☆") is False

    def test_rejects_purchase_text(self):
        """Test rejection of purchase-related text"""
        assert is_valid_actress_name("商品ご購入はこちら") is False
        assert is_valid_actress_name("こちらからダウンロード") is False

    def test_rejects_urls(self):
        """Test rejection of URLs"""
        assert is_valid_actress_name("www.example.com") is False
        assert is_valid_actress_name("https://test.jp") is False

    def test_rejects_too_long(self):
        """Test rejection of overly long strings"""
        assert is_valid_actress_name("A" * 50) is False

    def test_rejects_numbers_only(self):
        """Test rejection of numbers only"""
        assert is_valid_actress_name("12345") is False

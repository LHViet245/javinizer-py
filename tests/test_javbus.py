"""Tests for JavBus scraper"""

from datetime import date
from unittest.mock import Mock

from javinizer.scrapers.javbus import JavBusScraper


class TestJavBusScraper:
    """Test JavBusScraper functionality"""

    def test_scraper_name(self):
        """Test scraper has correct name"""
        scraper = JavBusScraper()
        assert scraper.name == "javbus"

    def test_language_urls(self):
        """Test different language URLs"""
        en_scraper = JavBusScraper(language="en")
        assert en_scraper.base_url == "https://www.javbus.com"

        ja_scraper = JavBusScraper(language="ja")
        assert ja_scraper.base_url == "https://www.javbus.com/ja"

        zh_scraper = JavBusScraper(language="zh")
        assert zh_scraper.base_url == "https://www.javbus.com/zh"

    def test_get_search_url(self):
        """Test search URL generation"""
        scraper = JavBusScraper()
        
        url = scraper.get_search_url("IPX-486")
        assert url == "https://www.javbus.com/IPX-486"
        
        # Test normalization
        url = scraper.get_search_url("ipx 486")
        assert url == "https://www.javbus.com/IPX-486"

    def test_extract_id(self):
        """Test ID extraction from HTML"""
        scraper = JavBusScraper()
        
        html = '<span style="color:#CC0000;">IPX-486</span>'
        movie_id = scraper._extract_id(html)
        assert movie_id == "IPX-486"

    def test_extract_title(self):
        """Test title extraction"""
        scraper = JavBusScraper()
        
        html = '<h3>IPX-486 Beautiful Actress Title</h3>'
        title = scraper._extract_title(html)
        assert title == "Beautiful Actress Title"

    def test_extract_date(self):
        """Test date extraction"""
        scraper = JavBusScraper()
        
        html = '>Release Date:</span> 2024-01-15'
        extracted_date = scraper._extract_date(html)
        assert extracted_date == date(2024, 1, 15)

    def test_extract_runtime(self):
        """Test runtime extraction"""
        scraper = JavBusScraper()
        
        html = '>Length:</span> 120min'
        runtime = scraper._extract_runtime(html)
        assert runtime == 120

    def test_extract_genres(self):
        """Test genre extraction"""
        scraper = JavBusScraper()
        
        html = '''
        <span class="genre"><a href="/genre/1">Beautiful Girl</a></span>
        <span class="genre"><a href="/genre/2">Featured Actress</a></span>
        '''
        genres = scraper._extract_genres(html)
        assert "Beautiful Girl" in genres
        assert "Featured Actress" in genres

    def test_extract_cover(self):
        """Test cover URL extraction"""
        scraper = JavBusScraper()
        
        html = '<a class="bigImage" href="https://example.com/cover.jpg">'
        cover = scraper._extract_cover(html)
        assert cover == "https://example.com/cover.jpg"

    def test_is_japanese(self):
        """Test Japanese text detection"""
        scraper = JavBusScraper()
        
        assert scraper._is_japanese("桃乃木かな")
        assert scraper._is_japanese("西宮ゆめ")
        assert not scraper._is_japanese("Kana Momonogi")
        assert not scraper._is_japanese("Test Name")

    def test_parse_html_with_mocked_content(self):
        """Test full HTML parsing with mocked content"""
        scraper = JavBusScraper()
        
        html = '''
        <div class="container">
            <div class="movie">
                <h3>IPX-486 Test Movie Title</h3>
                <span style="color:#CC0000;">IPX-486</span>
                >Release Date:</span> 2024-01-15
                >Length:</span> 120min
                >Studio:</span> <a href="/studio/1">Test Studio</a>
                <span class="genre"><a href="/genre/1">Beautiful Girl</a></span>
                <a class="bigImage" href="https://example.com/cover.jpg">
            </div>
        </div>
        '''
        
        metadata = scraper._parse_html(html, "https://www.javbus.com/IPX-486")
        
        assert metadata is not None
        assert metadata.id == "IPX-486"
        assert metadata.title == "Test Movie Title"
        assert metadata.release_date == date(2024, 1, 15)
        assert metadata.runtime == 120
        assert "Beautiful Girl" in metadata.genres
        assert metadata.cover_url == "https://example.com/cover.jpg"
        assert metadata.source == "javbus"


class TestJavBusScraperNetwork:
    """Test JavBusScraper with mocked network responses"""

    def test_scrape_with_mocked_client(self):
        """Test scrape method with mocked HTTP client"""
        scraper = JavBusScraper()
        
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <div class="container">
            <div class="movie">
                <h3>IPX-486 Test Title</h3>
                <span style="color:#CC0000;">IPX-486</span>
            </div>
        </div>
        '''
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        
        # Set the mocked client - JavBusScraper uses _curl_client
        scraper._curl_client = mock_client
        
        result = scraper.scrape("https://www.javbus.com/IPX-486")
        
        assert result is not None
        assert result.id == "IPX-486"
        assert "Test Title" in result.title


"""Tests for MGStage scraper"""

from datetime import date
from unittest.mock import Mock

from javinizer.scrapers.mgstage import MGStageScraper
from javinizer.models import ProxyConfig


class TestMGStageScraper:
    """Test MGStageScraper functionality"""

    def test_scraper_name(self):
        """Test scraper has correct name"""
        scraper = MGStageScraper()
        assert scraper.name == "mgstage"

    def test_base_url(self):
        """Test base URL is correct"""
        scraper = MGStageScraper()
        assert scraper.base_url == "https://www.mgstage.com"

    def test_age_check_cookie(self):
        """Test age verification cookie is set"""
        scraper = MGStageScraper()
        assert "adc" in scraper.cookies
        assert scraper.cookies["adc"] == "1"

    def test_cookies_merge(self):
        """Test custom cookies are merged with age check cookie"""
        custom_cookies = {"session": "abc123"}
        scraper = MGStageScraper(cookies=custom_cookies)
        
        assert "adc" in scraper.cookies
        assert "session" in scraper.cookies
        assert scraper.cookies["session"] == "abc123"

    def test_proxy_config(self):
        """Test proxy configuration"""
        proxy = ProxyConfig(enabled=True, url="socks5://japan:1080")
        scraper = MGStageScraper(proxy=proxy)
        
        assert scraper.proxy is not None
        assert scraper.proxy.enabled is True
        assert scraper.proxy.url == "socks5://japan:1080"

    def test_get_search_url(self):
        """Test search URL generation"""
        scraper = MGStageScraper()
        
        url = scraper.get_search_url("SIRO-5000")
        assert "cSearch.php" in url
        assert "search_word=SIRO-5000" in url
        
        # Test normalization (trimming only, case might vary but search_word usually kept)
        url = scraper.get_search_url(" siro-5000 ")
        assert "siro-5000" in url or "SIRO-5000" in url

    def test_extract_id_from_url(self):
        """Test ID extraction from URL"""
        scraper = MGStageScraper()
        
        movie_id = scraper._extract_id("", "/product/product_detail/SIRO-5000/")
        assert movie_id == "SIRO-5000"

    def test_extract_id_from_html(self):
        """Test ID extraction from HTML"""
        scraper = MGStageScraper()
        
        html = '>品番：</th><td class="data">SIRO-5000</td>'
        movie_id = scraper._extract_id(html, "")
        assert movie_id == "SIRO-5000"

    def test_extract_title(self):
        """Test title extraction"""
        scraper = MGStageScraper()
        
        html = '<h1 class="tag">テスト動画タイトル</h1>'
        title = scraper._extract_title(html)
        assert title == "テスト動画タイトル"

    def test_extract_date(self):
        """Test date extraction"""
        scraper = MGStageScraper()
        
        html = '>配信開始日：</th><td class="data">2024/01/15</td>'
        extracted_date = scraper._extract_date(html)
        assert extracted_date == date(2024, 1, 15)

    def test_extract_runtime(self):
        """Test runtime extraction"""
        scraper = MGStageScraper()
        
        html = '>収録時間：</th><td class="data">120分</td>'
        runtime = scraper._extract_runtime(html)
        assert runtime == 120

    def test_extract_genres(self):
        """Test genre extraction"""
        scraper = MGStageScraper()
        
        html = '''
        <th>ジャンル：</th>
        <td>
            <a href="/genre/1">素人</a>
            <a href="/genre/2">美少女</a>
        </td>
        '''
        genres = scraper._extract_genres(html)
        assert "素人" in genres
        assert "美少女" in genres

    def test_extract_cover(self):
        """Test cover URL extraction"""
        scraper = MGStageScraper()
        
        html = '<a href="https://example.com/cover.jpg" class="sample_image">'
        cover = scraper._extract_cover(html)
        assert cover == "https://example.com/cover.jpg"

    def test_is_valid_movie_page(self):
        """Test movie page validation"""
        scraper = MGStageScraper()
        
        valid_html = '<div class="common_detail_cover">'
        assert scraper._is_valid_movie_page(valid_html)
        
        invalid_html = '<div class="error">Not found</div>'
        assert not scraper._is_valid_movie_page(invalid_html)

    def test_parse_html_with_mocked_content(self):
        """Test full HTML parsing with mocked content"""
        scraper = MGStageScraper()
        
        html = '''
        <div class="common_detail_cover">
            <h1 class="tag">テスト動画</h1>
            <th>品番：</th><td class="data">SIRO-5000</td>
            <th>配信開始日：</th><td class="data">2024/01/15</td>
            <th>収録時間：</th><td class="data">90分</td>
            <th>メーカー：</th><td><a href="#">テストメーカー</a></td>
            <th>ジャンル：</th><td><a href="/genre/1">素人</a></td>
            <a href="https://example.com/cover.jpg" class="sample_image">
        </div>
        '''
        
        metadata = scraper._parse_html(html, "/product/product_detail/SIRO-5000/")
        
        assert metadata is not None
        assert metadata.id == "SIRO-5000"
        assert metadata.title == "テスト動画"
        assert metadata.release_date == date(2024, 1, 15)
        assert metadata.runtime == 90
        assert metadata.maker == "テストメーカー"
        assert "素人" in metadata.genres
        assert metadata.cover_url == "https://example.com/cover.jpg"
        assert metadata.source == "mgstage"


class TestMGStageScraperNetwork:
    """Test MGStageScraper with mocked network responses"""

    def test_scrape_with_mocked_client(self):
        """Test scrape method with mocked HTTP client"""
        scraper = MGStageScraper()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        <div class="common_detail_cover">
            <h1 class="tag">テスト</h1>
            >品番：</th><td class="data">TEST-001</td>
        </div>
        '''
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        
        scraper._client = mock_client
        
        result = scraper.scrape("https://www.mgstage.com/product/product_detail/TEST-001/")
        
        assert result is not None
        assert result.id == "TEST-001"
        assert "テスト" in result.title

    def test_get_movie_url_with_mocked_client(self):
        """Test get_movie_url with mocked HTTP client"""
        scraper = MGStageScraper()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<div class="common_detail_cover">Valid page</div>'
        mock_response.url = "https://www.mgstage.com/product/product_detail/TEST-001/"
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        
        scraper._client = mock_client
        
        url = scraper.get_movie_url("TEST-001")
        
        assert url is not None
        assert "TEST-001" in url

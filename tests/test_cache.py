# File: tests/test_cache.py
"""Tests for SQLite cache manager"""

import pytest
from pathlib import Path
from datetime import date
import tempfile

from javinizer.cache.manager import CacheManager, CacheConfig
from javinizer.models import MovieMetadata, Actress, Rating


@pytest.fixture
def temp_cache():
    """Create a temporary cache for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = CacheConfig(
            db_path=Path(tmpdir) / "test_cache.db",
            ttl_days=7,
            enabled=True,
        )
        cache = CacheManager(config)
        yield cache
        cache.close()


@pytest.fixture
def sample_metadata() -> MovieMetadata:
    """Sample metadata for testing."""
    return MovieMetadata(
        id="IPX-486",
        content_id="ipx00486",
        title="Test Movie Title",
        original_title="テスト映画",
        description="Test description",
        release_date=date(2024, 1, 15),
        runtime=120,
        maker="Test Studio",
        actresses=[
            Actress(
                first_name="Momo",
                last_name="Sakura",
                japanese_name="桜もも",
            )
        ],
        genres=["Beautiful Girl", "Featured Actress"],
        rating=Rating(rating=8.5, votes=100),
        cover_url="https://example.com/cover.jpg",
        source="test",
    )


class TestCacheConfig:
    """Test CacheConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = CacheConfig()
        assert config.ttl_days == 30
        assert config.enabled is True
        assert config.max_entries == 0

    def test_custom_values(self):
        """Test custom configuration"""
        config = CacheConfig(
            db_path=Path("custom.db"),
            ttl_days=14,
            enabled=False,
        )
        assert config.db_path == Path("custom.db")
        assert config.ttl_days == 14
        assert config.enabled is False


class TestCacheManager:
    """Test CacheManager class"""

    def test_get_not_found_returns_none(self, temp_cache):
        """Test getting non-existent entry returns None"""
        result = temp_cache.get("NONEXISTENT-123", "dmm")
        assert result is None

    def test_set_and_get(self, temp_cache, sample_metadata):
        """Test storing and retrieving metadata"""
        # Store
        success = temp_cache.set("IPX-486", "r18dev", sample_metadata)
        assert success is True
        
        # Retrieve
        cached = temp_cache.get("IPX-486", "r18dev")
        assert cached is not None
        assert cached.id == "IPX-486"
        assert cached.title == "Test Movie Title"
        assert len(cached.actresses) == 1

    def test_case_insensitive_lookup(self, temp_cache, sample_metadata):
        """Test that movie ID lookup is case-insensitive"""
        temp_cache.set("ipx-486", "dmm", sample_metadata)
        
        # Should find with uppercase
        cached = temp_cache.get("IPX-486", "dmm")
        assert cached is not None

    def test_different_sources_separate(self, temp_cache, sample_metadata):
        """Test that different sources are stored separately"""
        # Store with two sources
        temp_cache.set("IPX-486", "dmm", sample_metadata)
        
        modified = sample_metadata.model_copy()
        modified.title = "Modified Title"
        temp_cache.set("IPX-486", "r18dev", modified)
        
        # Retrieve both
        dmm_cached = temp_cache.get("IPX-486", "dmm")
        r18_cached = temp_cache.get("IPX-486", "r18dev")
        
        assert dmm_cached.title == "Test Movie Title"
        assert r18_cached.title == "Modified Title"

    def test_invalidate_single_source(self, temp_cache, sample_metadata):
        """Test invalidating a specific source"""
        temp_cache.set("IPX-486", "dmm", sample_metadata)
        temp_cache.set("IPX-486", "r18dev", sample_metadata)
        
        # Invalidate only dmm
        count = temp_cache.invalidate("IPX-486", "dmm")
        assert count == 1
        
        # r18dev should still exist
        assert temp_cache.get("IPX-486", "dmm") is None
        assert temp_cache.get("IPX-486", "r18dev") is not None

    def test_invalidate_all_sources(self, temp_cache, sample_metadata):
        """Test invalidating all sources for a movie"""
        temp_cache.set("IPX-486", "dmm", sample_metadata)
        temp_cache.set("IPX-486", "r18dev", sample_metadata)
        
        count = temp_cache.invalidate("IPX-486")
        assert count == 2
        
        assert temp_cache.get("IPX-486", "dmm") is None
        assert temp_cache.get("IPX-486", "r18dev") is None

    def test_get_stats(self, temp_cache, sample_metadata):
        """Test cache statistics"""
        # Initial stats
        stats = temp_cache.get_stats()
        assert stats["enabled"] is True
        assert stats["total_entries"] == 0
        
        # Add entries
        temp_cache.set("IPX-486", "dmm", sample_metadata)
        temp_cache.set("SSNI-123", "dmm", sample_metadata)
        
        # Get to increment hit count
        temp_cache.get("IPX-486", "dmm")
        
        stats = temp_cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["total_hits"] == 1

    def test_clear(self, temp_cache, sample_metadata):
        """Test clearing all cache entries"""
        temp_cache.set("IPX-486", "dmm", sample_metadata)
        temp_cache.set("SSNI-123", "dmm", sample_metadata)
        
        count = temp_cache.clear()
        assert count == 2
        
        stats = temp_cache.get_stats()
        assert stats["total_entries"] == 0

    def test_disabled_cache_returns_none(self, sample_metadata):
        """Test that disabled cache always returns None"""
        config = CacheConfig(enabled=False)
        cache = CacheManager(config)
        
        cache.set("IPX-486", "dmm", sample_metadata)
        result = cache.get("IPX-486", "dmm")
        
        assert result is None

    def test_context_manager(self, sample_metadata):
        """Test context manager usage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = CacheConfig(
                db_path=Path(tmpdir) / "test.db",
                enabled=True,
            )
            
            with CacheManager(config) as cache:
                cache.set("IPX-486", "dmm", sample_metadata)
                assert cache.get("IPX-486", "dmm") is not None

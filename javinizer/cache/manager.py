# File: javinizer/cache/manager.py
"""SQLite-based metadata cache for scraped data"""

import json
import sqlite3
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from javinizer.models import MovieMetadata
from javinizer.logger import get_logger

logger = get_logger(__name__)

# Cache schema version for migrations
SCHEMA_VERSION = 1


@dataclass
class CacheConfig:
    """Configuration for metadata cache.

    Attributes:
        db_path: Path to SQLite database file
        ttl_days: Time-to-live for cached entries in days
        enabled: Whether caching is enabled
        max_entries: Maximum number of entries (0 = unlimited)
    """

    db_path: Path = field(default_factory=lambda: Path("cache/metadata.db"))
    ttl_days: int = 30
    enabled: bool = True
    max_entries: int = 0  # 0 = unlimited


class CacheManager:
    """SQLite-based cache for movie metadata.

    Provides persistent caching of scraped metadata to avoid redundant
    network requests and speed up repeated lookups.

    Example:
        cache = CacheManager(CacheConfig(db_path=Path("cache.db")))

        # Try cache first
        metadata = cache.get("IPX-486", "r18dev")
        if not metadata:
            metadata = scraper.find("IPX-486")
            cache.set("IPX-486", "r18dev", metadata)
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager.

        Args:
            config: Cache configuration (uses defaults if None)
        """
        self.config = config or CacheConfig()
        self._conn: Optional[sqlite3.Connection] = None

        if self.config.enabled:
            self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with schema."""
        # Ensure parent directory exists
        self.config.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(
            str(self.config.db_path),
            check_same_thread=False,  # Allow multi-thread access
        )
        self._conn.row_factory = sqlite3.Row

        # Create tables
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
            
            CREATE TABLE IF NOT EXISTS metadata_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id TEXT NOT NULL,
                source TEXT NOT NULL,
                data_json TEXT NOT NULL,
                data_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                UNIQUE(movie_id, source)
            );
            
            CREATE INDEX IF NOT EXISTS idx_cache_lookup
            ON metadata_cache(movie_id, source);
            
            CREATE INDEX IF NOT EXISTS idx_cache_expires
            ON metadata_cache(expires_at);
        """)

        # Set schema version
        cursor = self._conn.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        if not row:
            self._conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,)
            )

        self._conn.commit()
        logger.debug(f"Cache initialized at {self.config.db_path}")

    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        try:
            yield self._conn
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            raise e

    def _compute_hash(self, data: str) -> str:
        """Compute hash of data for change detection."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get(self, movie_id: str, source: str) -> Optional[MovieMetadata]:
        """Retrieve cached metadata.

        Args:
            movie_id: Movie ID (e.g., "IPX-486")
            source: Scraper source name (e.g., "r18dev", "dmm")

        Returns:
            Cached MovieMetadata if found and not expired, None otherwise
        """
        if not self.config.enabled or not self._conn:
            return None

        movie_id = movie_id.upper()
        now = datetime.now(timezone.utc).isoformat()

        cursor = self._conn.execute(
            """
            SELECT data_json, expires_at
            FROM metadata_cache
            WHERE movie_id = ? AND source = ? AND expires_at > ?
        """,
            (movie_id, source, now),
        )

        row = cursor.fetchone()
        if not row:
            return None

        try:
            data = json.loads(row["data_json"])
            metadata = MovieMetadata.model_validate(data)

            # Update hit count
            self._conn.execute(
                """
                UPDATE metadata_cache
                SET hit_count = hit_count + 1
                WHERE movie_id = ? AND source = ?
            """,
                (movie_id, source),
            )
            self._conn.commit()

            logger.debug(f"Cache hit: {movie_id} from {source}")
            return metadata

        except Exception as e:
            logger.warning(f"Failed to deserialize cached data: {e}")
            return None

    def set(
        self,
        movie_id: str,
        source: str,
        metadata: MovieMetadata,
        ttl_days: Optional[int] = None,
    ) -> bool:
        """Store metadata in cache.

        Args:
            movie_id: Movie ID
            source: Scraper source name
            metadata: Metadata to cache
            ttl_days: Override TTL for this entry

        Returns:
            True if stored successfully
        """
        if not self.config.enabled or not self._conn:
            return False

        movie_id = movie_id.upper()
        ttl = ttl_days or self.config.ttl_days

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=ttl)

        data_json = metadata.model_dump_json()
        data_hash = self._compute_hash(data_json)

        try:
            with self._transaction():
                self._conn.execute(
                    """
                    INSERT OR REPLACE INTO metadata_cache
                    (movie_id, source, data_json, data_hash, created_at, expires_at, hit_count)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                    (
                        movie_id,
                        source,
                        data_json,
                        data_hash,
                        now.isoformat(),
                        expires_at.isoformat(),
                    ),
                )

            logger.debug(
                f"Cached: {movie_id} from {source} (expires: {expires_at.date()})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to cache metadata: {e}")
            return False

    def invalidate(self, movie_id: str, source: Optional[str] = None) -> int:
        """Invalidate cached entries.

        Args:
            movie_id: Movie ID to invalidate
            source: Specific source to invalidate, or None for all sources

        Returns:
            Number of entries invalidated
        """
        if not self.config.enabled or not self._conn:
            return 0

        movie_id = movie_id.upper()

        if source:
            cursor = self._conn.execute(
                """
                DELETE FROM metadata_cache
                WHERE movie_id = ? AND source = ?
            """,
                (movie_id, source),
            )
        else:
            cursor = self._conn.execute(
                """
                DELETE FROM metadata_cache
                WHERE movie_id = ?
            """,
                (movie_id,),
            )

        self._conn.commit()
        count = cursor.rowcount

        if count > 0:
            logger.debug(f"Invalidated {count} cache entries for {movie_id}")

        return count

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        if not self.config.enabled or not self._conn:
            return 0

        now = datetime.now(timezone.utc).isoformat()

        cursor = self._conn.execute(
            """
            DELETE FROM metadata_cache
            WHERE expires_at <= ?
        """,
            (now,),
        )

        self._conn.commit()
        count = cursor.rowcount

        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")

        return count

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache statistics (entries, hits, size, etc.)
        """
        if not self.config.enabled or not self._conn:
            return {"enabled": False}

        cursor = self._conn.execute("""
            SELECT 
                COUNT(*) as total_entries,
                SUM(hit_count) as total_hits,
                SUM(LENGTH(data_json)) as total_size_bytes
            FROM metadata_cache
        """)

        row = cursor.fetchone()

        return {
            "enabled": True,
            "db_path": str(self.config.db_path),
            "total_entries": row["total_entries"] or 0,
            "total_hits": row["total_hits"] or 0,
            "total_size_bytes": row["total_size_bytes"] or 0,
            "ttl_days": self.config.ttl_days,
        }

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        if not self.config.enabled or not self._conn:
            return 0

        cursor = self._conn.execute("DELETE FROM metadata_cache")
        self._conn.commit()
        count = cursor.rowcount

        logger.info(f"Cleared {count} cache entries")
        return count

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "CacheManager":
        return self

    def __exit__(self, *args) -> None:
        self.close()


# Global cache instance
_global_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def configure_cache(config: CacheConfig) -> CacheManager:
    """Configure global cache instance."""
    global _global_cache
    if _global_cache:
        _global_cache.close()
    _global_cache = CacheManager(config)
    return _global_cache

"""
Cache management for HTTP responses and content hashes
Uses SQLite for persistent cache with TTL
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any, Dict
from contextlib import contextmanager

from .config import config


class Cache:
    """SQLite-based cache with TTL support"""
    
    def __init__(self, db_name: str = "pipeline_cache.db"):
        self.db_path = config.cache_dir / db_name
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    content_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # Create index for faster cleanup
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper row factory"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache if not expired"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT value, content_hash, created_at, expires_at
                FROM cache
                WHERE key = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                (key,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "value": json.loads(row["value"]),
                    "content_hash": row["content_hash"],
                    "created_at": row["created_at"],
                    "expires_at": row["expires_at"],
                }
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        content_hash: Optional[str] = None,
        ttl_hours: Optional[int] = None
    ):
        """Set value in cache with optional TTL"""
        ttl_hours = ttl_hours or config.cache_ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, content_hash, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, json.dumps(value), content_hash, expires_at.isoformat())
            )
            conn.commit()
    
    def get_content_hash(self, key: str) -> Optional[str]:
        """Get just the content hash for a key"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT content_hash FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            return row["content_hash"] if row else None
    
    def has_hash_changed(self, key: str, new_hash: str) -> bool:
        """Check if content hash has changed"""
        old_hash = self.get_content_hash(key)
        if old_hash is None:
            return True  # No previous hash = changed
        return old_hash != new_hash
    
    def cleanup(self):
        """Remove expired entries"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < CURRENT_TIMESTAMP"
            )
            conn.commit()
            return cursor.rowcount
    
    def clear(self):
        """Clear all cache entries"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            expired = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at < CURRENT_TIMESTAMP"
            ).fetchone()[0]
            return {
                "total_entries": total,
                "expired_entries": expired,
                "valid_entries": total - expired,
            }


def compute_content_hash(content: str, algorithm: str = "sha256") -> str:
    """Compute hash of content for change detection"""
    if algorithm == "sha256":
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def compute_partial_hash(content: str, selectors: list = None) -> str:
    """
    Compute hash of specific parts of content
    For example, only hash the main content area, not headers/footers
    """
    if selectors is None:
        # Default: hash first 5000 chars (to avoid huge pages)
        return compute_content_hash(content[:5000])
    
    # TODO: Implement selector-based hashing
    # This would require parsing HTML and extracting specific elements
    return compute_content_hash(content)


# Global cache instance
cache = Cache()

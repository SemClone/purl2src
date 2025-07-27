"""Simple URL cache implementation."""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache


class URLCache:
    """Simple file-based cache for resolved URLs."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory to store cache files (default: ~/.cache/purl2src)
            ttl: Time to live in seconds (default: 1 hour)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "purl2src"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        
        # In-memory LRU cache for faster access
        self._memory_cache = {}
    
    def _get_cache_path(self, purl: str) -> Path:
        """Get cache file path for a PURL."""
        # Use hash to avoid filesystem issues with special characters
        import hashlib
        purl_hash = hashlib.sha256(purl.encode()).hexdigest()[:16]
        return self.cache_dir / f"{purl_hash}.json"
    
    def get(self, purl: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a PURL.
        
        Args:
            purl: Package URL string
            
        Returns:
            Cached result or None if not found/expired
        """
        # Check memory cache first
        if purl in self._memory_cache:
            entry = self._memory_cache[purl]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
        
        # Check file cache
        cache_path = self._get_cache_path(purl)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r") as f:
                entry = json.load(f)
            
            # Check if expired
            if time.time() - entry["timestamp"] > self.ttl:
                cache_path.unlink()  # Delete expired entry
                return None
            
            # Update memory cache
            self._memory_cache[purl] = entry
            return entry["data"]
            
        except (json.JSONDecodeError, KeyError, IOError):
            # Invalid cache entry, remove it
            cache_path.unlink(missing_ok=True)
            return None
    
    def set(self, purl: str, data: Dict[str, Any]) -> None:
        """
        Cache result for a PURL.
        
        Args:
            purl: Package URL string
            data: Data to cache
        """
        entry = {
            "timestamp": time.time(),
            "data": data
        }
        
        # Update memory cache
        self._memory_cache[purl] = entry
        
        # Write to file cache
        cache_path = self._get_cache_path(purl)
        try:
            with open(cache_path, "w") as f:
                json.dump(entry, f)
        except IOError:
            # Ignore cache write errors
            pass
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()
        
        # Remove all cache files
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
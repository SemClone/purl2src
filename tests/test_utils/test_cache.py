"""Tests for cache utility."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from purl2src.utils.cache import URLCache


class TestURLCache:
    """Test URL cache functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = URLCache(cache_dir=self.temp_dir, ttl=3600)

        self.test_purl = "pkg:npm/express@4.17.1"
        self.test_data = {
            "download_url": "https://registry.npmjs.org/express/-/express-4.17.1.tgz",
            "method": "direct",
            "validated": True,
        }

    def teardown_method(self):
        """Clean up after tests."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization_default_dir(self):
        """Test cache initialization with default directory."""
        cache = URLCache()
        expected_dir = Path.home() / ".cache" / "purl2src"
        assert cache.cache_dir == expected_dir
        assert cache.ttl == 3600

    def test_cache_initialization_custom_dir(self):
        """Test cache initialization with custom directory."""
        custom_dir = self.temp_dir / "custom"
        cache = URLCache(cache_dir=custom_dir, ttl=7200)
        assert cache.cache_dir == custom_dir
        assert cache.ttl == 7200
        assert custom_dir.exists()

    def test_cache_path_generation(self):
        """Test cache file path generation."""
        cache_path = self.cache._get_cache_path(self.test_purl)
        assert cache_path.parent == self.temp_dir
        assert cache_path.suffix == ".json"
        assert len(cache_path.stem) == 16  # SHA256 hash truncated to 16 chars

    def test_cache_path_consistency(self):
        """Test that same PURL generates same cache path."""
        path1 = self.cache._get_cache_path(self.test_purl)
        path2 = self.cache._get_cache_path(self.test_purl)
        assert path1 == path2

    def test_cache_path_different_purls(self):
        """Test that different PURLs generate different cache paths."""
        path1 = self.cache._get_cache_path("pkg:npm/express@4.17.1")
        path2 = self.cache._get_cache_path("pkg:npm/lodash@4.17.21")
        assert path1 != path2

    def test_set_and_get_basic(self):
        """Test basic cache set and get operations."""
        # Initially should return None
        assert self.cache.get(self.test_purl) is None

        # Set data
        self.cache.set(self.test_purl, self.test_data)

        # Should now return the data
        cached_data = self.cache.get(self.test_purl)
        assert cached_data == self.test_data

    def test_memory_cache(self):
        """Test that data is cached in memory."""
        self.cache.set(self.test_purl, self.test_data)

        # Data should be in memory cache
        assert self.test_purl in self.cache._memory_cache
        assert self.cache._memory_cache[self.test_purl]["data"] == self.test_data

        # Should return from memory
        cached_data = self.cache.get(self.test_purl)
        assert cached_data == self.test_data

    def test_file_cache_persistence(self):
        """Test that cache persists to file."""
        self.cache.set(self.test_purl, self.test_data)

        # Check file was created
        cache_path = self.cache._get_cache_path(self.test_purl)
        assert cache_path.exists()

        # Read file directly
        with open(cache_path, "r") as f:
            file_data = json.load(f)

        assert file_data["data"] == self.test_data
        assert "timestamp" in file_data

    def test_cache_across_instances(self):
        """Test cache persistence across different cache instances."""
        # Set data with first instance
        self.cache.set(self.test_purl, self.test_data)

        # Create new cache instance with same directory
        new_cache = URLCache(cache_dir=self.temp_dir, ttl=3600)

        # Should retrieve data from file
        cached_data = new_cache.get(self.test_purl)
        assert cached_data == self.test_data

    def test_ttl_expiration_memory(self):
        """Test TTL expiration in memory cache."""
        # Use very short TTL
        short_cache = URLCache(cache_dir=self.temp_dir, ttl=1)

        short_cache.set(self.test_purl, self.test_data)

        # Should return data immediately
        assert short_cache.get(self.test_purl) == self.test_data

        # Wait for expiration
        time.sleep(1.1)

        # Should return None after expiration
        assert short_cache.get(self.test_purl) is None

    def test_ttl_expiration_file(self):
        """Test TTL expiration for file cache."""
        # Create cache with short TTL
        short_cache = URLCache(cache_dir=self.temp_dir, ttl=1)
        short_cache.set(self.test_purl, self.test_data)

        # Clear memory cache to force file read
        short_cache._memory_cache.clear()

        # Wait for expiration
        time.sleep(1.1)

        # Should return None and delete expired file
        cache_path = short_cache._get_cache_path(self.test_purl)
        assert short_cache.get(self.test_purl) is None
        assert not cache_path.exists()

    def test_clear_cache(self):
        """Test clearing all cache entries."""
        # Set multiple entries
        purls = ["pkg:npm/express@4.17.1", "pkg:npm/lodash@4.17.21", "pkg:pypi/requests@2.28.0"]

        for purl in purls:
            self.cache.set(purl, {"url": f"https://example.com/{purl}"})

        # Verify entries exist
        for purl in purls:
            assert self.cache.get(purl) is not None
            assert self.cache._get_cache_path(purl).exists()

        # Clear cache
        self.cache.clear()

        # Verify all entries are gone
        assert len(self.cache._memory_cache) == 0
        for purl in purls:
            assert self.cache.get(purl) is None
            assert not self.cache._get_cache_path(purl).exists()

    def test_invalid_cache_file_handling(self):
        """Test handling of invalid cache files."""
        cache_path = self.cache._get_cache_path(self.test_purl)

        # Create invalid JSON file
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            f.write("invalid json content")

        # Should return None and remove invalid file
        assert self.cache.get(self.test_purl) is None
        assert not cache_path.exists()

    def test_missing_timestamp_in_cache_file(self):
        """Test handling of cache file missing timestamp."""
        cache_path = self.cache._get_cache_path(self.test_purl)

        # Create file without timestamp
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump({"data": self.test_data}, f)  # Missing timestamp

        # Should return None and remove invalid file
        assert self.cache.get(self.test_purl) is None
        assert not cache_path.exists()

    def test_io_error_during_set(self):
        """Test handling of IO errors during cache set."""
        # Create cache with read-only directory
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        try:
            readonly_cache = URLCache(cache_dir=readonly_dir, ttl=3600)

            # Should not raise exception even if file write fails
            readonly_cache.set(self.test_purl, self.test_data)

            # Memory cache should still work
            assert readonly_cache.get(self.test_purl) == self.test_data

        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_cache_with_special_characters_in_purl(self):
        """Test caching PURLs with special characters."""
        special_purls = [
            "pkg:npm/@angular/core@12.0.0",
            "pkg:maven/org.apache.commons/commons-lang3@3.12.0",
            "pkg:golang/github.com/user/repo@v1.0.0",
            "pkg:pypi/package-with-dashes@1.0.0",
        ]

        for purl in special_purls:
            data = {"url": f"https://example.com/{purl}"}
            self.cache.set(purl, data)
            assert self.cache.get(purl) == data

    def test_large_data_caching(self):
        """Test caching large data structures."""
        large_data = {
            "url": "https://example.com/package.tgz",
            "metadata": {
                "size": 1024000,
                "dependencies": ["dep1", "dep2", "dep3"] * 100,
                "description": "A" * 1000,
            },
            "versions": {f"1.{i}.0": f"url-{i}" for i in range(100)},
        }

        self.cache.set(self.test_purl, large_data)
        cached_data = self.cache.get(self.test_purl)
        assert cached_data == large_data

    @patch("time.time")
    def test_cache_timestamp_precision(self, mock_time):
        """Test cache timestamp handling."""
        # Mock time to specific value
        mock_time.return_value = 1609459200.0  # 2021-01-01 00:00:00

        self.cache.set(self.test_purl, self.test_data)

        # Verify timestamp in file
        cache_path = self.cache._get_cache_path(self.test_purl)
        with open(cache_path, "r") as f:
            file_data = json.load(f)

        assert file_data["timestamp"] == 1609459200.0

    def test_memory_cache_update_on_file_read(self):
        """Test that memory cache is updated when reading from file."""
        # Set data and clear memory cache
        self.cache.set(self.test_purl, self.test_data)
        self.cache._memory_cache.clear()

        # Get should read from file and update memory cache
        cached_data = self.cache.get(self.test_purl)
        assert cached_data == self.test_data
        assert self.test_purl in self.cache._memory_cache

    def test_concurrent_cache_operations(self):
        """Test cache behavior with concurrent-like operations."""
        # Simulate multiple rapid operations
        purls = [f"pkg:npm/package{i}@1.0.0" for i in range(10)]

        # Set all
        for i, purl in enumerate(purls):
            self.cache.set(purl, {"index": i, "url": f"https://example.com/{i}"})

        # Get all
        for i, purl in enumerate(purls):
            data = self.cache.get(purl)
            assert data["index"] == i
            assert data["url"] == f"https://example.com/{i}"

    def test_cache_directory_creation(self):
        """Test cache directory is created if it doesn't exist."""
        nonexistent_dir = self.temp_dir / "nested" / "cache" / "dir"
        assert not nonexistent_dir.exists()

        cache = URLCache(cache_dir=nonexistent_dir)
        assert nonexistent_dir.exists()

    def test_empty_purl_handling(self):
        """Test handling of empty PURL string."""
        empty_purl = ""
        self.cache.set(empty_purl, self.test_data)
        assert self.cache.get(empty_purl) == self.test_data

    def test_none_data_caching(self):
        """Test caching None or empty data."""
        self.cache.set(self.test_purl, None)
        assert self.cache.get(self.test_purl) is None

        self.cache.set(self.test_purl, {})
        assert self.cache.get(self.test_purl) == {}

    def test_cache_file_permissions(self):
        """Test that cache files are created with appropriate permissions."""
        self.cache.set(self.test_purl, self.test_data)
        cache_path = self.cache._get_cache_path(self.test_purl)

        # File should be readable by owner
        assert cache_path.exists()
        assert cache_path.is_file()
        # Note: Specific permission testing is platform-dependent

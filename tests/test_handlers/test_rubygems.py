"""Tests for RubyGems handler."""

import unittest
from unittest.mock import Mock, MagicMock, patch

from purl2src.handlers.rubygems import RubyGemsHandler
from purl2src.parser import Purl
from purl2src.utils.http import HttpClient


class TestRubyGemsHandler(unittest.TestCase):
    """Test RubyGems handler."""

    def setUp(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = RubyGemsHandler(self.http_client)

    def test_is_github_url_valid(self):
        """Test _is_github_url with valid GitHub URLs."""
        assert self.handler._is_github_url("https://github.com/user/repo")
        assert self.handler._is_github_url("http://github.com/user/repo")
        assert self.handler._is_github_url("https://github.com/user/repo.git")

    def test_is_github_url_invalid(self):
        """Test _is_github_url with invalid/malicious URLs."""
        # These should all return False to prevent security issues
        assert not self.handler._is_github_url("https://evil.com/github.com/user/repo")
        assert not self.handler._is_github_url("https://github.com.evil.com/user/repo")
        assert not self.handler._is_github_url("https://evil.com?redirect=github.com")
        assert not self.handler._is_github_url("https://example.com/path/github.com")
        assert not self.handler._is_github_url("ftp://github.com/user/repo")
        assert not self.handler._is_github_url("malformed-url")
        assert not self.handler._is_github_url("")

    def test_build_download_url(self):
        """Test building download URL."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")
        url = self.handler.build_download_url(purl)
        assert url == "https://rubygems.org/downloads/rails-7.0.0.gem"

    def test_build_download_url_no_version(self):
        """Test building download URL without version."""
        purl = Purl(ecosystem="gem", name="rails")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_get_download_url_from_api_with_gem_uri(self):
        """Test API response with gem_uri."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "gem_uri": "https://rubygems.org/downloads/rails-7.0.0.gem"
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://rubygems.org/downloads/rails-7.0.0.gem"

    def test_get_download_url_from_api_with_safe_github_source(self):
        """Test API response with safe GitHub source_code_uri."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "source_code_uri": "https://github.com/rails/rails"
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://github.com/rails/rails.git"

    def test_get_download_url_from_api_with_malicious_source(self):
        """Test API response with malicious source_code_uri containing github.com substring."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "source_code_uri": "https://evil.com/github.com/malicious"
        }

        url = self.handler.get_download_url_from_api(purl)
        # Should return the URL as-is without adding .git since it's not from GitHub
        assert url == "https://evil.com/github.com/malicious"

    def test_get_download_url_from_api_with_safe_github_homepage(self):
        """Test API response with safe GitHub homepage_uri."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {"homepage_uri": "https://github.com/rails/rails"}

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://github.com/rails/rails.git"

    def test_get_download_url_from_api_with_malicious_homepage(self):
        """Test API response with malicious homepage_uri containing github.com substring."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "homepage_uri": "https://evil.com/github.com/malicious"
        }

        url = self.handler.get_download_url_from_api(purl)
        # Should return None since it's not from GitHub and no other URL is available
        assert url is None

    def test_get_fallback_cmd(self):
        """Test getting fallback command."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "gem fetch rails --version 7.0.0"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(ecosystem="gem", name="rails")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_package_manager_cmd(self):
        """Test getting package manager command."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["gem"]

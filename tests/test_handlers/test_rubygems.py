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
        """Test API response with safe GitHub source_code_uri.

        Versionless: a repository URL is only offered when no version was asked
        for, so that is the case where the GitHub host check applies.
        """
        purl = Purl(ecosystem="gem", name="rails")

        self.http_client.get_json.return_value = {
            "source_code_uri": "https://github.com/rails/rails"
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://github.com/rails/rails.git"

    def test_get_download_url_from_api_with_malicious_source(self):
        """Test API response with malicious source_code_uri containing github.com substring.

        Versionless, so the host check is actually reached: a versioned request
        declines a repository URL before inspecting its host, which would let
        this test pass without exercising _is_github_url at all.
        """
        purl = Purl(ecosystem="gem", name="rails")

        self.http_client.get_json.return_value = {
            "source_code_uri": "https://evil.com/github.com/malicious"
        }

        url = self.handler.get_download_url_from_api(purl)
        # Should return None since it's not from GitHub and no other URL is available
        assert url is None

    def test_get_download_url_from_api_with_safe_github_homepage(self):
        """Test API response with safe GitHub homepage_uri.

        Versionless, for the same reason as the source_code_uri case above.
        """
        purl = Purl(ecosystem="gem", name="rails")

        self.http_client.get_json.return_value = {"homepage_uri": "https://github.com/rails/rails"}

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://github.com/rails/rails.git"

    def test_get_download_url_from_api_with_malicious_homepage(self):
        """Test API response with malicious homepage_uri containing github.com substring.

        Versionless, so the host check is actually reached: a versioned request
        declines a repository URL before inspecting its host, which would let
        this test pass without exercising _is_github_url at all.
        """
        purl = Purl(ecosystem="gem", name="rails")

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

    def test_gem_uri_for_another_version_is_not_returned(self):
        """The gems endpoint describes the latest release, which is not what was asked for."""
        purl = Purl(ecosystem="gem", name="rails", version="99.99.99")

        self.http_client.get_json.return_value = {
            "gem_uri": "https://rubygems.org/gems/rails-8.1.3.1.gem",
            "source_code_uri": "https://github.com/rails/rails",
        }

        assert self.handler.get_download_url_from_api(purl) is None

    def test_repository_url_is_not_an_answer_about_a_version(self):
        """A bare clone URL says nothing about the requested version, so it is not returned."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "homepage_uri": "https://github.com/rails/rails",
        }

        assert self.handler.get_download_url_from_api(purl) is None

    def test_missing_version_fails_rather_than_validating_another_version(self):
        """The resolution chain reports failure for a gem version that does not exist.

        Companion to the npm case in #30: the versioned .gem URL 404s, and the API
        level used to answer with the latest gem, which validates.
        """
        purl = Purl(ecosystem="gem", name="rails", version="99.99.99")

        self.http_client.get_json.return_value = {
            "gem_uri": "https://rubygems.org/gems/rails-8.1.3.1.gem",
            "source_code_uri": "https://github.com/rails/rails",
        }
        self.http_client.validate_url.side_effect = lambda url: "99.99.99" not in url

        with patch("shutil.which", return_value=None):
            result = self.handler.get_download_url(purl, validate=True)

        assert result.status == "failed"
        assert result.download_url is None
        assert result.validated is False

    def test_query_string_cannot_spoof_the_version(self):
        """A query ending in the requested filename does not make the URL that gem."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "gem_uri": "https://rubygems.org/downloads/rails-8.1.3.gem?x=/rails-7.0.0.gem",
        }

        assert self.handler.get_download_url_from_api(purl) is None

    def test_query_string_does_not_reject_the_right_version(self):
        """A signed or tracked URL for the requested version is still accepted."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")
        gem_uri = "https://rubygems.org/downloads/rails-7.0.0.gem?token=abc123"

        self.http_client.get_json.return_value = {"gem_uri": gem_uri}

        assert self.handler.get_download_url_from_api(purl) == gem_uri

    def test_fragment_cannot_spoof_the_version(self):
        """A fragment ending in the requested filename is likewise not the gem."""
        purl = Purl(ecosystem="gem", name="rails", version="7.0.0")

        self.http_client.get_json.return_value = {
            "gem_uri": "https://rubygems.org/downloads/rails-8.1.3.gem#/rails-7.0.0.gem",
        }

        assert self.handler.get_download_url_from_api(purl) is None

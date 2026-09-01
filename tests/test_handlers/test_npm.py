"""Tests for NPM handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.npm import NpmHandler
from purl2src.utils.http import HttpClient


class TestNpmHandler:
    """Test NPM handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = NpmHandler(self.http_client)

    def test_build_download_url_simple(self):
        """Test building download URL for simple package."""
        purl = Purl(ecosystem="npm", name="express", version="4.17.1")
        url = self.handler.build_download_url(purl)
        assert url == "https://registry.npmjs.org/express/-/express-4.17.1.tgz"

    def test_build_download_url_scoped(self):
        """Test building download URL for scoped package."""
        purl = Purl(ecosystem="npm", namespace="@angular", name="core", version="12.0.0")
        url = self.handler.build_download_url(purl)
        assert url == "https://registry.npmjs.org/@angular/core/-/core-12.0.0.tgz"

    def test_build_download_url_no_version(self):
        """Test building download URL without version returns None."""
        purl = Purl(ecosystem="npm", name="express")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_get_download_url_from_api(self):
        """Test getting download URL from API."""
        purl = Purl(ecosystem="npm", name="express", version="4.17.1")

        # Mock API response
        self.http_client.get_json.return_value = {
            "versions": {
                "4.17.1": {
                    "dist": {"tarball": "https://registry.npmjs.org/express/-/express-4.17.1.tgz"}
                }
            }
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://registry.npmjs.org/express/-/express-4.17.1.tgz"
        self.http_client.get_json.assert_called_once_with("https://registry.npmjs.org/express")

    def test_get_fallback_cmd(self):
        """Test getting fallback command."""
        purl = Purl(ecosystem="npm", name="express", version="4.17.1")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "npm view express@4.17.1 dist.tarball"

    def test_get_fallback_cmd_scoped(self):
        """Test getting fallback command for scoped package."""
        purl = Purl(ecosystem="npm", namespace="@angular", name="core", version="12.0.0")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "npm view @angular/core@12.0.0 dist.tarball"

    def test_is_package_manager_available(self):
        """Test checking if package manager is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/npm"
            assert self.handler.is_package_manager_available() is True

            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output(self):
        """Test parsing npm view output."""
        output = "https://registry.npmjs.org/express/-/express-4.17.1.tgz\n"
        url = self.handler.parse_fallback_output(output)
        assert url == "https://registry.npmjs.org/express/-/express-4.17.1.tgz"

        # Test invalid output
        output = "Not a URL"
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_get_download_url_from_api_missing_version_is_not_substituted(self):
        """A version the registry does not carry resolves to nothing, not to latest."""
        purl = Purl(ecosystem="npm", name="express", version="99.99.99")

        self.http_client.get_json.return_value = {
            "dist-tags": {"latest": "5.2.1"},
            "versions": {
                "5.2.1": {
                    "dist": {"tarball": "https://registry.npmjs.org/express/-/express-5.2.1.tgz"}
                }
            },
        }

        assert self.handler.get_download_url_from_api(purl) is None

    def test_get_download_url_from_api_without_version_uses_latest(self):
        """With no version asked for, latest is the answer to the question posed."""
        purl = Purl(ecosystem="npm", name="express")

        self.http_client.get_json.return_value = {
            "dist-tags": {"latest": "5.2.1"},
            "versions": {
                "5.2.1": {
                    "dist": {"tarball": "https://registry.npmjs.org/express/-/express-5.2.1.tgz"}
                }
            },
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://registry.npmjs.org/express/-/express-5.2.1.tgz"

    def test_missing_version_fails_rather_than_validating_another_version(self):
        """The whole resolution chain reports failure for a version that does not exist.

        Regression test for #30: the direct URL 404s, and the API level used to
        answer with the latest tarball, which validates and so was reported as a
        validated result for a coordinate the registry never had.
        """
        purl = Purl(ecosystem="npm", name="express", version="99.99.99")

        self.http_client.get_json.return_value = {
            "dist-tags": {"latest": "5.2.1"},
            "versions": {
                "5.2.1": {
                    "dist": {"tarball": "https://registry.npmjs.org/express/-/express-5.2.1.tgz"}
                }
            },
        }
        # Only the real 5.2.1 tarball resolves; the 99.99.99 URL 404s.
        self.http_client.validate_url.side_effect = lambda url: "5.2.1" in url

        with patch("shutil.which", return_value=None):
            result = self.handler.get_download_url(purl, validate=True)

        assert result.status == "failed"
        assert result.download_url is None
        assert result.validated is False

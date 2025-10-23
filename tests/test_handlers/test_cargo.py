"""Tests for Cargo handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.cargo import CargoHandler
from purl2src.utils.http import HttpClient


class TestCargoHandler:
    """Test Cargo handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = CargoHandler(self.http_client)

    def test_build_download_url_with_version(self):
        """Test building download URL with version."""
        purl = Purl(ecosystem="cargo", name="serde", version="1.0.130")
        url = self.handler.build_download_url(purl)
        assert url == "https://crates.io/api/v1/crates/serde/1.0.130/download"

    def test_build_download_url_no_version(self):
        """Test building download URL without version returns None."""
        purl = Purl(ecosystem="cargo", name="serde")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_complex_name(self):
        """Test building download URL with complex package name."""
        purl = Purl(ecosystem="cargo", name="tokio-util", version="0.6.8")
        url = self.handler.build_download_url(purl)
        assert url == "https://crates.io/api/v1/crates/tokio-util/0.6.8/download"

    def test_get_download_url_from_api(self):
        """Test that API method returns None (not implemented)."""
        purl = Purl(ecosystem="cargo", name="serde", version="1.0.130")
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd(self):
        """Test getting fallback command."""
        purl = Purl(ecosystem="cargo", name="serde", version="1.0.130")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "cargo search serde --limit 1"

    def test_get_fallback_cmd_special_chars(self):
        """Test getting fallback command with special characters."""
        purl = Purl(ecosystem="cargo", name="my-crate", version="1.0.0")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "cargo search my-crate --limit 1"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(ecosystem="cargo", name="serde")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "cargo search serde --limit 1"

    def test_get_package_manager_cmd(self):
        """Test getting package manager command."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["cargo"]

    def test_is_package_manager_available(self):
        """Test checking if package manager is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/cargo"
            assert self.handler.is_package_manager_available() is True

            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output(self):
        """Test parsing cargo search output."""
        # Cargo search doesn't provide download URLs
        output = 'serde = "1.0.130"    # A generic serialization/deserialization framework'
        url = self.handler.parse_fallback_output(output)
        assert url is None

        # Test empty output
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_multiline(self):
        """Test parsing multiline cargo search output."""
        output = """serde = "1.0.130"    # A generic serialization/deserialization framework
serde_derive = "1.0.130"    # Macros 1.1 implementation of #[derive(Serialize, Deserialize)]
serde_json = "1.0.68"    # A JSON serialization file format"""

        url = self.handler.parse_fallback_output(output)
        assert url is None

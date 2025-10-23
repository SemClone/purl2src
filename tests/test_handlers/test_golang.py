"""Tests for GoLang handler."""

import json
import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.golang import GoLangHandler
from purl2src.utils.http import HttpClient


class TestGoLangHandler:
    """Test GoLang handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = GoLangHandler(self.http_client)

    def test_build_download_url_with_namespace(self):
        """Test building download URL with namespace."""
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/gorilla",
            name="mux",
            version="v1.8.0"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://proxy.golang.org/github.com%2Fgorilla%2Fmux/@v/v1.8.0.zip"

    def test_build_download_url_without_namespace(self):
        """Test building download URL without namespace."""
        purl = Purl(
            ecosystem="golang",
            name="testify",
            version="v1.7.0"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://proxy.golang.org/testify/@v/v1.7.0.zip"

    def test_build_download_url_no_version(self):
        """Test building download URL without version returns None."""
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/gorilla",
            name="mux"
        )
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_complex_namespace(self):
        """Test building download URL with complex namespace."""
        purl = Purl(
            ecosystem="golang",
            namespace="go.uber.org/zap",
            name="zapcore",
            version="v1.19.1"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://proxy.golang.org/go.uber.org%2Fzap%2Fzapcore/@v/v1.19.1.zip"

    def test_build_download_url_special_chars_encoding(self):
        """Test URL encoding of special characters in module path."""
        purl = Purl(
            ecosystem="golang",
            namespace="k8s.io/api",
            name="core",
            version="v0.22.0"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://proxy.golang.org/k8s.io%2Fapi%2Fcore/@v/v0.22.0.zip"

    def test_get_download_url_from_api_with_namespace_success(self):
        """Test API method with namespace - success."""
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/gorilla",
            name="mux",
            version="v1.8.0"
        )

        # Mock successful API response
        self.http_client.get.return_value = MagicMock()

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://proxy.golang.org/github.com%2Fgorilla%2Fmux/@v/v1.8.0.zip"

        # Verify API call was made to info endpoint
        self.http_client.get.assert_called_once_with(
            "https://proxy.golang.org/github.com%2Fgorilla%2Fmux/@v/v1.8.0.info"
        )

    def test_get_download_url_from_api_without_namespace_success(self):
        """Test API method without namespace - success."""
        purl = Purl(
            ecosystem="golang",
            name="testify",
            version="v1.7.0"
        )

        # Mock successful API response
        self.http_client.get.return_value = MagicMock()

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://proxy.golang.org/testify/@v/v1.7.0.zip"

        # Verify API call was made
        self.http_client.get.assert_called_once_with(
            "https://proxy.golang.org/testify/@v/v1.7.0.info"
        )

    def test_get_download_url_from_api_failure(self):
        """Test API method with failure."""
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/gorilla",
            name="mux",
            version="v1.8.0"
        )

        # Mock API failure
        self.http_client.get.side_effect = Exception("API Error")

        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_with_namespace(self):
        """Test getting fallback command with namespace."""
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/gorilla",
            name="mux",
            version="v1.8.0"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "go mod download -json github.com/gorilla/mux@v1.8.0"

    def test_get_fallback_cmd_without_namespace(self):
        """Test getting fallback command without namespace."""
        purl = Purl(
            ecosystem="golang",
            name="testify",
            version="v1.7.0"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "go mod download -json testify@v1.7.0"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/gorilla",
            name="mux"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_package_manager_cmd(self):
        """Test getting package manager command."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["go"]

    def test_is_package_manager_available(self):
        """Test checking if package manager is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/go"
            assert self.handler.is_package_manager_available() is True

            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output_success(self):
        """Test parsing go mod download JSON output."""
        output_data = {
            "Path": "github.com/gorilla/mux",
            "Version": "v1.8.0",
            "Info": "/go/pkg/mod/cache/download/github.com/gorilla/mux/@v/v1.8.0.info",
            "GoMod": "/go/pkg/mod/cache/download/github.com/gorilla/mux/@v/v1.8.0.mod",
            "Zip": "/go/pkg/mod/cache/download/github.com/gorilla/mux/@v/v1.8.0.zip",
            "Dir": "/go/pkg/mod/github.com/gorilla/mux@v1.8.0",
            "Sum": "h1:i40aqfkR1h2SlN9hojwV5ZA91wcXFOvI",
            "GoModSum": "h1:DVmS30j4vzqLsgCCF"
        }
        output = json.dumps(output_data)

        url = self.handler.parse_fallback_output(output)
        assert url == "https://proxy.golang.org/github.com%2Fgorilla%2Fmux/@v/v1.8.0.zip"

    def test_parse_fallback_output_missing_fields(self):
        """Test parsing go mod download JSON output with missing fields."""
        output_data = {
            "Path": "github.com/gorilla/mux"
            # Missing Version field
        }
        output = json.dumps(output_data)

        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_invalid_json(self):
        """Test parsing invalid JSON output."""
        output = "This is not valid JSON"

        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_empty(self):
        """Test parsing empty output."""
        output = ""

        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_complex_path(self):
        """Test parsing output with complex module path."""
        output_data = {
            "Path": "k8s.io/api/core/v1",
            "Version": "v0.22.0"
        }
        output = json.dumps(output_data)

        url = self.handler.parse_fallback_output(output)
        assert url == "https://proxy.golang.org/k8s.io%2Fapi%2Fcore%2Fv1/@v/v0.22.0.zip"

    def test_encoding_edge_cases(self):
        """Test URL encoding edge cases."""
        # Test module path with multiple slashes and dots
        purl = Purl(
            ecosystem="golang",
            namespace="gopkg.in/yaml.v2",
            name="yaml",
            version="v2.4.0"
        )
        url = self.handler.build_download_url(purl)
        # gopkg.in/yaml.v2/yaml should be encoded properly
        assert url == "https://proxy.golang.org/gopkg.in%2Fyaml.v2%2Fyaml/@v/v2.4.0.zip"

    def test_version_formats(self):
        """Test different version formats."""
        # Semantic version
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/user",
            name="repo",
            version="v1.2.3"
        )
        url = self.handler.build_download_url(purl)
        assert "v1.2.3" in url

        # Pre-release version
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/user",
            name="repo",
            version="v1.2.3-beta.1"
        )
        url = self.handler.build_download_url(purl)
        assert "v1.2.3-beta.1" in url

        # Pseudo-version
        purl = Purl(
            ecosystem="golang",
            namespace="github.com/user",
            name="repo",
            version="v0.0.0-20210101000000-abc123def456"
        )
        url = self.handler.build_download_url(purl)
        assert "v0.0.0-20210101000000-abc123def456" in url
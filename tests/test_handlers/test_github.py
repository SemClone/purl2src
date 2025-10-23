"""Tests for GitHub handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.github import GitHubHandler
from purl2src.utils.http import HttpClient


class TestGitHubHandler:
    """Test GitHub handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = GitHubHandler(self.http_client)

    def test_build_download_url_simple_repo(self):
        """Test building download URL for simple repository."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://github.com/rails/rails.git"

    def test_build_download_url_no_namespace(self):
        """Test building download URL without namespace returns None."""
        purl = Purl(ecosystem="github", name="rails")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_with_subpath(self):
        """Test building download URL with subpath."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0",
            subpath="README.md"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://raw.githubusercontent.com/rails/rails/v7.0.0/README.md"

    def test_build_download_url_with_subpath_no_version(self):
        """Test building download URL with subpath but no version uses main."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            subpath="lib/rails.rb"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://raw.githubusercontent.com/rails/rails/main/lib/rails.rb"

    def test_build_download_url_with_subpath_deep_path(self):
        """Test building download URL with deep subpath."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0",
            subpath="activerecord/lib/active_record.rb"
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://raw.githubusercontent.com/rails/rails/v7.0.0/activerecord/lib/active_record.rb"

    def test_get_download_url_from_api_no_namespace(self):
        """Test API method without namespace returns None."""
        purl = Purl(ecosystem="github", name="rails")
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_download_url_from_api_release_success(self):
        """Test API method for release version."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0"
        )

        # Mock successful API response
        self.http_client.get_json.return_value = {
            "tarball_url": "https://api.github.com/repos/rails/rails/tarball/v7.0.0"
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://api.github.com/repos/rails/rails/tarball/v7.0.0"

        # Verify API call
        self.http_client.get_json.assert_called_once_with(
            "https://api.github.com/repos/rails/rails/releases/tags/v7.0.0"
        )

    def test_get_download_url_from_api_release_failure(self):
        """Test API method for release version with API failure."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0"
        )

        # Mock API failure
        self.http_client.get_json.side_effect = Exception("API Error")

        url = self.handler.get_download_url_from_api(purl)
        # Should fallback to archive URL
        assert url == "https://github.com/rails/rails/archive/refs/tags/v7.0.0.tar.gz"

    def test_get_download_url_from_api_branch_main(self):
        """Test API method for main branch."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="main"
        )

        url = self.handler.get_download_url_from_api(purl)
        # Should not try releases API for main/master
        assert url == "https://github.com/rails/rails/archive/refs/tags/main.tar.gz"

        # Verify no API call was made
        self.http_client.get_json.assert_not_called()

    def test_get_download_url_from_api_branch_master(self):
        """Test API method for master branch."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="master"
        )

        url = self.handler.get_download_url_from_api(purl)
        # Should not try releases API for main/master
        assert url == "https://github.com/rails/rails/archive/refs/tags/master.tar.gz"

        # Verify no API call was made
        self.http_client.get_json.assert_not_called()

    def test_get_download_url_from_api_no_version(self):
        """Test API method without version."""
        purl = Purl(ecosystem="github", namespace="rails", name="rails")

        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_with_version(self):
        """Test getting fallback command with version."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/rails/rails.git && cd rails && git checkout v7.0.0"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(ecosystem="github", namespace="rails", name="rails")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/rails/rails.git"

    def test_get_fallback_cmd_no_namespace(self):
        """Test getting fallback command without namespace."""
        purl = Purl(ecosystem="github", name="rails")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_fallback_cmd_complex_names(self):
        """Test getting fallback command with complex names."""
        purl = Purl(
            ecosystem="github",
            namespace="microsoft",
            name="vscode-python",
            version="2021.8.1105767423"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/microsoft/vscode-python.git && cd vscode-python && git checkout 2021.8.1105767423"

    def test_get_package_manager_cmd(self):
        """Test getting package manager command."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["git"]

    def test_is_package_manager_available(self):
        """Test checking if package manager is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/git"
            assert self.handler.is_package_manager_available() is True

            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output(self):
        """Test parsing git output."""
        # Git clone doesn't return download URLs
        output = "Cloning into 'rails'..."
        url = self.handler.parse_fallback_output(output)
        assert url is None

        # Test empty output
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_get_download_url_from_api_release_no_tarball(self):
        """Test API method for release without tarball_url."""
        purl = Purl(
            ecosystem="github",
            namespace="rails",
            name="rails",
            version="v7.0.0"
        )

        # Mock API response without tarball_url
        self.http_client.get_json.return_value = {
            "name": "v7.0.0",
            "tag_name": "v7.0.0"
        }

        url = self.handler.get_download_url_from_api(purl)
        # Should fallback to archive URL
        assert url == "https://github.com/rails/rails/archive/refs/tags/v7.0.0.tar.gz"

    def test_archive_url_format(self):
        """Test that archive URL format is correct."""
        purl = Purl(
            ecosystem="github",
            namespace="user",
            name="repo",
            version="v1.0.0"
        )

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://github.com/user/repo/archive/refs/tags/v1.0.0.tar.gz"
"""Tests for Conda handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.conda import CondaHandler
from purl2src.handlers.base import HandlerError
from purl2src.utils.http import HttpClient


class TestCondaHandler:
    """Test Conda handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = CondaHandler(self.http_client)

    def test_build_download_url_main_channel(self):
        """Test building download URL for main channel."""
        purl = Purl(
            ecosystem="conda",
            name="numpy",
            version="1.21.0",
            qualifiers={
                "build": "py39h89e85a6_0",
                "channel": "main",
                "subdir": "linux-64"
            }
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.anaconda.com/pkgs/main/linux-64/numpy-1.21.0-py39h89e85a6_0.tar.bz2"
        assert url == expected

    def test_build_download_url_defaults_channel(self):
        """Test building download URL for defaults channel."""
        purl = Purl(
            ecosystem="conda",
            name="scipy",
            version="1.7.0",
            qualifiers={
                "build": "py39h89e85a6_0",
                "channel": "defaults",
                "subdir": "linux-64"
            }
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.anaconda.com/pkgs/main/linux-64/scipy-1.7.0-py39h89e85a6_0.tar.bz2"
        assert url == expected

    def test_build_download_url_conda_forge(self):
        """Test building download URL for conda-forge channel."""
        purl = Purl(
            ecosystem="conda",
            name="matplotlib",
            version="3.4.2",
            qualifiers={
                "build": "py39h89e85a6_0",
                "channel": "conda-forge",
                "subdir": "linux-64"
            }
        )
        url = self.handler.build_download_url(purl)
        expected = "https://anaconda.org/conda-forge/matplotlib/3.4.2/download/linux-64/matplotlib-3.4.2-py39h89e85a6_0.tar.bz2"
        assert url == expected

    def test_build_download_url_bioconda(self):
        """Test building download URL for bioconda channel."""
        purl = Purl(
            ecosystem="conda",
            name="samtools",
            version="1.13",
            qualifiers={
                "build": "h8c37831_0",
                "channel": "bioconda",
                "subdir": "linux-64"
            }
        )
        url = self.handler.build_download_url(purl)
        expected = "https://anaconda.org/bioconda/samtools/1.13/download/linux-64/samtools-1.13-h8c37831_0.tar.bz2"
        assert url == expected

    def test_build_download_url_no_version(self):
        """Test building download URL without version."""
        purl = Purl(
            ecosystem="conda",
            name="numpy",
            qualifiers={
                "build": "py39h89e85a6_0",
                "channel": "main",
                "subdir": "linux-64"
            }
        )
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_missing_build(self):
        """Test error when build qualifier is missing."""
        purl = Purl(
            ecosystem="conda",
            name="numpy",
            version="1.21.0",
            qualifiers={
                "channel": "main",
                "subdir": "linux-64"
            }
        )
        with pytest.raises(HandlerError, match="Missing required qualifier: build"):
            self.handler.build_download_url(purl)

    def test_build_download_url_missing_channel(self):
        """Test error when channel qualifier is missing."""
        purl = Purl(
            ecosystem="conda",
            name="numpy",
            version="1.21.0",
            qualifiers={
                "build": "py39h89e85a6_0",
                "subdir": "linux-64"
            }
        )
        with pytest.raises(HandlerError, match="Missing required qualifier: channel"):
            self.handler.build_download_url(purl)

    def test_build_download_url_missing_subdir(self):
        """Test error when subdir qualifier is missing."""
        purl = Purl(
            ecosystem="conda",
            name="numpy",
            version="1.21.0",
            qualifiers={
                "build": "py39h89e85a6_0",
                "channel": "main"
            }
        )
        with pytest.raises(HandlerError, match="Missing required qualifier: subdir"):
            self.handler.build_download_url(purl)

    def test_get_download_url_from_api(self):
        """Test that API method returns None (not implemented)."""
        purl = Purl(ecosystem="conda", name="numpy", version="1.21.0")
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_with_version(self):
        """Test getting fallback command with version."""
        purl = Purl(
            ecosystem="conda",
            name="numpy",
            version="1.21.0",
            qualifiers={"channel": "conda-forge"}
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "conda search -c conda-forge numpy=1.21.0 --info"

    def test_get_fallback_cmd_default_channel(self):
        """Test getting fallback command with default channel."""
        purl = Purl(ecosystem="conda", name="numpy", version="1.21.0")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "conda search -c conda-forge numpy=1.21.0 --info"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(ecosystem="conda", name="numpy")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_package_manager_cmd(self):
        """Test getting package manager commands."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["conda", "mamba", "micromamba"]

    def test_is_package_manager_available(self):
        """Test checking if package manager is available."""
        with patch("purl2src.handlers.base.shutil.which") as mock_which:
            # Test conda available
            mock_which.side_effect = lambda x: "/usr/bin/conda" if x == "conda" else None
            assert self.handler.is_package_manager_available() is True

            # Test mamba available
            mock_which.side_effect = lambda x: "/usr/bin/mamba" if x == "mamba" else None
            assert self.handler.is_package_manager_available() is True

            # Test micromamba available
            mock_which.side_effect = lambda x: "/usr/bin/micromamba" if x == "micromamba" else None
            assert self.handler.is_package_manager_available() is True

            # Test none available
            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output_with_url(self):
        """Test parsing conda search output with URL."""
        output = """numpy 1.21.0 py39h89e85a6_0
file name   : numpy-1.21.0-py39h89e85a6_0.tar.bz2
name        : numpy
version     : 1.21.0
build string: py39h89e85a6_0
build number: 0
size        : 6.6 MB
license     : BSD
url         : https://repo.anaconda.com/pkgs/main/linux-64/numpy-1.21.0-py39h89e85a6_0.tar.bz2
md5         : abc123def456
timestamp   : 2021-06-22 20:41:35 UTC
dependencies:
  - blas * mkl
  - python >=3.9,<3.10.0a0"""

        url = self.handler.parse_fallback_output(output)
        assert url == "https://repo.anaconda.com/pkgs/main/linux-64/numpy-1.21.0-py39h89e85a6_0.tar.bz2"

    def test_parse_fallback_output_no_url(self):
        """Test parsing conda search output without URL."""
        output = """numpy 1.21.0 py39h89e85a6_0
file name   : numpy-1.21.0-py39h89e85a6_0.tar.bz2
name        : numpy
version     : 1.21.0
build string: py39h89e85a6_0"""

        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_empty(self):
        """Test parsing empty conda search output."""
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_invalid_url(self):
        """Test parsing conda search output with invalid URL."""
        output = """numpy 1.21.0 py39h89e85a6_0
url         : not-a-valid-url"""

        url = self.handler.parse_fallback_output(output)
        assert url is None
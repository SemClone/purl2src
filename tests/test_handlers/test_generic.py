"""Tests for Generic handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.generic import GenericHandler
from purl2src.handlers.base import HandlerResult
from purl2src.utils.http import HttpClient


class TestGenericHandler:
    """Test Generic handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = GenericHandler(self.http_client)

    def test_build_download_url_with_download_url_qualifier(self):
        """Test building download URL from download_url qualifier."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={"download_url": "https://example.com/package.tar.gz"},
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://example.com/package.tar.gz"

    def test_build_download_url_with_vcs_url_simple(self):
        """Test building download URL from simple vcs_url qualifier."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={"vcs_url": "https://github.com/user/repo.git"},
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://github.com/user/repo.git"

    def test_build_download_url_with_vcs_url_git_prefix(self):
        """Test building download URL from vcs_url with git+ prefix."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={"vcs_url": "git+https://github.com/user/repo.git"},
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://github.com/user/repo.git"

    def test_build_download_url_with_vcs_url_commit(self):
        """Test building download URL from vcs_url with commit hash."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={"vcs_url": "https://github.com/user/repo.git@abc123def456"},
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://github.com/user/repo.git"
        # Check that commit is stored
        assert hasattr(self.handler, "_commit")
        assert self.handler._commit == "abc123def456"

    def test_build_download_url_with_vcs_url_git_prefix_commit(self):
        """Test building download URL from vcs_url with git+ prefix and commit hash."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={"vcs_url": "git+https://github.com/user/repo.git@abc123def456"},
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://github.com/user/repo.git"
        assert hasattr(self.handler, "_commit")
        assert self.handler._commit == "abc123def456"

    def test_build_download_url_no_qualifiers(self):
        """Test building download URL without relevant qualifiers."""
        purl = Purl(ecosystem="generic", name="mypackage", version="1.0.0")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_priority_download_url_over_vcs(self):
        """Test that download_url takes priority over vcs_url."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={
                "download_url": "https://example.com/package.tar.gz",
                "vcs_url": "https://github.com/user/repo.git",
            },
        )
        url = self.handler.build_download_url(purl)
        assert url == "https://example.com/package.tar.gz"

    def test_get_download_url_from_api(self):
        """Test that API method returns None (not implemented)."""
        purl = Purl(ecosystem="generic", name="mypackage", version="1.0.0")
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_with_vcs_url_simple(self):
        """Test getting fallback command for simple vcs_url."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            qualifiers={"vcs_url": "https://github.com/user/repo.git"},
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/user/repo.git"

    def test_get_fallback_cmd_with_vcs_url_git_prefix(self):
        """Test getting fallback command for vcs_url with git+ prefix."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            qualifiers={"vcs_url": "git+https://github.com/user/repo.git"},
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/user/repo.git"

    def test_get_fallback_cmd_with_vcs_url_commit(self):
        """Test getting fallback command for vcs_url with commit hash."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            qualifiers={"vcs_url": "https://github.com/user/repo.git@abc123def456"},
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/user/repo.git && git checkout abc123def456"

    def test_get_fallback_cmd_with_vcs_url_git_prefix_commit(self):
        """Test getting fallback command for vcs_url with git+ prefix and commit hash."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            qualifiers={"vcs_url": "git+https://github.com/user/repo.git@abc123def456"},
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "git clone https://github.com/user/repo.git && git checkout abc123def456"

    def test_get_fallback_cmd_no_vcs_url(self):
        """Test getting fallback command without vcs_url qualifier."""
        purl = Purl(ecosystem="generic", name="mypackage", version="1.0.0")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

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
        output = "Cloning into 'repo'..."
        url = self.handler.parse_fallback_output(output)
        assert url is None

        # Test empty output
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_get_download_url_with_checksum_validation_sha256(self):
        """Test download URL with SHA256 checksum validation."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={
                "download_url": "https://example.com/package.tar.gz",
                "checksum": "sha256:abc123def456",
            },
        )

        # Mock validation success
        self.http_client.validate_url.return_value = True
        self.http_client.download_and_verify.return_value = None

        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/package.tar.gz"
        assert result.status == "success"
        assert result.validated is True

        # Verify checksum validation was called
        self.http_client.download_and_verify.assert_called_once_with(
            "https://example.com/package.tar.gz",
            expected_checksum="abc123def456",
            algorithm="sha256",
        )

    def test_get_download_url_with_checksum_validation_default_sha256(self):
        """Test download URL with checksum validation (default SHA256)."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={
                "download_url": "https://example.com/package.tar.gz",
                "checksum": "abc123def456",
            },
        )

        # Mock validation success
        self.http_client.validate_url.return_value = True
        self.http_client.download_and_verify.return_value = None

        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/package.tar.gz"
        assert result.status == "success"
        assert result.validated is True

        # Verify checksum validation was called with default SHA256
        self.http_client.download_and_verify.assert_called_once_with(
            "https://example.com/package.tar.gz",
            expected_checksum="abc123def456",
            algorithm="sha256",
        )

    def test_get_download_url_with_checksum_validation_failure(self):
        """Test download URL with checksum validation failure."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={
                "download_url": "https://example.com/package.tar.gz",
                "checksum": "sha256:abc123def456",
            },
        )

        # Mock validation success but checksum failure
        self.http_client.validate_url.return_value = True
        self.http_client.download_and_verify.side_effect = ValueError("Checksum mismatch")

        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/package.tar.gz"
        assert result.status == "failed"
        assert result.validated is False
        assert result.error == "Checksum mismatch"

    def test_get_download_url_without_checksum(self):
        """Test download URL without checksum validation."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={"download_url": "https://example.com/package.tar.gz"},
        )

        # Mock validation success
        self.http_client.validate_url.return_value = True

        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/package.tar.gz"
        assert result.status == "success"
        assert result.validated is True

        # Verify checksum validation was not called
        self.http_client.download_and_verify.assert_not_called()

    def test_get_download_url_without_validation(self):
        """Test download URL without URL validation."""
        purl = Purl(
            ecosystem="generic",
            name="mypackage",
            version="1.0.0",
            qualifiers={
                "download_url": "https://example.com/package.tar.gz",
                "checksum": "sha256:abc123def456",
            },
        )

        result = self.handler.get_download_url(purl, validate=False)

        assert result.download_url == "https://example.com/package.tar.gz"
        assert result.status == "success"
        assert result.validated is False

        # Verify neither URL nor checksum validation was called
        self.http_client.validate_url.assert_not_called()
        self.http_client.download_and_verify.assert_not_called()

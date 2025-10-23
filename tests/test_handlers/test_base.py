"""Tests for base handler class."""

import subprocess
from unittest.mock import MagicMock, Mock, patch

import pytest

from purl2src.handlers.base import BaseHandler, HandlerError, HandlerResult
from purl2src.parser import Purl
from purl2src.utils.http import HttpClient


class TestBaseHandler:
    """Test base handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)

        # Create a concrete implementation for testing
        class TestHandler(BaseHandler):
            def build_download_url(self, purl: Purl):
                if purl.name == "direct_success":
                    return "https://example.com/direct.tgz"
                elif purl.name == "direct_fail":
                    return None
                elif purl.name == "api_success":
                    return None  # Force to try API
                else:
                    raise Exception("Direct method failed")

            def get_download_url_from_api(self, purl: Purl):
                if purl.name == "api_success":
                    return "https://example.com/api.tgz"
                elif purl.name == "api_fail":
                    return None
                else:
                    raise Exception("API method failed")

            def get_fallback_cmd(self, purl: Purl):
                if purl.name in [
                    "fallback_success",
                    "fallback_fail",
                    "direct_success",
                    "api_success",
                ]:
                    return f"echo https://example.com/{purl.name}.tgz"
                return None

            def get_package_manager_cmd(self):
                return ["testpm", "alt-testpm"]

            def parse_fallback_output(self, output: str):
                if "fallback_success" in output:
                    return output.strip()
                return None

        self.handler = TestHandler(self.http_client)

    def test_handler_initialization(self):
        """Test handler initialization."""
        assert self.handler.http_client == self.http_client

    def test_handler_result_creation(self):
        """Test HandlerResult creation and conversion."""
        result = HandlerResult(
            purl="pkg:test/package@1.0.0",
            download_url="https://example.com/package.tgz",
            validated=True,
            method="direct",
            fallback_command="testpm download package@1.0.0",
            status="success",
        )

        assert result.purl == "pkg:test/package@1.0.0"
        assert result.download_url == "https://example.com/package.tgz"
        assert result.validated is True
        assert result.method == "direct"
        assert result.status == "success"

        # Test to_dict method
        result_dict = result.to_dict()
        assert result_dict["purl"] == "pkg:test/package@1.0.0"
        assert result_dict["download_url"] == "https://example.com/package.tgz"
        assert "error" not in result_dict  # None values should be filtered out

    def test_handler_result_with_none_values(self):
        """Test HandlerResult filters out None values in to_dict."""
        result = HandlerResult(
            purl="pkg:test/package@1.0.0",
            download_url=None,
            validated=False,
            method="none",
            error="Failed to resolve",
            status="failed",
        )

        result_dict = result.to_dict()
        assert "download_url" not in result_dict
        assert result_dict["error"] == "Failed to resolve"

    @patch("shutil.which")
    def test_direct_url_success_with_validation(self, mock_which):
        """Test successful direct URL resolution with validation."""
        mock_which.return_value = "/usr/bin/testpm"
        self.http_client.validate_url.return_value = True

        purl = Purl(ecosystem="test", name="direct_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=True)

        assert result.purl == str(purl)
        assert result.download_url == "https://example.com/direct.tgz"
        assert result.validated is True
        assert result.method == "direct"
        assert result.status == "success"
        assert result.fallback_available is True

        self.http_client.validate_url.assert_called_once_with("https://example.com/direct.tgz")

    @patch("shutil.which")
    def test_direct_url_success_without_validation(self, mock_which):
        """Test successful direct URL resolution without validation."""
        mock_which.return_value = "/usr/bin/testpm"

        purl = Purl(ecosystem="test", name="direct_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=False)

        assert result.download_url == "https://example.com/direct.tgz"
        assert result.validated is False
        assert result.method == "direct"
        assert result.status == "success"

        self.http_client.validate_url.assert_not_called()

    @patch("shutil.which")
    def test_direct_url_validation_fails(self, mock_which):
        """Test direct URL validation fails, falls back to API."""
        mock_which.return_value = "/usr/bin/testpm"

        # Create a PURL that will return a URL from direct method but fail validation
        # This should cause it to fall back to API
        purl = Purl(ecosystem="test", name="direct_success", version="1.0.0")

        # Mock validation to fail for direct URL, then succeed for API URL
        self.http_client.validate_url.side_effect = [False, True]

        # Override the test handler to also provide API method for this PURL
        original_api_method = self.handler.get_download_url_from_api

        def mock_api_method(p):
            if p.name == "direct_success":
                return "https://example.com/api.tgz"
            return original_api_method(p)

        self.handler.get_download_url_from_api = mock_api_method

        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/api.tgz"
        assert result.method == "api"
        assert result.status == "success"

    @patch("shutil.which")
    def test_api_fallback_success(self, mock_which):
        """Test API method success when direct fails."""
        mock_which.return_value = "/usr/bin/testpm"
        self.http_client.validate_url.return_value = True

        purl = Purl(ecosystem="test", name="api_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/api.tgz"
        assert result.method == "api"
        assert result.status == "success"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_fallback_command_success(self, mock_run, mock_which):
        """Test package manager fallback success."""
        mock_which.return_value = "/usr/bin/testpm"

        # Setup subprocess mock
        mock_result = Mock()
        mock_result.stdout = "https://example.com/fallback_success.tgz"
        mock_run.return_value = mock_result

        self.http_client.validate_url.return_value = True

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url == "https://example.com/fallback_success.tgz"
        assert result.method == "fallback"
        assert result.status == "success"

        # Verify subprocess was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["timeout"] == 30
        assert call_args[1]["check"] is True

    @patch("shutil.which")
    def test_package_manager_not_available(self, mock_which):
        """Test when package manager is not available."""
        mock_which.return_value = None  # Package manager not found

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url is None
        assert result.method == "none"
        assert result.status == "failed"
        assert result.fallback_available is False
        assert result.error == "Failed to resolve download URL"

    @patch("shutil.which")
    def test_all_methods_fail(self, mock_which):
        """Test when all resolution methods fail."""
        mock_which.return_value = "/usr/bin/testpm"
        self.http_client.validate_url.return_value = False

        purl = Purl(ecosystem="test", name="all_fail", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url is None
        assert result.method == "none"
        assert result.status == "failed"
        assert result.error == "Failed to resolve download URL"

    def test_is_package_manager_available_found(self):
        """Test package manager availability check when found."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/testpm" if cmd == "testpm" else None

            assert self.handler.is_package_manager_available() is True
            mock_which.assert_called_with("testpm")

    def test_is_package_manager_available_alternative_found(self):
        """Test package manager availability check with alternative command."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: (
                "/usr/bin/alt-testpm" if cmd == "alt-testpm" else None
            )

            assert self.handler.is_package_manager_available() is True
            # Should check both commands
            assert mock_which.call_count == 2

    def test_is_package_manager_available_not_found(self):
        """Test package manager availability check when not found."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None

            assert self.handler.is_package_manager_available() is False

    @patch("subprocess.run")
    def test_execute_fallback_command_success(self, mock_run):
        """Test successful fallback command execution."""
        mock_result = Mock()
        mock_result.stdout = "https://example.com/fallback_success.tgz"
        mock_run.return_value = mock_result

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")
        result = self.handler.execute_fallback_command(purl)

        assert result == "https://example.com/fallback_success.tgz"

    @patch("subprocess.run")
    def test_execute_fallback_command_timeout(self, mock_run):
        """Test fallback command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("testpm", 30)

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")

        with pytest.raises(HandlerError, match="Command timed out"):
            self.handler.execute_fallback_command(purl)

    @patch("subprocess.run")
    def test_execute_fallback_command_error(self, mock_run):
        """Test fallback command execution error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "testpm", stderr="Command failed")

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")

        with pytest.raises(HandlerError, match="Command failed"):
            self.handler.execute_fallback_command(purl)

    def test_execute_fallback_command_no_command(self):
        """Test fallback command execution with no command."""
        purl = Purl(ecosystem="test", name="no_fallback", version="1.0.0")
        result = self.handler.execute_fallback_command(purl)

        assert result is None

    def test_parse_fallback_output_base_implementation(self):
        """Test base implementation of parse_fallback_output returns None."""
        # Test the actual base implementation through our test handler
        # by calling the method directly (not through the polymorphic get_download_url)

        # Create a minimal concrete handler that uses base implementation
        class MinimalHandler(BaseHandler):
            def build_download_url(self, purl: Purl):
                return None

            def get_download_url_from_api(self, purl: Purl):
                return None

            def get_fallback_cmd(self, purl: Purl):
                return None

            def get_package_manager_cmd(self):
                return []

            # Inherit base parse_fallback_output (doesn't override)

        handler = MinimalHandler(self.http_client)
        result = handler.parse_fallback_output("some output")
        assert result is None

    def test_handler_error_exception(self):
        """Test HandlerError exception."""
        error = HandlerError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    @patch("shutil.which")
    def test_fallback_available_calculation(self, mock_which):
        """Test fallback_available field calculation."""
        # Test with package manager available and fallback command
        mock_which.return_value = "/usr/bin/testpm"
        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=False)
        assert result.fallback_available is True

        # Test with no package manager
        mock_which.return_value = None
        result = self.handler.get_download_url(purl, validate=False)
        assert result.fallback_available is False

        # Test with package manager but no fallback command
        mock_which.return_value = "/usr/bin/testpm"
        purl_no_fallback = Purl(ecosystem="test", name="no_fallback", version="1.0.0")
        result = self.handler.get_download_url(purl_no_fallback, validate=False)
        assert result.fallback_available is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_fallback_command_validation_fails(self, mock_run, mock_which):
        """Test fallback command succeeds but validation fails."""
        mock_which.return_value = "/usr/bin/testpm"

        mock_result = Mock()
        mock_result.stdout = "https://example.com/fallback_success.tgz"
        mock_run.return_value = mock_result

        self.http_client.validate_url.return_value = False

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=True)

        assert result.download_url is None
        assert result.method == "none"
        assert result.status == "failed"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_fallback_command_parse_fails(self, mock_run, mock_which):
        """Test fallback command executes but parsing fails."""
        mock_which.return_value = "/usr/bin/testpm"

        mock_result = Mock()
        mock_result.stdout = "https://example.com/fallback_fail.tgz"  # Will return None from parse
        mock_run.return_value = mock_result

        purl = Purl(ecosystem="test", name="fallback_fail", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=False)

        assert result.download_url is None
        assert result.method == "none"
        assert result.status == "failed"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_fallback_command_exception(self, mock_run, mock_which):
        """Test fallback command raises exception during execution."""
        mock_which.return_value = "/usr/bin/testpm"
        mock_run.side_effect = Exception("Unexpected error")

        purl = Purl(ecosystem="test", name="fallback_success", version="1.0.0")
        result = self.handler.get_download_url(purl, validate=False)

        assert result.download_url is None
        assert result.method == "none"
        assert result.status == "failed"

    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods must be implemented."""
        # BaseHandler can't be instantiated directly due to abstract methods
        with pytest.raises(TypeError):
            BaseHandler(self.http_client)

    @patch("shutil.which")
    def test_method_order_priority(self, mock_which):
        """Test that methods are tried in correct order: direct -> api -> fallback."""
        mock_which.return_value = "/usr/bin/testpm"

        # Create a handler that tracks method calls
        method_calls = []

        class TrackingHandler(BaseHandler):
            def build_download_url(self, purl: Purl):
                method_calls.append("direct")
                return None  # Force fallback to next method

            def get_download_url_from_api(self, purl: Purl):
                method_calls.append("api")
                return None  # Force fallback to next method

            def get_fallback_cmd(self, purl: Purl):
                method_calls.append("fallback_cmd_check")
                return "testpm download test"  # Return a command to enable fallback

            def get_package_manager_cmd(self):
                return ["testpm"]

            def execute_fallback_command(self, purl: Purl):
                method_calls.append("fallback_execute")
                return None  # Force failure

        tracking_handler = TrackingHandler(self.http_client)
        purl = Purl(ecosystem="test", name="test", version="1.0.0")
        tracking_handler.get_download_url(purl, validate=False)

        # get_fallback_cmd is called first to check availability, then methods are tried in order
        assert method_calls == ["fallback_cmd_check", "direct", "api", "fallback_execute"]

    @patch("shutil.which")
    def test_early_success_skips_later_methods(self, mock_which):
        """Test that successful method skips later methods."""
        mock_which.return_value = "/usr/bin/testpm"
        self.http_client.validate_url.return_value = True

        method_calls = []

        class EarlySuccessHandler(BaseHandler):
            def build_download_url(self, purl: Purl):
                method_calls.append("direct")
                return "https://example.com/direct.tgz"  # Success

            def get_download_url_from_api(self, purl: Purl):
                method_calls.append("api")
                return "https://example.com/api.tgz"

            def get_fallback_cmd(self, purl: Purl):
                method_calls.append("fallback_cmd_check")
                return "testpm download test"

            def get_package_manager_cmd(self):
                return ["testpm"]

        handler = EarlySuccessHandler(self.http_client)
        purl = Purl(ecosystem="test", name="test", version="1.0.0")
        result = handler.get_download_url(purl, validate=True)

        # get_fallback_cmd is called first to check availability, then direct succeeds
        assert method_calls == [
            "fallback_cmd_check",
            "direct",
        ]  # Should not call api or fallback execute
        assert result.method == "direct"
        assert result.status == "success"

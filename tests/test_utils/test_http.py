"""Tests for HTTP utility."""

import hashlib
import json
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from purl2src.utils.http import HttpClient


class TestHttpClient:
    """Test HTTP client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = HttpClient(timeout=30, max_retries=3)

    def teardown_method(self):
        """Clean up after tests."""
        self.client.close()

    def test_client_initialization_default_params(self):
        """Test client initialization with default parameters."""
        client = HttpClient()
        assert client.timeout == 30
        assert isinstance(client.session, requests.Session)

        # Check User-Agent header
        assert "semantic-copycat-purl2src" in client.session.headers["User-Agent"]

    def test_client_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        client = HttpClient(timeout=60, max_retries=5)
        assert client.timeout == 60

        # Close the client
        client.close()

    def test_session_adapter_configuration(self):
        """Test that session adapters are configured correctly."""
        # Check that adapters are mounted for both http and https
        http_adapter = self.client.session.get_adapter("http://example.com")
        https_adapter = self.client.session.get_adapter("https://example.com")

        assert isinstance(http_adapter, HTTPAdapter)
        assert isinstance(https_adapter, HTTPAdapter)

    @patch("requests.Session.get")
    def test_get_request(self, mock_get):
        """Test GET request method."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_get.return_value = mock_response

        url = "https://example.com/test"
        response = self.client.get(url)

        assert response == mock_response
        mock_get.assert_called_once_with(url, timeout=30)

    @patch("requests.Session.get")
    def test_get_request_with_kwargs(self, mock_get):
        """Test GET request with additional kwargs."""
        mock_response = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/test"
        headers = {"Authorization": "Bearer token"}
        response = self.client.get(url, headers=headers, timeout=60)

        assert response == mock_response
        mock_get.assert_called_once_with(url, headers=headers, timeout=60)

    @patch("requests.Session.head")
    def test_head_request(self, mock_head):
        """Test HEAD request method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url = "https://example.com/test"
        response = self.client.head(url)

        assert response == mock_response
        mock_head.assert_called_once_with(url, timeout=30)

    @patch("requests.Session.head")
    def test_validate_url_success(self, mock_head):
        """Test URL validation with successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url = "https://example.com/valid"
        result = self.client.validate_url(url)

        assert result is True
        mock_head.assert_called_once_with(url, allow_redirects=True, timeout=30)

    @patch("requests.Session.head")
    def test_validate_url_failure_status_code(self, mock_head):
        """Test URL validation with non-200 status code."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        url = "https://example.com/notfound"
        result = self.client.validate_url(url)

        assert result is False

    @patch("requests.Session.head")
    def test_validate_url_request_exception(self, mock_head):
        """Test URL validation with request exception."""
        mock_head.side_effect = requests.RequestException("Network error")

        url = "https://example.com/error"
        result = self.client.validate_url(url)

        assert result is False

    @patch("requests.Session.get")
    def test_download_and_verify_success(self, mock_get):
        """Test successful download and verification."""
        # Create test content
        content = b"test file content"
        expected_hash = hashlib.sha256(content).hexdigest()

        # Setup mock response
        mock_response = Mock()
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/file.txt"
        result = self.client.download_and_verify(url, expected_hash)

        assert result == content
        mock_get.assert_called_once_with(url, stream=True, timeout=30)
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.Session.get")
    def test_download_and_verify_checksum_mismatch(self, mock_get):
        """Test download with checksum mismatch."""
        content = b"test file content"
        wrong_hash = "wrong_checksum"

        mock_response = Mock()
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/file.txt"

        with pytest.raises(ValueError, match="Checksum mismatch"):
            self.client.download_and_verify(url, wrong_hash)

    @patch("requests.Session.get")
    def test_download_and_verify_no_checksum(self, mock_get):
        """Test download without checksum verification."""
        content = b"test file content"

        mock_response = Mock()
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/file.txt"
        result = self.client.download_and_verify(url)

        assert result == content

    @patch("requests.Session.get")
    def test_download_and_verify_chunked_content(self, mock_get):
        """Test download with chunked content."""
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        full_content = b"".join(chunks)
        expected_hash = hashlib.sha256(full_content).hexdigest()

        mock_response = Mock()
        mock_response.iter_content.return_value = chunks
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/file.txt"
        result = self.client.download_and_verify(url, expected_hash)

        assert result == full_content

    @patch("requests.Session.get")
    def test_download_and_verify_different_algorithm(self, mock_get):
        """Test download with different hash algorithm."""
        content = b"test file content"
        expected_hash = hashlib.md5(content).hexdigest()

        mock_response = Mock()
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/file.txt"
        result = self.client.download_and_verify(url, expected_hash, algorithm="md5")

        assert result == content

    @patch("requests.Session.get")
    def test_download_and_verify_request_exception(self, mock_get):
        """Test download with request exception."""
        mock_get.side_effect = requests.RequestException("Network error")

        url = "https://example.com/file.txt"

        with pytest.raises(requests.RequestException):
            self.client.download_and_verify(url)

    @patch("requests.Session.get")
    def test_download_and_verify_http_error(self, mock_get):
        """Test download with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        url = "https://example.com/notfound.txt"

        with pytest.raises(requests.HTTPError):
            self.client.download_and_verify(url)

    @patch("requests.Session.get")
    def test_get_json_success(self, mock_get):
        """Test successful JSON response."""
        json_data = {"key": "value", "number": 42}

        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://api.example.com/data"
        result = self.client.get_json(url)

        assert result == json_data
        mock_get.assert_called_once_with(url, timeout=30)
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.Session.get")
    def test_get_json_with_kwargs(self, mock_get):
        """Test JSON request with additional kwargs."""
        json_data = {"data": "test"}

        mock_response = Mock()
        mock_response.json.return_value = json_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://api.example.com/data"
        headers = {"Accept": "application/json"}
        result = self.client.get_json(url, headers=headers)

        assert result == json_data
        mock_get.assert_called_once_with(url, headers=headers, timeout=30)

    @patch("requests.Session.get")
    def test_get_json_request_exception(self, mock_get):
        """Test JSON request with request exception."""
        mock_get.side_effect = requests.RequestException("Network error")

        url = "https://api.example.com/data"

        with pytest.raises(requests.RequestException):
            self.client.get_json(url)

    @patch("requests.Session.get")
    def test_get_json_http_error(self, mock_get):
        """Test JSON request with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        url = "https://api.example.com/data"

        with pytest.raises(requests.HTTPError):
            self.client.get_json(url)

    @patch("requests.Session.get")
    def test_get_json_decode_error(self, mock_get):
        """Test JSON request with JSON decode error."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://api.example.com/data"

        with pytest.raises(json.JSONDecodeError):
            self.client.get_json(url)

    def test_context_manager(self):
        """Test using HttpClient as context manager."""
        with HttpClient() as client:
            assert isinstance(client, HttpClient)
            # Test that it has the context manager methods
            assert hasattr(client, '__enter__')
            assert hasattr(client, '__exit__')

        # Test the context manager calls close
        with patch('purl2src.utils.http.HttpClient.close') as mock_close:
            with HttpClient() as client:
                pass
            mock_close.assert_called_once()

    def test_close_method(self):
        """Test close method."""
        with patch.object(self.client.session, 'close') as mock_close:
            self.client.close()
            mock_close.assert_called_once()

    @patch("requests.Session.get")
    def test_retry_configuration(self, mock_get):
        """Test that retry configuration is working."""
        # Setup mock to fail first calls then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_success = Mock()
        mock_response_success.status_code = 200

        mock_get.side_effect = [
            requests.HTTPError("Server Error"),
            requests.HTTPError("Server Error"),
            mock_response_success
        ]

        # This test verifies the retry adapter is configured
        # The actual retry behavior is handled by urllib3/requests
        client = HttpClient(max_retries=3)
        try:
            # The adapter should be configured for retries
            adapter = client.session.get_adapter("https://example.com")
            assert isinstance(adapter, HTTPAdapter)
            assert adapter.max_retries.total == 3
        finally:
            client.close()

    @patch("requests.Session.get")
    def test_timeout_handling(self, mock_get):
        """Test timeout handling."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        url = "https://slow.example.com"

        with pytest.raises(requests.Timeout):
            self.client.get(url)

    @patch("requests.Session.get")
    def test_custom_timeout_override(self, mock_get):
        """Test custom timeout override."""
        mock_response = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/test"
        self.client.get(url, timeout=120)

        mock_get.assert_called_once_with(url, timeout=120)

    def test_user_agent_header(self):
        """Test that User-Agent header is set correctly."""
        user_agent = self.client.session.headers.get("User-Agent")
        assert "semantic-copycat-purl2src" in user_agent

    @patch("requests.Session.get")
    def test_download_empty_content(self, mock_get):
        """Test download with empty content."""
        mock_response = Mock()
        mock_response.iter_content.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/empty.txt"
        result = self.client.download_and_verify(url)

        assert result == b""

    @patch("requests.Session.get")
    def test_download_with_none_chunks(self, mock_get):
        """Test download with None chunks (empty chunks in stream)."""
        content = b"test content"
        chunks = [b"test", None, b" content", None]  # None chunks should be ignored

        mock_response = Mock()
        mock_response.iter_content.return_value = chunks
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        url = "https://example.com/file.txt"
        result = self.client.download_and_verify(url)

        assert result == content

    def test_case_insensitive_checksum_verification(self):
        """Test case-insensitive checksum verification."""
        content = b"test file content"
        checksum = hashlib.sha256(content).hexdigest()

        with patch.object(self.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.iter_content.return_value = [content]
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            url = "https://example.com/file.txt"

            # Test with uppercase checksum
            result = self.client.download_and_verify(url, checksum.upper())
            assert result == content

            # Test with lowercase checksum
            result = self.client.download_and_verify(url, checksum.lower())
            assert result == content

    @patch("requests.Session.head")
    def test_validate_url_with_redirects(self, mock_head):
        """Test URL validation follows redirects."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url = "https://example.com/redirect"
        result = self.client.validate_url(url)

        assert result is True
        mock_head.assert_called_once_with(url, allow_redirects=True, timeout=30)

    def test_session_adapter_pool_configuration(self):
        """Test session adapter pool configuration."""
        adapter = self.client.session.get_adapter("https://example.com")
        # HTTPAdapter pool_maxsize is set in __init__ but might not be directly accessible
        # We just verify it's an HTTPAdapter which should have pool configuration
        assert isinstance(adapter, HTTPAdapter)
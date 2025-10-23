"""Tests for PyPI handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.pypi import PyPiHandler
from purl2src.utils.http import HttpClient


class TestPyPiHandler:
    """Test PyPI handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = PyPiHandler(self.http_client)

    def test_build_download_url_basic(self):
        """Test building download URL for basic package."""
        purl = Purl(
            ecosystem="pypi",
            name="requests",
            version="2.28.1"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/r/requests/requests-2.28.1.tar.gz"
        assert url == expected

    def test_build_download_url_with_namespace(self):
        """Test building download URL with namespace (uses namespace for first letter)."""
        purl = Purl(
            ecosystem="pypi",
            namespace="mycompany",
            name="package",
            version="1.0.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/m/package/package-1.0.0.tar.gz"
        assert url == expected

    def test_build_download_url_no_version(self):
        """Test building download URL without version returns None."""
        purl = Purl(ecosystem="pypi", name="requests")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_first_letter_extraction(self):
        """Test first letter extraction for different package names."""
        # Test uppercase
        purl = Purl(ecosystem="pypi", name="Django", version="4.1.0")
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/d/Django/Django-4.1.0.tar.gz"
        assert url == expected

        # Test number
        purl = Purl(ecosystem="pypi", name="3to2", version="1.1.1")
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/3/3to2/3to2-1.1.1.tar.gz"
        assert url == expected

        # Test special character
        purl = Purl(ecosystem="pypi", name="-package", version="1.0.0")
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/-/-package/-package-1.0.0.tar.gz"
        assert url == expected

    def test_get_download_url_from_api_with_version(self):
        """Test API method with specific version."""
        purl = Purl(ecosystem="pypi", name="requests", version="2.28.1")

        # Mock API response
        self.http_client.get_json.return_value = {
            "releases": {
                "2.28.1": [
                    {
                        "packagetype": "sdist",
                        "url": "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"
                    },
                    {
                        "packagetype": "bdist_wheel",
                        "url": "https://files.pythonhosted.org/packages/py3/requests-2.28.1-py3-none-any.whl"
                    }
                ]
            }
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"

        # Verify API call
        self.http_client.get_json.assert_called_once_with("https://pypi.org/pypi/requests/json")

    def test_get_download_url_from_api_latest_version(self):
        """Test API method without version (latest)."""
        purl = Purl(ecosystem="pypi", name="requests")

        # Mock API response
        self.http_client.get_json.return_value = {
            "urls": [
                {
                    "packagetype": "sdist",
                    "url": "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"
                },
                {
                    "packagetype": "bdist_wheel",
                    "url": "https://files.pythonhosted.org/packages/py3/requests-2.28.1-py3-none-any.whl"
                }
            ]
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"

    def test_get_download_url_from_api_no_sdist(self):
        """Test API method when no sdist available, fallback to any tar.gz."""
        purl = Purl(ecosystem="pypi", name="requests", version="2.28.1")

        # Mock API response with only wheel
        self.http_client.get_json.return_value = {
            "releases": {
                "2.28.1": [
                    {
                        "packagetype": "bdist_wheel",
                        "url": "https://files.pythonhosted.org/packages/py3/requests-2.28.1-py3-none-any.whl"
                    },
                    {
                        "packagetype": "other",
                        "url": "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"
                    }
                ]
            }
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url == "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"

    def test_get_download_url_from_api_version_not_found(self):
        """Test API method when version is not found."""
        purl = Purl(ecosystem="pypi", name="requests", version="99.99.99")

        # Mock API response without the requested version
        self.http_client.get_json.return_value = {
            "releases": {
                "2.28.1": [
                    {
                        "packagetype": "sdist",
                        "url": "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"
                    }
                ]
            }
        }

        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_download_url_from_api_exception(self):
        """Test API method with exception."""
        purl = Purl(ecosystem="pypi", name="requests", version="2.28.1")

        # Mock API exception
        self.http_client.get_json.side_effect = Exception("API Error")

        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_with_version(self):
        """Test getting fallback command with version."""
        purl = Purl(ecosystem="pypi", name="requests", version="2.28.1")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "pip download --no-deps --no-binary :all: requests%3D%3D2.28.1"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(ecosystem="pypi", name="requests")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_fallback_cmd_special_characters(self):
        """Test getting fallback command with special characters."""
        purl = Purl(ecosystem="pypi", name="my-package", version="1.0.0")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "pip download --no-deps --no-binary :all: my-package%3D%3D1.0.0"

    def test_get_package_manager_cmd(self):
        """Test getting package manager commands."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["pip", "pip3"]

    def test_is_package_manager_available_pip(self):
        """Test checking if pip is available."""
        with patch("shutil.which") as mock_which:
            # Test pip available
            mock_which.side_effect = lambda x: "/usr/bin/pip" if x == "pip" else None
            assert self.handler.is_package_manager_available() is True

    def test_is_package_manager_available_pip3(self):
        """Test checking if pip3 is available."""
        with patch("shutil.which") as mock_which:
            # Test pip3 available
            mock_which.side_effect = lambda x: "/usr/bin/pip3" if x == "pip3" else None
            assert self.handler.is_package_manager_available() is True

    def test_is_package_manager_available_none(self):
        """Test checking if no package manager is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output_downloading_pattern(self):
        """Test parsing pip download output with 'Downloading' pattern."""
        output = """Collecting requests==2.28.1
  Downloading https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz (109kB)
Successfully downloaded requests"""

        url = self.handler.parse_fallback_output(output)
        assert url == "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"

    def test_parse_fallback_output_from_pattern(self):
        """Test parsing pip download output with 'from' pattern."""
        output = """Collecting requests==2.28.1
  Using cached requests-2.28.1.tar.gz from https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz
Successfully downloaded requests"""

        url = self.handler.parse_fallback_output(output)
        assert url == "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"

    def test_parse_fallback_output_no_url(self):
        """Test parsing pip download output without URL."""
        output = """Collecting requests==2.28.1
  Using cached requests-2.28.1.tar.gz
Successfully downloaded requests"""

        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_multiple_lines(self):
        """Test parsing pip download output with multiple packages."""
        output = """Collecting requests==2.28.1
  Downloading https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz (109kB)
Collecting urllib3>=1.21.1
  Downloading https://files.pythonhosted.org/packages/source/u/urllib3/urllib3-1.26.12.tar.gz (300kB)
Successfully downloaded requests urllib3"""

        url = self.handler.parse_fallback_output(output)
        # Should return the first URL found
        assert url == "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.1.tar.gz"

    def test_parse_fallback_output_empty(self):
        """Test parsing empty pip download output."""
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_api_response_edge_cases(self):
        """Test API response edge cases."""
        purl = Purl(ecosystem="pypi", name="requests", version="2.28.1")

        # Empty releases
        self.http_client.get_json.return_value = {"releases": {}}
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

        # No files for version
        self.http_client.get_json.return_value = {"releases": {"2.28.1": []}}
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

        # Missing fields
        self.http_client.get_json.return_value = {"releases": {"2.28.1": [{"url": "test.tar.gz"}]}}
        url = self.handler.get_download_url_from_api(purl)
        assert url == "test.tar.gz"

    def test_build_download_url_edge_case_names(self):
        """Test building download URL with edge case package names."""
        # Package with underscore
        purl = Purl(ecosystem="pypi", name="my_package", version="1.0.0")
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/m/my_package/my_package-1.0.0.tar.gz"
        assert url == expected

        # Package with dot
        purl = Purl(ecosystem="pypi", name="my.package", version="1.0.0")
        url = self.handler.build_download_url(purl)
        expected = "https://pypi.python.org/packages/source/m/my.package/my.package-1.0.0.tar.gz"
        assert url == expected
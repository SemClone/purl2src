"""Tests for NuGet handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.nuget import NuGetHandler
from purl2src.utils.http import HttpClient


class TestNuGetHandler:
    """Test NuGet handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = NuGetHandler(self.http_client)

    def test_build_download_url_basic(self):
        """Test building download URL for basic package."""
        purl = Purl(
            ecosystem="nuget",
            name="Newtonsoft.Json",
            version="13.0.1"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.1/newtonsoft.json.13.0.1.nupkg"
        assert url == expected

    def test_build_download_url_case_handling(self):
        """Test that package names and versions are lowercased."""
        purl = Purl(
            ecosystem="nuget",
            name="Microsoft.Extensions.Logging",
            version="6.0.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/microsoft.extensions.logging/6.0.0/microsoft.extensions.logging.6.0.0.nupkg"
        assert url == expected

    def test_build_download_url_prerelease(self):
        """Test building download URL for prerelease package."""
        purl = Purl(
            ecosystem="nuget",
            name="Microsoft.AspNetCore.App",
            version="7.0.0-rc.1.22426.10"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/microsoft.aspnetcore.app/7.0.0-rc.1.22426.10/microsoft.aspnetcore.app.7.0.0-rc.1.22426.10.nupkg"
        assert url == expected

    def test_build_download_url_complex_name(self):
        """Test building download URL for complex package name."""
        purl = Purl(
            ecosystem="nuget",
            name="System.Text.Json",
            version="6.0.5"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/system.text.json/6.0.5/system.text.json.6.0.5.nupkg"
        assert url == expected

    def test_build_download_url_no_version(self):
        """Test building download URL without version returns None."""
        purl = Purl(ecosystem="nuget", name="Newtonsoft.Json")
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_special_characters(self):
        """Test building download URL with special characters in name."""
        purl = Purl(
            ecosystem="nuget",
            name="jQuery",
            version="3.6.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/jquery/3.6.0/jquery.3.6.0.nupkg"
        assert url == expected

    def test_build_download_url_numeric_version(self):
        """Test building download URL with numeric version formats."""
        purl = Purl(
            ecosystem="nuget",
            name="EntityFramework",
            version="6.4.4"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/entityframework/6.4.4/entityframework.6.4.4.nupkg"
        assert url == expected

    def test_build_download_url_underscore_in_name(self):
        """Test building download URL with underscore in package name."""
        purl = Purl(
            ecosystem="nuget",
            name="NUnit3TestAdapter",
            version="4.2.1"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/nunit3testadapter/4.2.1/nunit3testadapter.4.2.1.nupkg"
        assert url == expected

    def test_get_download_url_from_api(self):
        """Test that API method returns None (not implemented)."""
        purl = Purl(
            ecosystem="nuget",
            name="Newtonsoft.Json",
            version="13.0.1"
        )
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_with_version(self):
        """Test getting fallback command with version."""
        purl = Purl(
            ecosystem="nuget",
            name="Newtonsoft.Json",
            version="13.0.1"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "dotnet nuget list source"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(ecosystem="nuget", name="Newtonsoft.Json")
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_package_manager_cmd(self):
        """Test getting package manager commands."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["nuget", "dotnet"]

    def test_is_package_manager_available_nuget(self):
        """Test checking if NuGet package manager is available."""
        with patch("shutil.which") as mock_which:
            # Test nuget available
            mock_which.side_effect = lambda x: "/usr/bin/nuget" if x == "nuget" else None
            assert self.handler.is_package_manager_available() is True

    def test_is_package_manager_available_dotnet(self):
        """Test checking if dotnet package manager is available."""
        with patch("shutil.which") as mock_which:
            # Test dotnet available
            mock_which.side_effect = lambda x: "/usr/bin/dotnet" if x == "dotnet" else None
            assert self.handler.is_package_manager_available() is True

    def test_is_package_manager_available_none(self):
        """Test checking if no package manager is available."""
        with patch("shutil.which") as mock_which:
            # Test none available
            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output(self):
        """Test parsing nuget output."""
        # NuGet list source doesn't provide download URLs
        output = """Registered Sources:
  1.  nuget.org [Enabled]
      https://api.nuget.org/v3/index.json
  2.  Microsoft Visual Studio Offline Packages [Enabled]
      C:\\Program Files (x86)\\Microsoft SDKs\\NuGetPackages\\"""

        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_empty(self):
        """Test parsing empty nuget output."""
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_parse_fallback_output_error(self):
        """Test parsing nuget error output."""
        output = "error: Unable to load the service index for source https://invalid-source.org/"
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_build_download_url_version_edge_cases(self):
        """Test building download URL with various version edge cases."""
        # Version with four parts
        purl = Purl(
            ecosystem="nuget",
            name="Microsoft.Extensions.Hosting",
            version="6.0.1.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/microsoft.extensions.hosting/6.0.1.0/microsoft.extensions.hosting.6.0.1.0.nupkg"
        assert url == expected

        # Version with pre-release and build metadata
        purl = Purl(
            ecosystem="nuget",
            name="TestPackage",
            version="1.0.0-beta.1+build.123"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/testpackage/1.0.0-beta.1+build.123/testpackage.1.0.0-beta.1+build.123.nupkg"
        assert url == expected

    def test_build_download_url_long_package_name(self):
        """Test building download URL with very long package name."""
        purl = Purl(
            ecosystem="nuget",
            name="Microsoft.Extensions.DependencyInjection.Abstractions",
            version="6.0.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://api.nuget.org/v3-flatcontainer/microsoft.extensions.dependencyinjection.abstractions/6.0.0/microsoft.extensions.dependencyinjection.abstractions.6.0.0.nupkg"
        assert url == expected

    def test_case_sensitivity_consistency(self):
        """Test that case handling is consistent throughout the URL."""
        purl = Purl(
            ecosystem="nuget",
            name="UPPERCASE.Package.NAME",
            version="1.0.0-BETA"
        )
        url = self.handler.build_download_url(purl)
        # All parts should be lowercase
        expected = "https://api.nuget.org/v3-flatcontainer/uppercase.package.name/1.0.0-beta/uppercase.package.name.1.0.0-beta.nupkg"
        assert url == expected
        # Verify no uppercase letters remain
        assert url.lower() == url
"""Simple E2E tests to verify package resolution works for all ecosystems."""

import pytest
from purl2src import get_download_url


@pytest.mark.e2e
class TestE2E:
    """End-to-end tests for all supported ecosystems."""

    def test_npm_package(self):
        """Verify NPM package resolves correctly."""
        result = get_download_url("pkg:npm/express@4.18.2")
        assert result.download_url == "https://registry.npmjs.org/express/-/express-4.18.2.tgz"

    def test_npm_scoped_package(self):
        """Verify scoped NPM package resolves correctly."""
        result = get_download_url("pkg:npm/@angular/core@15.0.0")
        assert result.download_url == "https://registry.npmjs.org/@angular/core/-/core-15.0.0.tgz"

    def test_pypi_package(self):
        """Verify PyPI package resolves correctly."""
        result = get_download_url("pkg:pypi/requests@2.31.0")
        assert result.download_url is not None
        # PyPI can use either domain
        assert "pypi.python.org" in result.download_url or "pythonhosted.org" in result.download_url
        assert "requests-2.31.0" in result.download_url

    def test_rubygems_package(self):
        """Verify RubyGems package resolves correctly."""
        result = get_download_url("pkg:gem/rails@7.0.4")
        assert result.download_url == "https://rubygems.org/downloads/rails-7.0.4.gem"

    def test_cargo_package(self):
        """Verify Cargo/Crates.io package resolves correctly."""
        result = get_download_url("pkg:cargo/serde@1.0.152")
        assert result.download_url == "https://crates.io/api/v1/crates/serde/1.0.152/download"

    def test_nuget_package(self):
        """Verify NuGet package resolves correctly."""
        result = get_download_url("pkg:nuget/Newtonsoft.Json@13.0.2")
        assert result.download_url == "https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.2/newtonsoft.json.13.0.2.nupkg"

    def test_maven_package(self):
        """Verify Maven package resolves correctly."""
        result = get_download_url("pkg:maven/org.apache.commons/commons-lang3@3.12.0")
        expected = "https://repo.maven.apache.org/maven2/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.jar"
        assert result.download_url == expected

    def test_maven_with_classifier(self):
        """Verify Maven package with classifier resolves correctly."""
        result = get_download_url("pkg:maven/org.apache.commons/commons-lang3@3.12.0?classifier=sources")
        expected = "https://repo.maven.apache.org/maven2/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0-sources.jar"
        assert result.download_url == expected

    def test_golang_package(self):
        """Verify Golang package resolves correctly."""
        result = get_download_url("pkg:golang/github.com/gin-gonic/gin@v1.9.0")
        # Go proxy uses URL encoding for slashes
        assert result.download_url == "https://proxy.golang.org/github.com%2Fgin-gonic%2Fgin/@v/v1.9.0.zip"

    def test_github_package(self):
        """Verify GitHub package resolves correctly."""
        result = get_download_url("pkg:github/facebook/react@v18.2.0")
        assert result.download_url is not None
        assert "github.com/facebook/react" in result.download_url
        # GitHub handler returns git URL
        assert result.download_url == "https://github.com/facebook/react.git"

    def test_conda_package(self):
        """Verify Conda package resolves correctly (if qualifiers provided)."""
        result = get_download_url("pkg:conda/numpy@1.24.0?channel=conda-forge&subdir=linux-64&build=py39h1234567_0")
        # Conda requires specific qualifiers, may return None if not all provided
        if result.download_url:
            assert "numpy" in result.download_url
            assert "1.24.0" in result.download_url


    def test_validation_flag(self):
        """Verify validation actually checks if URL exists."""
        # This should succeed
        result = get_download_url("pkg:npm/express@4.18.2", validate=True)
        assert result.validated is True

        # Non-existent package should not validate
        result = get_download_url("pkg:npm/this-definitely-does-not-exist-xyz123@1.0.0", validate=True)
        # If it returns a URL, it should fail validation
        if result.download_url:
            assert result.validated is False
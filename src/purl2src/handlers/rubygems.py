"""RubyGems handler."""

import re
from typing import Optional, List
from urllib.parse import urlparse

from ..parser import Purl
from .base import BaseHandler


class RubyGemsHandler(BaseHandler):
    """Handler for Ruby gems."""

    def _is_github_url(self, url: str) -> bool:
        """
        Safely check if a URL is from GitHub by parsing the hostname and scheme.

        Args:
            url: The URL to check

        Returns:
            True if the URL is from github.com with http/https scheme, False otherwise
        """
        try:
            parsed = urlparse(url)
            return parsed.hostname == "github.com" and parsed.scheme in ("http", "https")
        except Exception:
            return False

    def _names_version(self, url: str, purl: Purl) -> bool:
        """Check that a gem URL points at the version the caller asked for.

        Only the path is compared. A query string or fragment can be made to end
        with the requested filename without the URL serving that gem, and a
        legitimate URL can carry a query that the filename check would otherwise
        reject.
        """
        try:
            path = urlparse(url).path
        except Exception:
            return False
        return path.rstrip("/").endswith(f"/{purl.name}-{purl.version}.gem")

    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build RubyGems download URL.

        Format: https://rubygems.org/downloads/{name}-{version}.gem
        """
        if not purl.version:
            return None

        return f"https://rubygems.org/downloads/{purl.name}-{purl.version}.gem"

    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query RubyGems API."""
        api_url = f"https://rubygems.org/api/v1/gems/{purl.name}.json"

        try:
            data = self.http_client.get_json(api_url)

            # Check various URL fields
            # Priority: gem_uri, source_code_uri (if github), homepage_uri (if github)

            # Direct gem URI. This endpoint describes the gem's latest release, so
            # for a versioned request it names the wrong artifact unless it happens
            # to name the version asked for.
            if "gem_uri" in data:
                gem_uri = data["gem_uri"]
                if purl.version and not self._names_version(gem_uri, purl):
                    return None
                result: Optional[str] = gem_uri
                return result

            # The remaining fields are repository URLs, which say nothing about
            # which version they would give you. Returning one for a versioned
            # request reports a resolvable URL for a version that may not exist.
            if purl.version:
                return None

            # Source code URI if it's GitHub
            if "source_code_uri" in data:
                uri = data["source_code_uri"]
                if self._is_github_url(uri):
                    if not uri.endswith(".git"):
                        git_url: Optional[str] = f"{uri}.git"
                        return git_url
                    source_uri: Optional[str] = uri
                    return source_uri

            # Homepage URI if it's GitHub
            if "homepage_uri" in data:
                uri = data["homepage_uri"]
                if self._is_github_url(uri):
                    if not uri.endswith(".git"):
                        return f"{uri}.git"
                    homepage_url: Optional[str] = uri
                    return homepage_url

            return None

        except Exception:
            return None

    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get gem command."""
        if not purl.version:
            return None

        return f"gem fetch {purl.name} --version {purl.version}"

    def get_package_manager_cmd(self) -> List[str]:
        """Gem command."""
        return ["gem"]

    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse gem fetch output."""
        # gem fetch downloads the file but doesn't show the URL
        # Look for "Downloaded" message
        match = re.search(r"Downloaded\s+(\S+)", output)
        if match:
            # This gives us the filename, not the URL
            # We could construct the URL from it
            filename = match.group(1)
            if filename.endswith(".gem"):
                # Extract name and version
                match = re.match(r"(.+)-([^-]+)\.gem$", filename)
                if match:
                    name, version = match.groups()
                    return f"https://rubygems.org/downloads/{filename}"
        return None

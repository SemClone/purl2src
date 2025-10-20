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
            return (parsed.hostname == "github.com" and
                   parsed.scheme in ("http", "https"))
        except Exception:
            return False

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
            
            # Direct gem URI
            if "gem_uri" in data:
                return data["gem_uri"]
            
            # Source code URI if it's GitHub
            if "source_code_uri" in data:
                uri = data["source_code_uri"]
                if self._is_github_url(uri) and not uri.endswith(".git"):
                    return f"{uri}.git"
                return uri
            
            # Homepage URI if it's GitHub
            if "homepage_uri" in data:
                uri = data["homepage_uri"]
                if self._is_github_url(uri) and not uri.endswith(".git"):
                    return f"{uri}.git"
            
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
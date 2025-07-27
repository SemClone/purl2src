"""PyPI (Python Package Index) handler."""

import re
from typing import Optional, List
from urllib.parse import quote

from ..parser import Purl
from .base import BaseHandler


class PyPiHandler(BaseHandler):
    """Handler for PyPI packages."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build PyPI download URL using predictable pattern.
        
        Format: https://pypi.python.org/packages/source/{first_letter}/{name}/{name}-{version}.tar.gz
        """
        if not purl.version:
            return None
        
        # Get first letter of package name
        first_letter = (purl.namespace or purl.name)[0].lower()
        
        # Construct URL
        return (
            f"https://pypi.python.org/packages/source/{first_letter}/"
            f"{purl.name}/{purl.name}-{purl.version}.tar.gz"
        )
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query PyPI JSON API for download URL."""
        # API URL
        api_url = f"https://pypi.org/pypi/{purl.name}/json"
        
        try:
            data = self.http_client.get_json(api_url)
            
            # Find the version
            if purl.version:
                if purl.version not in data.get("releases", {}):
                    return None
                releases = data["releases"][purl.version]
            else:
                # Use latest version
                releases = data.get("urls", [])
            
            # Look for source distribution (tar.gz)
            for release in releases:
                if release.get("packagetype") == "sdist":
                    url = release.get("url")
                    if url and url.endswith(".tar.gz"):
                        return url
            
            # Fallback to any tar.gz
            for release in releases:
                url = release.get("url")
                if url and url.endswith(".tar.gz"):
                    return url
            
            return None
            
        except Exception:
            return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get pip command to download package."""
        if not purl.version:
            return None
        
        # Use pip download to get the URL
        package_spec = f"{purl.name}=={purl.version}"
        return f"pip download --no-deps --no-binary :all: {quote(package_spec)}"
    
    def get_package_manager_cmd(self) -> List[str]:
        """Pip command names."""
        return ["pip", "pip3"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse pip download output to extract download URL."""
        # Look for "Downloading" line with URL
        for line in output.split("\n"):
            if "Downloading" in line:
                # Extract URL from line like "Downloading https://..."
                match = re.search(r"Downloading\s+(https?://[^\s]+)", line)
                if match:
                    return match.group(1)
        
        # Alternative: look for "from https://" pattern
        for line in output.split("\n"):
            match = re.search(r"from\s+(https?://[^\s]+)", line)
            if match:
                return match.group(1)
        
        return None
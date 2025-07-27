"""GoLang handler."""

import json
from typing import Optional, List
from urllib.parse import quote

from ..parser import Purl
from .base import BaseHandler


class GoLangHandler(BaseHandler):
    """Handler for Go modules."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build Go module proxy URL.
        
        Format: https://proxy.golang.org/{module}/@v/{version}.zip
        """
        if not purl.version:
            return None
        
        # Construct module path
        if purl.namespace:
            module_path = f"{purl.namespace}/{purl.name}"
        else:
            module_path = purl.name
        
        # URL encode the module path
        encoded_path = quote(module_path, safe="")
        
        return f"https://proxy.golang.org/{encoded_path}/@v/{purl.version}.zip"
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query Go proxy for module info."""
        # Construct module path
        if purl.namespace:
            module_path = f"{purl.namespace}/{purl.name}"
        else:
            module_path = purl.name
        
        # URL encode the module path
        encoded_path = quote(module_path, safe="")
        
        # Try to get module info
        info_url = f"https://proxy.golang.org/{encoded_path}/@v/{purl.version}.info"
        
        try:
            # Verify the version exists
            self.http_client.get(info_url)
            # If successful, return the zip URL
            return f"https://proxy.golang.org/{encoded_path}/@v/{purl.version}.zip"
        except Exception:
            return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get go command."""
        if not purl.version:
            return None
        
        # Construct module path
        if purl.namespace:
            module_path = f"{purl.namespace}/{purl.name}"
        else:
            module_path = purl.name
        
        return f"go mod download -json {module_path}@{purl.version}"
    
    def get_package_manager_cmd(self) -> List[str]:
        """Go command."""
        return ["go"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse go mod download JSON output."""
        try:
            data = json.loads(output)
            # Go mod download returns zip file path, not URL
            # We could construct the proxy URL from the module info
            if "Path" in data and "Version" in data:
                module_path = quote(data["Path"], safe="")
                version = data["Version"]
                return f"https://proxy.golang.org/{module_path}/@v/{version}.zip"
        except json.JSONDecodeError:
            pass
        return None
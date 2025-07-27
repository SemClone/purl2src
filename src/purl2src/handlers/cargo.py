"""Cargo (Rust) handler."""

from typing import Optional, List
from urllib.parse import quote

from ..parser import Purl
from .base import BaseHandler


class CargoHandler(BaseHandler):
    """Handler for Cargo/Rust packages."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build Cargo download URL.
        
        Format: https://crates.io/api/v1/crates/{name}/{version}/download
        """
        if not purl.version:
            return None
        
        return f"https://crates.io/api/v1/crates/{purl.name}/{purl.version}/download"
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Cargo doesn't need API query - direct URL works."""
        return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get cargo command."""
        return f"cargo search {quote(purl.name)} --limit 1"
    
    def get_package_manager_cmd(self) -> List[str]:
        """Cargo command name."""
        return ["cargo"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse cargo search output."""
        # Cargo search doesn't directly provide download URLs
        # This would need more complex handling
        return None
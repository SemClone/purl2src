"""NuGet (.NET) handler."""

from typing import Optional, List
from urllib.parse import quote

from ..parser import Purl
from .base import BaseHandler


class NuGetHandler(BaseHandler):
    """Handler for NuGet packages."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build NuGet download URL.
        
        Format: https://api.nuget.org/v3-flatcontainer/{id}/{version}/{id}.{version}.nupkg
        """
        if not purl.version:
            return None
        
        package_id = purl.name.lower()
        version = purl.version.lower()
        
        return (
            f"https://api.nuget.org/v3-flatcontainer/"
            f"{package_id}/{version}/{package_id}.{version}.nupkg"
        )
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query NuGet API for download URL."""
        # NuGet v3 API is complex, direct URL usually works
        return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get nuget/dotnet command."""
        if not purl.version:
            return None
        
        return f"dotnet nuget list source"
    
    def get_package_manager_cmd(self) -> List[str]:
        """NuGet command names."""
        return ["nuget", "dotnet"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse nuget output."""
        # This would need more complex handling
        return None
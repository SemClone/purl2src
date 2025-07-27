"""GitHub handler."""

import re
from typing import Optional, List

from ..parser import Purl
from .base import BaseHandler


class GitHubHandler(BaseHandler):
    """Handler for GitHub repositories."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build GitHub repository URL.
        
        Returns git URL for cloning.
        """
        if not purl.namespace:
            return None
        
        # Base repository URL
        repo_url = f"https://github.com/{purl.namespace}/{purl.name}.git"
        
        # If subpath is specified, we need the specific file URL
        if purl.subpath:
            # For files, use raw content URL
            branch = purl.version or "main"
            return (
                f"https://raw.githubusercontent.com/"
                f"{purl.namespace}/{purl.name}/{branch}/{purl.subpath}"
            )
        
        return repo_url
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query GitHub API for download URL."""
        if not purl.namespace:
            return None
        
        # Check if it's a release
        if purl.version and not purl.version in ["main", "master"]:
            # Try releases API
            api_url = (
                f"https://api.github.com/repos/"
                f"{purl.namespace}/{purl.name}/releases/tags/{purl.version}"
            )
            
            try:
                data = self.http_client.get_json(api_url)
                # Look for source code archive
                if "tarball_url" in data:
                    return data["tarball_url"]
            except Exception:
                pass
        
        # For branches/tags, return archive URL
        if purl.version:
            return (
                f"https://github.com/{purl.namespace}/{purl.name}/"
                f"archive/refs/tags/{purl.version}.tar.gz"
            )
        
        return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get git command."""
        if not purl.namespace:
            return None
        
        repo_url = f"https://github.com/{purl.namespace}/{purl.name}.git"
        
        if purl.version:
            return f"git clone {repo_url} && cd {purl.name} && git checkout {purl.version}"
        else:
            return f"git clone {repo_url}"
    
    def get_package_manager_cmd(self) -> List[str]:
        """Git command."""
        return ["git"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse git output."""
        # Git clone doesn't return download URLs
        return None
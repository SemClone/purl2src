"""Generic handler using qualifiers."""

import re
from typing import Optional, List

from ..parser import Purl
from .base import BaseHandler


class GenericHandler(BaseHandler):
    """Handler for generic packages using qualifiers."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """Build URL from qualifiers."""
        # Check for direct download_url qualifier
        if "download_url" in purl.qualifiers:
            return purl.qualifiers["download_url"]
        
        # Check for vcs_url qualifier
        if "vcs_url" in purl.qualifiers:
            vcs_url = purl.qualifiers["vcs_url"]
            
            # Handle git+https:// prefix
            if vcs_url.startswith("git+"):
                vcs_url = vcs_url[4:]
            
            # Extract commit hash if present
            match = re.match(r"(.+)@([a-f0-9]+)$", vcs_url)
            if match:
                repo_url, commit = match.groups()
                # Store commit for later checkout
                self._commit = commit
                return repo_url
            
            return vcs_url
        
        return None
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Generic packages don't have a registry API."""
        return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get git command for VCS URLs."""
        if "vcs_url" in purl.qualifiers:
            vcs_url = purl.qualifiers["vcs_url"]
            
            # Handle git+https:// prefix
            if vcs_url.startswith("git+"):
                vcs_url = vcs_url[4:]
            
            # Extract commit hash if present
            match = re.match(r"(.+)@([a-f0-9]+)$", vcs_url)
            if match:
                repo_url, commit = match.groups()
                return f"git clone {repo_url} && git checkout {commit}"
            
            return f"git clone {vcs_url}"
        
        return None
    
    def get_package_manager_cmd(self) -> List[str]:
        """Git is used for VCS URLs."""
        return ["git"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse git output."""
        # Git clone doesn't return download URLs
        return None
    
    def get_download_url(self, purl: Purl, validate: bool = True) -> "HandlerResult":
        """Override to handle checksum validation."""
        result = super().get_download_url(purl, validate)
        
        # If we have a download URL and checksum, validate it
        if (
            result.download_url
            and result.validated
            and "checksum" in purl.qualifiers
        ):
            try:
                # Download and verify checksum
                checksum = purl.qualifiers["checksum"]
                # Extract algorithm if specified (e.g., sha256:abc123)
                if ":" in checksum:
                    algo, value = checksum.split(":", 1)
                else:
                    algo, value = "sha256", checksum
                
                self.http_client.download_and_verify(
                    result.download_url,
                    expected_checksum=value,
                    algorithm=algo
                )
            except ValueError as e:
                result.error = str(e)
                result.status = "failed"
                result.validated = False
        
        return result
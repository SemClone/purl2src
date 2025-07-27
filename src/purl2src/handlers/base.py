"""Base handler class for all package ecosystems."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
import shutil
import subprocess
import shlex

from ..parser import Purl
from ..utils.http import HttpClient


@dataclass
class HandlerResult:
    """Result from handler processing."""
    purl: str
    download_url: Optional[str]
    validated: bool
    method: str  # "direct", "api", or "fallback"
    fallback_command: Optional[str] = None
    error: Optional[str] = None
    status: str = "success"  # "success" or "failed"
    fallback_available: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class HandlerError(Exception):
    """Exception raised by handlers."""
    pass


class BaseHandler(ABC):
    """Base class for all ecosystem handlers."""
    
    def __init__(self, http_client: HttpClient):
        self.http_client = http_client
    
    def get_download_url(self, purl: Purl, validate: bool = True) -> HandlerResult:
        """
        Get download URL for a package.
        
        This method implements the three-level resolution strategy:
        1. Try direct URL construction
        2. Try API query
        3. Try package manager fallback
        
        Args:
            purl: Parsed PURL object
            validate: Whether to validate the URL is accessible
            
        Returns:
            HandlerResult with download URL and metadata
        """
        # Check fallback availability once
        fallback_cmd = self.get_fallback_cmd(purl)
        fallback_available = bool(fallback_cmd and self.is_package_manager_available())
        
        # Level 1: Try direct URL construction
        try:
            url = self.build_download_url(purl)
            if url and (not validate or self.http_client.validate_url(url)):
                return HandlerResult(
                    purl=str(purl),
                    download_url=url,
                    validated=validate,
                    method="direct",
                    fallback_command=fallback_cmd,
                    fallback_available=fallback_available,
                )
        except Exception:
            pass
        
        # Level 2: Try API query
        try:
            url = self.get_download_url_from_api(purl)
            if url and (not validate or self.http_client.validate_url(url)):
                return HandlerResult(
                    purl=str(purl),
                    download_url=url,
                    validated=validate,
                    method="api",
                    fallback_command=fallback_cmd,
                    fallback_available=fallback_available,
                )
        except Exception:
            pass
        
        # Level 3: Try package manager fallback
        if fallback_available:
            try:
                url = self.execute_fallback_command(purl)
                if url and (not validate or self.http_client.validate_url(url)):
                    return HandlerResult(
                        purl=str(purl),
                        download_url=url,
                        validated=validate,
                        method="fallback",
                        fallback_command=fallback_cmd,
                        fallback_available=fallback_available,
                    )
            except Exception:
                pass
        
        # All methods failed
        return HandlerResult(
            purl=str(purl),
            download_url=None,
            validated=False,
            method="none",
            fallback_command=fallback_cmd,
            error="Failed to resolve download URL",
            status="failed",
            fallback_available=fallback_available,
        )
    
    @abstractmethod
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build direct download URL from PURL components.
        
        Args:
            purl: Parsed PURL object
            
        Returns:
            Download URL or None if not applicable
        """
        pass
    
    @abstractmethod
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """
        Query package registry API for download URL.
        
        Args:
            purl: Parsed PURL object
            
        Returns:
            Download URL or None if not found
        """
        pass
    
    @abstractmethod
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """
        Get package manager command for fallback.
        
        Args:
            purl: Parsed PURL object
            
        Returns:
            Command string or None if not available
        """
        pass
    
    @abstractmethod
    def get_package_manager_cmd(self) -> List[str]:
        """
        Get package manager command name(s) to check.
        
        Returns:
            List of command names (e.g., ["npm", "yarn"])
        """
        pass
    
    def is_package_manager_available(self) -> bool:
        """Check if package manager is installed."""
        for cmd in self.get_package_manager_cmd():
            if shutil.which(cmd):
                return True
        return False
    
    def execute_fallback_command(self, purl: Purl) -> Optional[str]:
        """
        Execute package manager command and parse output.
        
        Args:
            purl: Parsed PURL object
            
        Returns:
            Download URL extracted from command output
            
        Raises:
            HandlerError: If command execution fails
        """
        cmd = self.get_fallback_cmd(purl)
        if not cmd:
            return None
        
        try:
            # Execute command safely
            result = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            
            # Parse output - this should be overridden by subclasses
            return self.parse_fallback_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise HandlerError(f"Command timed out: {cmd}")
        except subprocess.CalledProcessError as e:
            raise HandlerError(f"Command failed: {cmd}\n{e.stderr}")
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """
        Parse package manager command output.
        
        This should be overridden by subclasses to extract the download URL
        from the specific package manager's output format.
        
        Args:
            output: Command stdout
            
        Returns:
            Download URL or None if not found
        """
        return None
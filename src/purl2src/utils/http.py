"""HTTP client utilities with connection pooling."""

import hashlib
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HttpClient:
    """HTTP client with connection pooling and retry logic."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=20)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "User-Agent": "semantic-copycat-purl2src/0.1.0"
        })
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform GET request."""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)
    
    def head(self, url: str, **kwargs) -> requests.Response:
        """Perform HEAD request."""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.head(url, **kwargs)
    
    def validate_url(self, url: str) -> bool:
        """
        Validate that a URL is accessible.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL returns 200 OK, False otherwise
        """
        try:
            response = self.head(url, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def download_and_verify(
        self, 
        url: str, 
        expected_checksum: Optional[str] = None,
        algorithm: str = "sha256"
    ) -> bytes:
        """
        Download content and optionally verify checksum.
        
        Args:
            url: URL to download
            expected_checksum: Expected checksum value
            algorithm: Hash algorithm (default: sha256)
            
        Returns:
            Downloaded content as bytes
            
        Raises:
            ValueError: If checksum doesn't match
            requests.RequestException: If download fails
        """
        response = self.get(url, stream=True)
        response.raise_for_status()
        
        # Download in chunks and calculate hash
        hasher = hashlib.new(algorithm)
        content_chunks = []
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                hasher.update(chunk)
                content_chunks.append(chunk)
        
        content = b"".join(content_chunks)
        
        # Verify checksum if provided
        if expected_checksum:
            actual_checksum = hasher.hexdigest()
            if actual_checksum.lower() != expected_checksum.lower():
                raise ValueError(
                    f"Checksum mismatch: expected {expected_checksum}, "
                    f"got {actual_checksum}"
                )
        
        return content
    
    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Get JSON response from URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get
            
        Returns:
            Parsed JSON response
            
        Raises:
            requests.RequestException: If request fails
            json.JSONDecodeError: If response is not valid JSON
        """
        response = self.get(url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
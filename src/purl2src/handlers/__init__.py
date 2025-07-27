"""Package ecosystem handlers."""

from typing import Dict, Optional, Type
from .base import BaseHandler, HandlerResult
from .npm import NpmHandler
from .pypi import PyPiHandler
from .cargo import CargoHandler
from .nuget import NuGetHandler
from .github import GitHubHandler
from .generic import GenericHandler
from .conda import CondaHandler
from .golang import GoLangHandler
from .rubygems import RubyGemsHandler
from .maven import MavenHandler

# Registry of all available handlers
HANDLERS: Dict[str, Type[BaseHandler]] = {
    "npm": NpmHandler,
    "pypi": PyPiHandler,
    "cargo": CargoHandler,
    "nuget": NuGetHandler,
    "github": GitHubHandler,
    "generic": GenericHandler,
    "conda": CondaHandler,
    "golang": GoLangHandler,
    "gem": RubyGemsHandler,
    "rubygems": RubyGemsHandler,
    "maven": MavenHandler,
}


def get_download_url(purl: str, validate: bool = True) -> HandlerResult:
    """
    Get download URL for a Package URL.
    
    Args:
        purl: Package URL string
        validate: Whether to validate the URL is accessible
        
    Returns:
        HandlerResult with download URL and metadata
    """
    from ..parser import parse_purl
    from ..utils import HttpClient, URLCache
    
    # Check cache first
    cache = URLCache()
    cached = cache.get(purl)
    if cached:
        return HandlerResult(**cached)
    
    # Parse PURL
    parsed = parse_purl(purl)
    
    # Get appropriate handler
    handler_class = HANDLERS.get(parsed.ecosystem)
    if not handler_class:
        return HandlerResult(
            purl=purl,
            download_url=None,
            validated=False,
            method="unsupported",
            error=f"Unsupported ecosystem: {parsed.ecosystem}",
            status="failed",
            fallback_available=False,
        )
    
    # Create handler and get download URL
    with HttpClient() as http_client:
        handler = handler_class(http_client)
        result = handler.get_download_url(parsed, validate=validate)
    
    # Cache successful results
    if result.download_url and result.validated:
        cache.set(purl, result.to_dict())
    
    return result


__all__ = [
    "BaseHandler",
    "HandlerResult",
    "get_download_url",
    "HANDLERS",
]
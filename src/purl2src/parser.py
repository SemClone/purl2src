"""PURL (Package URL) parser implementation."""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import unquote, parse_qs


class PurlParseError(Exception):
    """Exception raised for PURL parsing errors."""
    pass


class Purl:
    """Represents a parsed Package URL."""
    
    def __init__(
        self,
        ecosystem: str,
        name: str,
        version: Optional[str] = None,
        namespace: Optional[str] = None,
        qualifiers: Optional[Dict[str, str]] = None,
        subpath: Optional[str] = None,
    ):
        self.ecosystem = ecosystem.lower()
        self.name = name
        self.version = version
        self.namespace = namespace
        self.qualifiers = qualifiers or {}
        self.subpath = subpath

    def __str__(self) -> str:
        """Convert back to PURL string."""
        purl = f"pkg:{self.ecosystem}/"
        if self.namespace:
            purl += f"{self.namespace}/"
        purl += self.name
        if self.version:
            purl += f"@{self.version}"
        if self.qualifiers:
            quals = "&".join(f"{k}={v}" for k, v in self.qualifiers.items())
            purl += f"?{quals}"
        if self.subpath:
            purl += f"#{self.subpath}"
        return purl

    def __repr__(self) -> str:
        return f"Purl(ecosystem={self.ecosystem!r}, name={self.name!r}, version={self.version!r})"


def parse_purl(purl_string: str) -> Purl:
    """
    Parse a Package URL string into its components.
    
    Format: pkg:{ecosystem}/[{namespace}/]{name}@{version}[?{qualifiers}][#{subpath}]
    
    Args:
        purl_string: The PURL string to parse
        
    Returns:
        Purl object with parsed components
        
    Raises:
        PurlParseError: If the PURL format is invalid
    """
    if not purl_string:
        raise PurlParseError("Empty PURL string")
    
    # Basic PURL regex pattern
    # Handle @ in scoped packages by using non-greedy match
    pattern = r"^pkg:([^/]+)/(.+?)(@[^#?]+)?(\?[^#]+)?(#.+)?$"
    match = re.match(pattern, purl_string)
    
    if not match:
        raise PurlParseError(f"Invalid PURL format: {purl_string}")
    
    ecosystem = match.group(1)
    path = match.group(2)
    version_part = match.group(3)
    qualifiers_part = match.group(4)
    subpath_part = match.group(5)
    
    # Parse version
    version = version_part[1:] if version_part else None
    
    # Parse qualifiers
    qualifiers = {}
    if qualifiers_part:
        quals_str = qualifiers_part[1:]  # Remove '?'
        qualifiers = {k: v[0] for k, v in parse_qs(quals_str).items()}
    
    # Parse subpath
    subpath = subpath_part[1:] if subpath_part else None
    
    # Special handling for different ecosystems
    if ecosystem.lower() == "golang":
        namespace, name = _parse_golang_path(path)
    else:
        # Parse namespace and name
        parts = path.split("/")
        if len(parts) > 1:
            namespace = "/".join(parts[:-1])
            name = parts[-1]
        else:
            namespace = None
            name = parts[0]
    
    # URL decode components
    if namespace:
        namespace = unquote(namespace)
    name = unquote(name)
    
    return Purl(
        ecosystem=ecosystem,
        name=name,
        version=version,
        namespace=namespace,
        qualifiers=qualifiers,
        subpath=subpath,
    )


def _parse_golang_path(path: str) -> Tuple[Optional[str], str]:
    """
    Special parsing for GoLang module paths.
    
    Examples:
        github.com/user/repo -> (github.com/user, repo)
        golang.org/x/text -> (golang.org/x, text)
        example.com/module -> (example.com, module)
    """
    parts = path.split("/")
    
    # GitHub repositories
    if parts[0] == "github.com" and len(parts) >= 3:
        namespace = "/".join(parts[:2])
        name = "/".join(parts[2:])
        return namespace, name
    
    # golang.org/x repositories
    if parts[0] == "golang.org" and len(parts) >= 3 and parts[1] == "x":
        namespace = "/".join(parts[:2])
        name = "/".join(parts[2:])
        return namespace, name
    
    # google.golang.org repositories
    if parts[0] == "google.golang.org" and len(parts) >= 2:
        namespace = parts[0]
        name = "/".join(parts[1:])
        return namespace, name
    
    # go.opentelemetry.io repositories
    if parts[0] == "go.opentelemetry.io" and len(parts) >= 2:
        namespace = parts[0]
        name = "/".join(parts[1:])
        return namespace, name
    
    # Default: first part is namespace, rest is name
    if len(parts) > 1:
        namespace = parts[0]
        name = "/".join(parts[1:])
        return namespace, name
    
    # Single part - no namespace
    return None, path
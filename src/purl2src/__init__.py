"""Semantic Copycat Purl2Src - Translate PURLs to download URLs."""

import warnings
# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

from .parser import parse_purl
from .handlers import get_download_url

try:
    from importlib.metadata import version
    __version__ = version("semantic-copycat-purl2src")
except Exception:
    # Fallback for development installations
    __version__ = "0.0.0+unknown"

__all__ = ["parse_purl", "get_download_url"]
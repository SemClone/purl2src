"""Semantic Copycat Purl2Src - Translate PURLs to download URLs."""

import warnings
# Suppress urllib3 OpenSSL warning on macOS
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

from .parser import parse_purl
from .handlers import get_download_url

__version__ = "0.1.0"
__all__ = ["parse_purl", "get_download_url"]
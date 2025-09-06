"""Conda handler."""

from typing import Optional, List

from ..parser import Purl
from .base import BaseHandler, HandlerError


class CondaHandler(BaseHandler):
    """Handler for Conda packages."""

    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build Conda download URL.

        Requires qualifiers: build, channel, subdir
        Format depends on channel:
        - main/defaults: repo.anaconda.com/pkgs/main/{subdir}/{pkg}-{ver}-{build}.tar.bz2
        - others: anaconda.org/{ch}/{pkg}/{ver}/download/{subdir}/{pkg}-{ver}-{build}.tar.bz2
        """
        if not purl.version:
            return None

        # Check required qualifiers
        required = ["build", "channel", "subdir"]
        for qual in required:
            if qual not in purl.qualifiers:
                raise HandlerError(f"Missing required qualifier: {qual}")

        build = purl.qualifiers["build"]
        channel = purl.qualifiers["channel"]
        subdir = purl.qualifiers["subdir"]

        # Handle different channel types
        if channel in ["main", "defaults"]:
            # Main/defaults channel uses repo.anaconda.com
            return (
                f"https://repo.anaconda.com/pkgs/main/{subdir}/"
                f"{purl.name}-{purl.version}-{build}.tar.bz2"
            )
        else:
            # Community channels (conda-forge, bioconda, etc.) use anaconda.org
            return (
                f"https://anaconda.org/{channel}/{purl.name}/{purl.version}/"
                f"download/{subdir}/{purl.name}-{purl.version}-{build}.tar.bz2"
            )

    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query Anaconda API."""
        # Could implement Anaconda API query here
        return None

    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get conda command."""
        if not purl.version:
            return None

        channel = purl.qualifiers.get("channel", "conda-forge")
        return f"conda search -c {channel} {purl.name}={purl.version} --info"

    def get_package_manager_cmd(self) -> List[str]:
        """Conda command names."""
        return ["conda", "mamba", "micromamba"]

    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse conda search output."""
        # Look for "url :" line
        for line in output.split("\n"):
            if line.strip().startswith("url :"):
                url = line.split(":", 1)[1].strip()
                if url.startswith("http"):
                    return url
        return None

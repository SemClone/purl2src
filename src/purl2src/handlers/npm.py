"""NPM (Node Package Manager) handler."""

import json
from typing import Optional, List
from urllib.parse import quote

from ..parser import Purl
from .base import BaseHandler


class NpmHandler(BaseHandler):
    """Handler for NPM packages."""

    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build NPM tarball URL.

        Format: https://registry.npmjs.org/{namespace/}name/-/name-version.tgz
        """
        if not purl.version:
            return None

        # Handle scoped packages
        if purl.namespace:
            # Convert %40 to @ for scoped packages
            namespace = purl.namespace.replace("%40", "@")
            package_path = f"{namespace}/{purl.name}"
            tarball_name = purl.name
        else:
            package_path = purl.name
            tarball_name = purl.name

        return f"https://registry.npmjs.org/{package_path}/-/{tarball_name}-{purl.version}.tgz"

    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Query NPM registry API for download URL."""
        # Construct package name with namespace
        if purl.namespace:
            namespace = purl.namespace.replace("%40", "@")
            package_name = f"{namespace}/{purl.name}"
        else:
            package_name = purl.name

        # Query registry API
        api_url = f"https://registry.npmjs.org/{package_name}"

        try:
            data = self.http_client.get_json(api_url)

            versions = data.get("versions", {})

            if purl.version:
                # The registry not carrying the requested version means there is
                # no answer. Substituting another release returns different
                # software under the coordinate the caller asked about, and the
                # substituted URL resolves, so it would be reported as validated.
                if purl.version not in versions:
                    return None
                version_data = versions[purl.version]
            else:
                # No version was requested, so latest answers the question posed.
                latest = data.get("dist-tags", {}).get("latest")
                if not latest or latest not in versions:
                    return None
                version_data = versions[latest]

            # Extract tarball URL
            result: Optional[str] = version_data.get("dist", {}).get("tarball")
            return result

        except Exception:
            return None

    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get npm command to retrieve download URL."""
        if not purl.version:
            return None

        # Construct package spec
        if purl.namespace:
            namespace = purl.namespace.replace("%40", "@")
            package_spec = f"{namespace}/{purl.name}@{purl.version}"
        else:
            package_spec = f"{purl.name}@{purl.version}"

        # NPM doesn't need URL encoding, just return the command directly
        return f"npm view {package_spec} dist.tarball"

    def get_package_manager_cmd(self) -> List[str]:
        """NPM command names."""
        return ["npm", "yarn"]

    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse npm view output to extract tarball URL."""
        # npm view returns the URL directly
        url = output.strip()
        if url.startswith("http") and url.endswith(".tgz"):
            return url
        return None

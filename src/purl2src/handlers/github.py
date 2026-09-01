"""GitHub handler."""

import re
from typing import Optional, List

from ..parser import Purl
from .base import BaseHandler


class GitHubHandler(BaseHandler):
    """Handler for GitHub repositories."""

    def _archive_url(self, purl: Purl) -> str:
        """Build the source archive URL for the requested ref.

        The plain ``/archive/{ref}.tar.gz`` form resolves a tag, a branch or a
        commit sha, and 404s for a ref that does not exist. The ``refs/tags/``
        form only resolves tags, so it 404s for a branch that is really there.
        """
        return f"https://github.com/{purl.namespace}/{purl.name}/" f"archive/{purl.version}.tar.gz"

    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build GitHub download URL.

        A ref that was asked for is answered with an archive of that ref. The
        clone URL resolves whatever ref you name, so returning it for a
        versioned PURL reports a ref that may not exist as validated. With no
        ref to archive, the repository itself is the honest answer.
        """
        if not purl.namespace:
            return None

        # If subpath is specified, we need the specific file URL
        if purl.subpath:
            # For files, use raw content URL
            branch = purl.version or "main"
            return (
                f"https://raw.githubusercontent.com/"
                f"{purl.namespace}/{purl.name}/{branch}/{purl.subpath}"
            )

        if purl.version:
            return self._archive_url(purl)

        return f"https://github.com/{purl.namespace}/{purl.name}.git"

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
                    result: Optional[str] = data["tarball_url"]
                    return result
            except Exception:
                pass

        # For branches/tags, return archive URL
        if purl.version:
            return self._archive_url(purl)

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

"""Maven (Java) handler."""

from typing import Optional, List

from ..parser import Purl
from .base import BaseHandler


class MavenHandler(BaseHandler):
    """Handler for Maven packages."""
    
    def build_download_url(self, purl: Purl) -> Optional[str]:
        """
        Build Maven download URL.
        
        Format: {repository_url}/{group_path}/{artifact}/{version}/{artifact}-{version}[-{classifier}].{type}
        """
        if not purl.version or not purl.namespace:
            return None
        
        # Get repository URL
        repo_url = purl.qualifiers.get(
            "repository_url", 
            "https://repo.maven.apache.org/maven2"
        )
        
        # Convert group ID dots to slashes
        group_path = purl.namespace.replace(".", "/")
        
        # Handle classifier
        classifier = None
        if "classifier" in purl.qualifiers:
            classifier = purl.qualifiers["classifier"]
        elif purl.qualifiers.get("packaging") == "sources":
            classifier = "sources"
        
        # Get file type
        file_type = purl.qualifiers.get("type", "jar")
        
        # Build filename
        filename = f"{purl.name}-{purl.version}"
        if classifier:
            filename += f"-{classifier}"
        filename += f".{file_type}"
        
        return f"{repo_url}/{group_path}/{purl.name}/{purl.version}/{filename}"
    
    def get_download_url_from_api(self, purl: Purl) -> Optional[str]:
        """Maven Central doesn't have a simple JSON API."""
        return None
    
    def get_fallback_cmd(self, purl: Purl) -> Optional[str]:
        """Get mvn command."""
        if not purl.version or not purl.namespace:
            return None
        
        # Build artifact coordinates
        coords = f"{purl.namespace}:{purl.name}:{purl.version}"
        
        # Add type if specified
        file_type = purl.qualifiers.get("type", "jar")
        coords += f":{file_type}"
        
        # Add classifier if specified
        classifier = purl.qualifiers.get("classifier")
        if not classifier and purl.qualifiers.get("packaging") == "sources":
            classifier = "sources"
        if classifier:
            coords += f":{classifier}"
        
        cmd = f"mvn dependency:get -Dartifact={coords} -Dtransitive=false"
        
        # Add custom repository if specified
        if "repository_url" in purl.qualifiers:
            cmd += f" -DremoteRepositories={purl.qualifiers['repository_url']}"
        
        return cmd
    
    def get_package_manager_cmd(self) -> List[str]:
        """Maven command."""
        return ["mvn"]
    
    def parse_fallback_output(self, output: str) -> Optional[str]:
        """Parse mvn output."""
        # Maven dependency:get doesn't return the URL directly
        # It downloads to local repository
        return None
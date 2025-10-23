"""Tests for Maven handler."""

import pytest
from unittest.mock import MagicMock, patch

from purl2src.parser import Purl
from purl2src.handlers.maven import MavenHandler
from purl2src.utils.http import HttpClient


class TestMavenHandler:
    """Test Maven handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = MagicMock(spec=HttpClient)
        self.handler = MavenHandler(self.http_client)

    def test_build_download_url_basic(self):
        """Test building download URL for basic artifact."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/springframework/spring-core/5.3.21/spring-core-5.3.21.jar"
        assert url == expected

    def test_build_download_url_with_classifier(self):
        """Test building download URL with classifier."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"classifier": "sources"}
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/springframework/spring-core/5.3.21/spring-core-5.3.21-sources.jar"
        assert url == expected

    def test_build_download_url_with_type(self):
        """Test building download URL with custom type."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"type": "pom"}
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/springframework/spring-core/5.3.21/spring-core-5.3.21.pom"
        assert url == expected

    def test_build_download_url_sources_packaging(self):
        """Test building download URL with sources packaging."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"packaging": "sources"}
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/springframework/spring-core/5.3.21/spring-core-5.3.21-sources.jar"
        assert url == expected

    def test_build_download_url_custom_repository(self):
        """Test building download URL with custom repository."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"repository_url": "https://repo.spring.io/release"}
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.spring.io/release/org/springframework/spring-core/5.3.21/spring-core-5.3.21.jar"
        assert url == expected

    def test_build_download_url_complex_group_id(self):
        """Test building download URL with complex group ID."""
        purl = Purl(
            ecosystem="maven",
            namespace="com.fasterxml.jackson.core",
            name="jackson-core",
            version="2.13.3"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/com/fasterxml/jackson/core/jackson-core/2.13.3/jackson-core-2.13.3.jar"
        assert url == expected

    def test_build_download_url_snapshot_version(self):
        """Test building download URL with SNAPSHOT version."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.example",
            name="my-library",
            version="1.0.0-SNAPSHOT"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/example/my-library/1.0.0-SNAPSHOT/my-library-1.0.0-SNAPSHOT.jar"
        assert url == expected

    def test_build_download_url_no_version(self):
        """Test building download URL without version."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core"
        )
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_no_namespace(self):
        """Test building download URL without namespace."""
        purl = Purl(
            ecosystem="maven",
            name="spring-core",
            version="5.3.21"
        )
        url = self.handler.build_download_url(purl)
        assert url is None

    def test_build_download_url_classifier_and_type(self):
        """Test building download URL with both classifier and type."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"classifier": "javadoc", "type": "jar"}
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/springframework/spring-core/5.3.21/spring-core-5.3.21-javadoc.jar"
        assert url == expected

    def test_get_download_url_from_api(self):
        """Test that API method returns None (not implemented)."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21"
        )
        url = self.handler.get_download_url_from_api(purl)
        assert url is None

    def test_get_fallback_cmd_basic(self):
        """Test getting fallback command for basic artifact."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.21:jar -Dtransitive=false"

    def test_get_fallback_cmd_with_classifier(self):
        """Test getting fallback command with classifier."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"classifier": "sources"}
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.21:jar:sources -Dtransitive=false"

    def test_get_fallback_cmd_with_type(self):
        """Test getting fallback command with custom type."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"type": "pom"}
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.21:pom -Dtransitive=false"

    def test_get_fallback_cmd_sources_packaging(self):
        """Test getting fallback command with sources packaging."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"packaging": "sources"}
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.21:jar:sources -Dtransitive=false"

    def test_get_fallback_cmd_with_custom_repository(self):
        """Test getting fallback command with custom repository."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"repository_url": "https://repo.spring.io/release"}
        )
        cmd = self.handler.get_fallback_cmd(purl)
        expected = "mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.21:jar -Dtransitive=false -DremoteRepositories=https://repo.spring.io/release"
        assert cmd == expected

    def test_get_fallback_cmd_classifier_and_type(self):
        """Test getting fallback command with both classifier and type."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core",
            version="5.3.21",
            qualifiers={"classifier": "javadoc", "type": "jar"}
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd == "mvn dependency:get -Dartifact=org.springframework:spring-core:5.3.21:jar:javadoc -Dtransitive=false"

    def test_get_fallback_cmd_no_version(self):
        """Test getting fallback command without version."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.springframework",
            name="spring-core"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_fallback_cmd_no_namespace(self):
        """Test getting fallback command without namespace."""
        purl = Purl(
            ecosystem="maven",
            name="spring-core",
            version="5.3.21"
        )
        cmd = self.handler.get_fallback_cmd(purl)
        assert cmd is None

    def test_get_package_manager_cmd(self):
        """Test getting package manager command."""
        cmd = self.handler.get_package_manager_cmd()
        assert cmd == ["mvn"]

    def test_is_package_manager_available(self):
        """Test checking if package manager is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/mvn"
            assert self.handler.is_package_manager_available() is True

            mock_which.return_value = None
            assert self.handler.is_package_manager_available() is False

    def test_parse_fallback_output(self):
        """Test parsing maven output."""
        # Maven dependency:get doesn't return URLs directly
        output = "[INFO] Downloaded from central: https://repo.maven.apache.org/maven2/org/springframework/spring-core/5.3.21/spring-core-5.3.21.jar"
        url = self.handler.parse_fallback_output(output)
        assert url is None

        # Test empty output
        output = ""
        url = self.handler.parse_fallback_output(output)
        assert url is None

    def test_edge_cases_single_letter_group(self):
        """Test edge case with single letter group ID."""
        purl = Purl(
            ecosystem="maven",
            namespace="a",
            name="artifact",
            version="1.0.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/a/artifact/1.0.0/artifact-1.0.0.jar"
        assert url == expected

    def test_edge_cases_special_characters_in_name(self):
        """Test edge case with special characters in artifact name."""
        purl = Purl(
            ecosystem="maven",
            namespace="org.example",
            name="my-artifact_name",
            version="1.0.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/org/example/my-artifact_name/1.0.0/my-artifact_name-1.0.0.jar"
        assert url == expected

    def test_long_group_id_path(self):
        """Test with very long group ID."""
        purl = Purl(
            ecosystem="maven",
            namespace="com.example.very.long.group.id.with.many.parts",
            name="artifact",
            version="1.0.0"
        )
        url = self.handler.build_download_url(purl)
        expected = "https://repo.maven.apache.org/maven2/com/example/very/long/group/id/with/many/parts/artifact/1.0.0/artifact-1.0.0.jar"
        assert url == expected
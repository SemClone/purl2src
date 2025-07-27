"""Tests for PURL parser."""

import pytest
from purl2src.parser import parse_purl, PurlParseError, Purl


class TestPurlParser:
    """Test PURL parsing functionality."""
    
    def test_parse_simple_purl(self):
        """Test parsing simple PURL without namespace."""
        purl = parse_purl("pkg:npm/express@4.17.1")
        assert purl.ecosystem == "npm"
        assert purl.name == "express"
        assert purl.version == "4.17.1"
        assert purl.namespace is None
        assert purl.qualifiers == {}
        assert purl.subpath is None
    
    def test_parse_purl_with_namespace(self):
        """Test parsing PURL with namespace."""
        purl = parse_purl("pkg:npm/@angular/core@1.0.0")
        assert purl.ecosystem == "npm"
        assert purl.namespace == "@angular"
        assert purl.name == "core"
        assert purl.version == "1.0.0"
    
    def test_parse_purl_with_qualifiers(self):
        """Test parsing PURL with qualifiers."""
        purl = parse_purl("pkg:maven/org.apache/commons@1.0?type=jar&classifier=sources")
        assert purl.ecosystem == "maven"
        assert purl.namespace == "org.apache"
        assert purl.name == "commons"
        assert purl.version == "1.0"
        assert purl.qualifiers == {"type": "jar", "classifier": "sources"}
    
    def test_parse_purl_with_subpath(self):
        """Test parsing PURL with subpath."""
        purl = parse_purl("pkg:github/user/repo@main#src/file.py")
        assert purl.ecosystem == "github"
        assert purl.namespace == "user"
        assert purl.name == "repo"
        assert purl.version == "main"
        assert purl.subpath == "src/file.py"
    
    def test_parse_golang_github(self):
        """Test parsing GoLang GitHub PURL."""
        purl = parse_purl("pkg:golang/github.com/user/repo@v1.0.0")
        assert purl.ecosystem == "golang"
        assert purl.namespace == "github.com/user"
        assert purl.name == "repo"
        assert purl.version == "v1.0.0"
    
    def test_parse_golang_stdlib(self):
        """Test parsing GoLang standard library PURL."""
        purl = parse_purl("pkg:golang/golang.org/x/text@v0.3.7")
        assert purl.ecosystem == "golang"
        assert purl.namespace == "golang.org/x"
        assert purl.name == "text"
        assert purl.version == "v0.3.7"
    
    def test_parse_invalid_purl(self):
        """Test parsing invalid PURL raises error."""
        with pytest.raises(PurlParseError):
            parse_purl("invalid-purl")
        
        with pytest.raises(PurlParseError):
            parse_purl("")
        
        with pytest.raises(PurlParseError):
            parse_purl("pkg:npm")
    
    def test_purl_to_string(self):
        """Test converting Purl object back to string."""
        original = "pkg:npm/@angular/core@1.0.0?foo=bar#src/index.js"
        purl = parse_purl(original)
        assert str(purl) == original
    
    def test_purl_repr(self):
        """Test Purl repr."""
        purl = Purl(ecosystem="npm", name="express", version="4.17.1")
        assert repr(purl) == "Purl(ecosystem='npm', name='express', version='4.17.1')"
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-01-06

### Fixed
- Conda handler now correctly resolves download URLs for packages from the 'main' channel
  - Main/defaults channels now use repo.anaconda.com/pkgs/main/ URL structure
  - Community channels (conda-forge, bioconda) continue using anaconda.org URL structure
- Resolved issue where main channel packages were failing with "Failed to resolve download URL" error

## [0.1.1] - 2025-01-27

### Changed
- Version is now dynamically loaded from pyproject.toml using importlib.metadata
- Removed hardcoded version from __init__.py to prevent version mismatches

## [0.1.0] - 2025-01-27

### Added
- Initial release of semantic-copycat-purl2src
- Support for 10 package ecosystems:
  - Maven (Java)
  - NPM (JavaScript/TypeScript)
  - PyPI (Python)
  - RubyGems (Ruby)
  - Cargo (Rust)
  - NuGet (.NET)
  - Golang (Go modules)
  - Conda (Data Science/Python)
  - GitHub (Source repositories)
  - Generic (Direct URLs)
- Three-level resolution strategy:
  1. Direct URL construction from PURL components
  2. Registry API queries for download URLs
  3. Package manager CLI fallback with availability detection
- CLI tool `purl2src` with:
  - Single PURL resolution
  - Batch processing from files
  - JSON, CSV, and text output formats
  - Progress bar for batch operations
  - URL validation options
  - Automatic output format detection from file extension
- Comprehensive PURL parsing with support for:
  - Namespaces (e.g., Maven group IDs, npm scopes)
  - Versions with special characters
  - Qualifiers (repository URLs, classifiers, etc.)
  - Subpaths
- HTTP client with:
  - Connection pooling
  - Retry logic with exponential backoff
  - Proper timeout handling
  - User-Agent headers
- Package manager detection for fallback commands
- Proper handling of scoped NPM packages (@namespace/package)

### Fixed
- PURL parser regex to handle scoped NPM packages with @ symbol
- CLI progressbar compatibility issue
- Test assertion for PURLs with qualifiers
- Maven artifact naming for Apache Commons IO versions
- fallback_available flag to correctly reflect package manager installation status
- urllib3 OpenSSL warning on macOS by constraining to v1.x and adding warning suppression
- NPM fallback command encoding issue - removed URL encoding for npm commands

### Security
- All HTTP requests use HTTPS where available
- No credentials or sensitive data are stored or logged
- Secure command execution with proper escaping

### Changed
- License from MIT to Apache-2.0

### Known Issues
- Maven fallback command doesn't directly return download URLs (downloads to local repository)
- Some ecosystem API endpoints may have rate limits
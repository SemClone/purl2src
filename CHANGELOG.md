# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- GitHub: a versioned PURL is answered with an archive of the ref asked for
  rather than the repository clone URL. The clone URL resolves whatever ref you
  name, so a tag that does not exist came back `validated=True`, and a consumer
  handing it to `tarfile.open` extracted zero files without an error (#33).
- GitHub: the archive URL is built as `/archive/{ref}.tar.gz` rather than
  `/archive/refs/tags/{ref}.tar.gz`. The old form only resolves tags, so it
  404'd for a branch that exists, and it cannot resolve a commit sha at all.

### Changed
- A versioned `pkg:github/*` PURL now returns a `.tar.gz` archive URL where it
  previously returned a `.git` clone URL. A versionless PURL still returns the
  clone URL, which is the honest answer when there is no ref to archive.

## [1.3.0] - 2026-08-31

### Fixed
- npm: a version the registry does not carry no longer resolves to the latest
  release. The API level fell back to `dist-tags.latest`, whose tarball URL
  resolves, so the substitution was reported as `validated=True` under the
  requested coordinate (#30).
- RubyGems: the same substitution via the gems endpoint, which describes the
  gem's latest release. A `gem_uri` is now returned only when it names the
  requested version, and the repository URLs in `source_code_uri` /
  `homepage_uri` are offered only when no version was requested, since a clone
  URL says nothing about which version it would give you.

### Changed
- A request for an npm or RubyGems version that cannot be resolved now
  reports `status="failed"` with no `download_url`, where it previously
  reported `status="success"` with another version's artifact. Callers that
  treated a successful result as proof the coordinate existed will now see
  those cases fail, which is the point of the change.

## [1.2.4] - 2026-03-15

### Security
- Updated urllib3 from >=2.5.0 to >=2.6.3 to address multiple high-severity vulnerabilities:
  - CVE-2026-21441: Decompression-bomb safeguards bypassed when following HTTP redirects (streaming API)
  - CVE-2025-66471: Streaming API improperly handles highly compressed data
  - CVE-2025-66418: Unbounded number of links in the decompression chain

## [1.2.3] - 2025-10-27

### Changed
- Project renamed from `semantic-copycat-purl2src` to `purl2src`
- Repository moved to https://github.com/SemClone/purl2src
- Updated all package references, URLs, and documentation to reflect new name
- Updated PyPI package name to `purl2src`

## [1.2.2] - 2025-10-22

### Documentation
- Added link to LICENSE file in README.md
- General documentation improvements and cleanup

### Maintenance
- Added git commit message template (.gitmessage)
- Added git hook to prevent commits with prohibited terms
- Code cleanup and maintenance

## [1.2.1] - 2025-10-22

### Security
- Updated urllib3 to v2.5.0 to address security vulnerability
- Fixed URL substring sanitization vulnerability in RubyGems handler that could potentially allow malicious URL injection

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
- Initial release of purl2src
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
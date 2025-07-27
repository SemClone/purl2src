# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Semantic Copycat Purl2Src (CopycatP2S) is a Python tool (CLI) and library that translates Package URLs (PURLs) into validated download URLs for obtaining source code artifacts. It supports multiple ecosystems with API fallbacks and package manager integration.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run tests
pytest
pytest -v  # verbose
pytest tests/test_parser.py  # specific test file
pytest -k "test_npm"  # run tests matching pattern

# Linting and formatting
black src/ tests/
flake8 src/ tests/
mypy src/

# Build package for PyPI
python -m build

# CLI usage
purl2src "pkg:npm/express@4.17.1"
purl2src "pkg:pypi/requests@2.28.0" --validate
purl2src -f purls.txt --output results.json
```

## Architecture Overview

### Core Components

1. **PURL Parser** (src/purl2src/parser.py)
   - Parses Package URLs into components: ecosystem, namespace, name, version, qualifiers
   - Special handling for GoLang repositories with complex path structures
   - Validates PURL format according to spec

2. **Ecosystem Handlers** (src/purl2src/handlers/)
   - Base handler class: BaseHandler with common validation logic
   - Each ecosystem has its own handler module (npm.py, pypi.py, etc.)
   - Implements: direct URL construction, API queries, fallback mechanisms
   - Currently implemented: NPM, PyPI, Cargo, NuGet, GitHub, Generic, Conda, GoLang, Ruby Gems, Maven

3. **Package Manager Interface** (src/purl2src/package_managers.py)
   - Detects installed package managers using shutil.which()
   - Executes fallback commands safely with subprocess
   - Parses command output to extract download URLs
   - Handles command failures gracefully

4. **Validation System** (src/purl2src/validator.py)
   - HTTP HEAD/GET requests for URL verification
   - SHA256 checksum validation when provided
   - Connection pooling with requests.Session()
   - Timeout handling and retry logic

5. **CLI Interface** (src/purl2src/cli.py)
   - Click-based CLI with multiple input options
   - Batch processing from files
   - JSON/CSV output formats
   - Progress bars for large batches

### Key Implementation Patterns

1. **Handler Registry Pattern**:
   ```python
   HANDLERS = {
       'npm': NpmHandler,
       'pypi': PyPiHandler,
       'cargo': CargoHandler,
       # ...
   }
   ```

2. **Three-Level Resolution Strategy**:
   - Level 1: Direct URL construction based on known patterns
   - Level 2: API queries to package registries
   - Level 3: Package manager command fallback

3. **Standardized Response Format**:
   ```python
   {
       "purl": "pkg:npm/express@4.17.1",
       "download_url": "https://registry.npmjs.org/express/-/express-4.17.1.tgz",
       "validated": True,
       "method": "direct",  # or "api" or "fallback"
       "fallback_command": "npm view express@4.17.1 dist.tarball"
   }
   ```

4. **Error Response Format**:
   ```python
   {
       "purl": "pkg:npm/invalid-package@1.0.0",
       "download_url": None,
       "status": "failed",
       "error": "HTTP-404: Package not found",
       "fallback_available": True
   }
   ```

### Ecosystem-Specific Implementation Details

#### NPM (src/purl2src/handlers/npm.py)
- URL Pattern: `https://registry.npmjs.org/{namespace/}name/-/name-version.tgz`
- Scoped packages: Convert `%40` to `@` for API calls
- Fallback: `npm view {package}@{version} dist.tarball`

#### PyPI (src/purl2src/handlers/pypi.py)
- Primary: Query `https://pypi.org/pypi/{package}/json` for download URLs
- Fallback pattern: `https://pypi.python.org/packages/source/{first_letter}/{name}/{name}-{version}.tar.gz`
- Package manager: `pip download --no-deps --no-binary :all: {package}=={version}`

#### Cargo (src/purl2src/handlers/cargo.py)
- URL: `https://crates.io/api/v1/crates/{name}/{version}/download`
- No API query needed, direct URL works
- Fallback: `cargo search {package} --limit 1`

#### GoLang (src/purl2src/handlers/golang.py)
- Complex path parsing for github.com, golang.org, etc.
- Proxy URL: `https://proxy.golang.org/{encoded_module_path}/@v/{version}.zip`
- Requires URL encoding of module paths
- Fallback: `go mod download -json {module}@{version}`

#### Maven (src/purl2src/handlers/maven.py)
- URL: `{repository_url}/{group_path}/{artifact}/{version}/{artifact}-{version}[-{classifier}].{type}`
- Group ID dots to slashes: `org.apache.commons` → `org/apache/commons`
- Supports qualifiers: repository_url, classifier, type
- Fallback: `mvn dependency:get -Dartifact={group}:{artifact}:{version}`

#### Generic (src/purl2src/handlers/generic.py)
- Qualifier-based resolution:
  - `download_url`: Direct download URL
  - `vcs_url`: Git repository URL with optional commit
  - `checksum`: SHA256 for validation
- Git operations for VCS URLs with specific commits

## Package Structure

```
semantic-copycat-purl2src/
├── src/
│   └── purl2src/
│       ├── __init__.py
│       ├── __main__.py      # Entry point for CLI
│       ├── cli.py           # Click CLI implementation
│       ├── parser.py        # PURL parsing logic
│       ├── validator.py     # URL validation and checksums
│       ├── package_managers.py  # Package manager detection/execution
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── base.py     # BaseHandler abstract class
│       │   ├── npm.py
│       │   ├── pypi.py
│       │   ├── cargo.py
│       │   ├── nuget.py
│       │   ├── github.py
│       │   ├── generic.py
│       │   ├── conda.py
│       │   ├── golang.py
│       │   ├── rubygems.py
│       │   └── maven.py
│       └── utils/
│           ├── __init__.py
│           ├── http.py      # HTTP client with pooling
│           └── cache.py     # Local caching logic
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_handlers/
│   │   ├── test_npm.py
│   │   ├── test_pypi.py
│   │   └── ...
│   └── test_cli.py
├── pyproject.toml          # Modern Python packaging
├── setup.py               # Backwards compatibility
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Development dependencies
└── tox.ini               # Testing across Python versions
```

## Important Considerations

1. **Security**:
   - Use shlex.quote() for all shell command arguments
   - Validate URLs before making requests
   - Never execute arbitrary code from packages
   - Use subprocess with shell=False

2. **Performance**:
   - requests.Session() for connection pooling
   - concurrent.futures for parallel PURL processing
   - LRU cache for resolved URLs
   - Lazy loading of handlers

3. **Error Handling**:
   - Custom exceptions: PurlParseError, HandlerError, ValidationError
   - Graceful degradation through fallback levels
   - Detailed error messages for debugging
   - Structured logging with levels

4. **Extensibility**:
   - New handlers inherit from BaseHandler
   - Register in HANDLERS dictionary
   - Follow existing handler patterns
   - Add comprehensive tests

5. **Testing Strategy**:
   - Unit tests for each component
   - Integration tests with mock HTTP responses
   - End-to-end tests with real packages (marked slow)
   - Test coverage target: 90%+

## Adding New Ecosystems

1. Create new handler in `src/purl2src/handlers/`
2. Inherit from `BaseHandler`
3. Implement required methods:
   - `build_download_url()`: Direct URL construction
   - `get_download_url_from_api()`: API query logic
   - `get_fallback_cmd()`: Package manager command
4. Add to HANDLERS registry
5. Write comprehensive tests
6. Update documentation
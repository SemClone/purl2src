# PURL2SRC - Package URL to Source Download URLs

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/purl2src.svg)](https://pypi.org/project/purl2src/)

Translate Package URLs (PURLs) into validated download URLs for source code artifacts across multiple package ecosystems. Provides a reliable three-tier resolution strategy with URL validation and batch processing capabilities for automated source code retrieval workflows.

## Features

- **Multi-Ecosystem Support**: NPM, PyPI, Cargo, NuGet, GitHub, Maven, RubyGems, Go, Conda, and more
- **Smart Resolution Strategy**: Three-level approach from direct URL construction to API queries and local fallback
- **URL Validation**: Verify download URLs are accessible before returning results
- **SEMCL.ONE Integration**: Seamlessly integrates with other ecosystem tools for comprehensive source analysis

## Installation

```bash
pip install purl2src
```

For development:
```bash
git clone https://github.com/SemClone/purl2src.git
cd purl2src
pip install -e .
```

## Quick Start

```bash
# Convert a single PURL to download URL
purl2src "pkg:npm/express@4.17.1"

# Batch process multiple PURLs with validation
purl2src -f purls.txt --validate --output results.json
```

## Usage

### CLI Usage

```bash
# Single PURL with default text output
purl2src "pkg:npm/express@4.17.1"
# Output: pkg:npm/express@4.17.1 -> https://registry.npmjs.org/express/-/express-4.17.1.tgz

# JSON output format
purl2src "pkg:npm/express@4.17.1" --format json

# With URL validation
purl2src "pkg:pypi/requests@2.28.0" --validate

# Batch processing from file
purl2src -f purls.txt --output results.json

# CSV output format
purl2src -f purls.txt --format csv --output results.csv
```

### Python API

```python
from purl2src import get_download_url

# Get download URL for a PURL
result = get_download_url("pkg:npm/express@4.17.1")
print(result.download_url)
# https://registry.npmjs.org/express/-/express-4.17.1.tgz

# With validation (recommended for production)
result = get_download_url("pkg:pypi/requests@2.28.0", validate=True)

# Batch processing
from purl2src import process_purls
results = process_purls(["pkg:npm/express@4.17.1", "pkg:pypi/requests@2.28.0"])
```

## Supported Ecosystems

| Ecosystem | PURL Type | Example |
|-----------|-----------|---------|
| NPM | `npm` | `pkg:npm/@angular/core@12.0.0` |
| PyPI | `pypi` | `pkg:pypi/django@4.0.0` |
| Cargo | `cargo` | `pkg:cargo/serde@1.0.0` |
| NuGet | `nuget` | `pkg:nuget/Newtonsoft.Json@13.0.1` |
| Maven | `maven` | `pkg:maven/org.apache.commons/commons-lang3@3.12.0` |
| RubyGems | `gem` | `pkg:gem/rails@7.0.0` |
| Go | `golang` | `pkg:golang/github.com/gin-gonic/gin@v1.8.0` |
| GitHub | `github` | `pkg:github/facebook/react@v18.0.0` |
| Conda | `conda` | `pkg:conda/numpy@1.23.0?channel=conda-forge&subdir=linux-64&build=py39h1234567_0` |
| Generic | `generic` | `pkg:generic/package@1.0.0?download_url=https://example.com/file.tar.gz` |

## Examples

### NPM with Scoped Package
```bash
purl2src "pkg:npm/@angular/core@12.0.0"
# Output: https://registry.npmjs.org/@angular/core/-/core-12.0.0.tgz
```

### Maven with Classifier
```bash
purl2src "pkg:maven/org.apache.xmlgraphics/batik-anim@1.9.1?classifier=sources"
# Output: https://repo.maven.apache.org/maven2/org/apache/xmlgraphics/batik-anim/1.9.1/batik-anim-1.9.1-sources.jar
```

### Generic with Checksum Validation
```bash
purl2src "pkg:generic/mypackage@1.0.0?download_url=https://example.com/pkg.tar.gz&checksum=sha256:abcd1234..."
```

## Integration with SEMCL.ONE

PURL2SRC is a core component of the SEMCL.ONE ecosystem, enabling automated source code retrieval workflows:

- Works with **src2purl** for package identification and coordinate extraction
- Integrates with **purl2notices** for legal notice generation from source packages
- Supports **upmex** package metadata extraction workflows
- Complements **osslili** for comprehensive license analysis of downloaded sources

## Documentation

- [User Guide](docs/user-guide.md) - Comprehensive usage examples and configuration
- [API Reference](docs/api.md) - Python API documentation and examples
- [Examples](docs/examples.md) - Common workflows and integration patterns

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Code of conduct
- Development setup
- Submitting pull requests
- Reporting issues

## Support

For support and questions:
- [GitHub Issues](https://github.com/SemClone/purl2src/issues) - Bug reports and feature requests
- [Documentation](https://github.com/SemClone/purl2src) - Complete project documentation
- [SEMCL.ONE Community](https://semcl.one) - Ecosystem support and discussions

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Authors

See [AUTHORS.md](AUTHORS.md) for a list of contributors.

---

*Part of the [SEMCL.ONE](https://semcl.one) ecosystem for comprehensive OSS compliance and code analysis.*

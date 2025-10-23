# PURL2SRC - Package URL (PURL) to Source

Translate Package URLs (PURLs) into validated download URLs for source code artifacts.

## Features

- **Multi-ecosystem support**: NPM, PyPI, Cargo, NuGet, GitHub, Maven, RubyGems, Go, Conda, and more
- **Three-level resolution strategy**:
  1. Direct URL construction based on known patterns
  2. Package registry API queries
  3. Local package manager fallback
- **URL validation**: Verify download URLs are accessible
- **Batch processing**: Process multiple PURLs from files
- **Multiple output formats**: JSON, CSV, or plain text
- **Extensible architecture**: Easy to add new package ecosystems

## Installation

```bash
pip install semantic-copycat-purl2src
```

## Usage

### Command Line

```bash
# Single PURL (default text output)
purl2src "pkg:npm/express@4.17.1"
# Output: pkg:npm/express@4.17.1 -> https://registry.npmjs.org/express/-/express-4.17.1.tgz

# JSON output format
purl2src "pkg:npm/express@4.17.1" --format json

# With validation
purl2src "pkg:pypi/requests@2.28.0" --validate

# Batch processing from file
purl2src -f purls.txt --output results.json

# Batch processing with JSON to stdout
purl2src -f purls.txt --format json
```

### Python API

```python
from purl2src import get_download_url

# Get download URL for a PURL
result = get_download_url("pkg:npm/express@4.17.1")
print(result.download_url)
# https://registry.npmjs.org/express/-/express-4.17.1.tgz

# Without validation (faster)
result = get_download_url("pkg:pypi/requests@2.28.0", validate=False)
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

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details

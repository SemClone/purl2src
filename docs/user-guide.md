# PURL2SRC - User Guide

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Understanding PURLs](#understanding-purls)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Supported Ecosystems](#supported-ecosystems)
- [Troubleshooting](#troubleshooting)

## Introduction

PURL2SRC translates Package URLs (PURLs) into validated download URLs for source code artifacts. It provides a reliable way to retrieve source code across multiple package ecosystems.

### Key Concepts

- **PURL (Package URL)**: A standardized format for identifying packages across ecosystems
- **Download URL**: Direct link to download the source code artifact
- **Resolution Strategy**: Three-level approach to find download URLs

## Installation

### From PyPI

```bash
pip install purl2src
```

### From Source

```bash
git clone https://github.com/SemClone/purl2src.git
cd purl2src
pip install -e .
```

### Verify Installation

```bash
purl2src --version
```

## Understanding PURLs

### PURL Format

A PURL follows this general format:
```
pkg:ECOSYSTEM/NAMESPACE/NAME@VERSION?QUALIFIERS#SUBPATH
```

Examples:
- `pkg:npm/express@4.17.1` - NPM package
- `pkg:pypi/django@4.0.0` - Python package
- `pkg:maven/org.apache.commons/commons-lang3@3.12.0` - Maven package
- `pkg:github/facebook/react@v18.0.0` - GitHub repository

### Components

- **Ecosystem**: Package type (npm, pypi, maven, etc.)
- **Namespace**: Optional grouping (e.g., org.apache.commons)
- **Name**: Package name
- **Version**: Package version
- **Qualifiers**: Optional key-value pairs
- **Subpath**: Optional path within package

## Basic Usage

### Single PURL Resolution

```bash
# Basic usage - returns download URL
purl2src "pkg:npm/express@4.17.1"

# Output:
# pkg:npm/express@4.17.1 -> https://registry.npmjs.org/express/-/express-4.17.1.tgz
```

### With Validation

```bash
# Verify the download URL is accessible
purl2src "pkg:pypi/requests@2.28.0" --validate
```

### Different Output Formats

```bash
# JSON output
purl2src "pkg:npm/express@4.17.1" --format json

# CSV output
purl2src "pkg:npm/express@4.17.1" --format csv
```

## Advanced Features

### Batch Processing

Create a file with multiple PURLs:

```text
# purls.txt
pkg:npm/express@4.17.1
pkg:pypi/django@4.0.0
pkg:maven/org.apache.commons/commons-lang3@3.12.0
```

Process the file:

```bash
# Process batch with default text output
purl2src -f purls.txt

# Save results to JSON file
purl2src -f purls.txt --format json --output results.json

# Save as CSV
purl2src -f purls.txt --format csv --output results.csv
```

### Resolution Strategy

PURL2SRC uses a three-level resolution strategy:

1. **Direct URL Construction**: Uses known patterns for each ecosystem
2. **Registry API Queries**: Queries package registries for metadata
3. **Local Fallback**: Uses local package managers if available

### Validation Options

```bash
# Validate all URLs (slower but ensures accessibility)
purl2src -f purls.txt --validate

# Skip validation for faster processing
purl2src -f purls.txt --no-validate
```

## Supported Ecosystems

### NPM (Node.js)

```bash
# Regular package
purl2src "pkg:npm/express@4.17.1"

# Scoped package
purl2src "pkg:npm/@angular/core@12.0.0"

# With dist-tag
purl2src "pkg:npm/react@latest"
```

### PyPI (Python)

```bash
# Regular package
purl2src "pkg:pypi/requests@2.28.0"

# With classifier
purl2src "pkg:pypi/numpy@1.23.0"
```

### Maven (Java)

```bash
# Basic artifact
purl2src "pkg:maven/org.apache.commons/commons-lang3@3.12.0"

# With classifier
purl2src "pkg:maven/org.apache.xmlgraphics/batik-anim@1.9.1?classifier=sources"

# With type
purl2src "pkg:maven/org.springframework/spring-core@5.3.20?type=jar"
```

### Cargo (Rust)

```bash
purl2src "pkg:cargo/serde@1.0.140"
purl2src "pkg:cargo/tokio@1.20.0"
```

### NuGet (.NET)

```bash
purl2src "pkg:nuget/Newtonsoft.Json@13.0.1"
purl2src "pkg:nuget/Microsoft.Extensions.Logging@6.0.0"
```

### GitHub

```bash
# Release tag
purl2src "pkg:github/facebook/react@v18.0.0"

# Commit hash
purl2src "pkg:github/torvalds/linux@5f9e832c1370"
```

### RubyGems

```bash
purl2src "pkg:gem/rails@7.0.0"
purl2src "pkg:gem/bundler@2.3.0"
```

### Go Modules

```bash
purl2src "pkg:golang/github.com/gin-gonic/gin@v1.8.0"
purl2src "pkg:golang/golang.org/x/net@v0.0.0-20220127200216-cd36cc0744dd"
```

### Conda

```bash
# With channel and subdir
purl2src "pkg:conda/numpy@1.23.0?channel=conda-forge&subdir=linux-64"

# With build string
purl2src "pkg:conda/python@3.9.0?build=h1234567_0"
```

### Generic

```bash
# With explicit download URL
purl2src "pkg:generic/mypackage@1.0.0?download_url=https://example.com/mypackage-1.0.0.tar.gz"

# With checksum validation
purl2src "pkg:generic/mypackage@1.0.0?download_url=https://example.com/pkg.tar.gz&checksum=sha256:abcd1234..."
```

## Troubleshooting

### Common Issues

#### Invalid PURL Format

**Error**: `Invalid PURL format`

**Solution**: Ensure your PURL follows the correct format:
- Starts with `pkg:`
- Has ecosystem type
- Includes package name
- Has version with `@`

#### Package Not Found

**Error**: `Package not found in registry`

**Solutions**:
1. Verify package name and version exist
2. Check ecosystem type is correct
3. Try without validation flag

#### Network Issues

**Error**: `Connection timeout`

**Solutions**:
1. Check internet connection
2. Try with `--timeout 60` for slower connections
3. Use `--no-validate` to skip URL verification

#### Validation Failures

**Error**: `URL validation failed`

**Solutions**:
1. The package might be private or removed
2. Try different version
3. Skip validation with `--no-validate`

### Debug Mode

For detailed troubleshooting:

```bash
# Enable verbose output
purl2src "pkg:npm/express@4.17.1" --verbose

# With debug logging
PURL2SRC_DEBUG=1 purl2src "pkg:npm/express@4.17.1"
```

### Environment Variables

```bash
# Set timeout
export PURL2SRC_TIMEOUT=60

# Set output format
export PURL2SRC_FORMAT=json

# Enable debug mode
export PURL2SRC_DEBUG=1
```

## Integration Examples

### Shell Script

```bash
#!/bin/bash
# download_sources.sh

while IFS= read -r purl; do
    url=$(purl2src "$purl" --no-validate | cut -d' ' -f3)
    if [ ! -z "$url" ]; then
        wget "$url" -P downloads/
    fi
done < purls.txt
```

### Makefile

```makefile
download-deps:
	@mkdir -p sources
	@purl2src -f purls.txt --format json | \
		jq -r '.[] | .download_url' | \
		xargs -I {} wget {} -P sources/
```

### CI/CD Pipeline

```yaml
# .github/workflows/download-sources.yml
- name: Download source packages
  run: |
    pip install purl2src
    purl2src -f purls.txt --validate --output urls.txt
    cat urls.txt | cut -d' ' -f3 | xargs -n1 wget -P sources/
```

## Best Practices

1. **Always validate in production**: Use `--validate` for critical workflows
2. **Cache results**: Save outputs to avoid repeated API calls
3. **Use batch processing**: More efficient than individual PURL resolution
4. **Handle failures gracefully**: Some packages might not resolve
5. **Keep PURLs updated**: Maintain accurate version information

## See Also

- [API Reference](api.md) - Python API documentation
- [Examples](examples.md) - More usage examples
- [PURL Specification](https://github.com/package-url/purl-spec) - Official PURL specification
# PURL2SRC - API Reference

## Table of Contents
- [Overview](#overview)
- [Core Functions](#core-functions)
- [Classes](#classes)
- [Data Types](#data-types)
- [Exceptions](#exceptions)
- [Examples](#examples)

## Overview

The PURL2SRC Python API provides programmatic access to PURL resolution functionality.

## Core Functions

### `get_download_url(purl, validate=False, timeout=30)`

Resolves a PURL to its download URL.

**Parameters:**
- `purl` (str): Package URL to resolve
- `validate` (bool): Whether to validate the URL is accessible
- `timeout` (int): Timeout in seconds for validation

**Returns:**
- `ResolvedPackage`: Object containing resolution results

**Raises:**
- `InvalidPURLError`: If PURL format is invalid
- `ResolutionError`: If resolution fails
- `ValidationError`: If validation fails

**Example:**
```python
from purl2src import get_download_url

result = get_download_url("pkg:npm/express@4.17.1", validate=True)
print(result.download_url)
# https://registry.npmjs.org/express/-/express-4.17.1.tgz
```

### `process_purls(purls, validate=False, parallel=True)`

Process multiple PURLs in batch.

**Parameters:**
- `purls` (List[str]): List of PURLs to process
- `validate` (bool): Whether to validate URLs
- `parallel` (bool): Process in parallel for speed

**Returns:**
- `List[ResolvedPackage]`: List of resolution results

**Example:**
```python
from purl2src import process_purls

purls = [
    "pkg:npm/express@4.17.1",
    "pkg:pypi/requests@2.28.0"
]

results = process_purls(purls, validate=True)
for result in results:
    print(f"{result.purl} -> {result.download_url}")
```

### `validate_purl(purl)`

Validates PURL format without resolving.

**Parameters:**
- `purl` (str): PURL to validate

**Returns:**
- `bool`: True if valid

**Raises:**
- `InvalidPURLError`: If format is invalid

**Example:**
```python
from purl2src import validate_purl

try:
    validate_purl("pkg:npm/express@4.17.1")
    print("Valid PURL")
except InvalidPURLError as e:
    print(f"Invalid: {e}")
```

## Classes

### `PURLResolver`

Main class for PURL resolution with configuration options.

```python
from purl2src import PURLResolver

resolver = PURLResolver(
    validate=True,
    timeout=30,
    cache_enabled=True,
    max_retries=3
)
```

#### Methods

##### `resolve(purl)`

Resolves a single PURL.

**Parameters:**
- `purl` (str): PURL to resolve

**Returns:**
- `ResolvedPackage`: Resolution result

**Example:**
```python
result = resolver.resolve("pkg:npm/express@4.17.1")
```

##### `resolve_batch(purls)`

Resolves multiple PURLs.

**Parameters:**
- `purls` (List[str]): List of PURLs

**Returns:**
- `List[ResolvedPackage]`: Resolution results

**Example:**
```python
results = resolver.resolve_batch([
    "pkg:npm/express@4.17.1",
    "pkg:pypi/django@4.0.0"
])
```

##### `set_strategy(strategy)`

Sets resolution strategy.

**Parameters:**
- `strategy` (ResolutionStrategy): Strategy to use

**Options:**
- `ResolutionStrategy.DIRECT`: Direct URL construction only
- `ResolutionStrategy.REGISTRY`: Registry API queries only
- `ResolutionStrategy.FALLBACK`: Local package managers only
- `ResolutionStrategy.ALL`: Try all strategies (default)

**Example:**
```python
from purl2src import ResolutionStrategy

resolver.set_strategy(ResolutionStrategy.DIRECT)
```

### `ResolvedPackage`

Result object from PURL resolution.

**Attributes:**
- `purl` (str): Original PURL
- `download_url` (str): Resolved download URL
- `ecosystem` (str): Package ecosystem
- `name` (str): Package name
- `version` (str): Package version
- `namespace` (str): Package namespace (if any)
- `validated` (bool): Whether URL was validated
- `resolution_method` (str): Method used for resolution
- `metadata` (dict): Additional package metadata

**Example:**
```python
result = get_download_url("pkg:npm/express@4.17.1")

print(f"Package: {result.name}")
print(f"Version: {result.version}")
print(f"URL: {result.download_url}")
print(f"Method: {result.resolution_method}")
```

### `PackageRegistry`

Interface to package registries.

```python
from purl2src import PackageRegistry

registry = PackageRegistry("npm")
```

#### Methods

##### `get_package_info(name, version)`

Gets package information from registry.

**Parameters:**
- `name` (str): Package name
- `version` (str): Package version

**Returns:**
- `dict`: Package metadata

**Example:**
```python
info = registry.get_package_info("express", "4.17.1")
print(info["dist"]["tarball"])
```

## Data Types

### `ResolutionStrategy`

Enum for resolution strategies.

```python
from purl2src import ResolutionStrategy

ResolutionStrategy.DIRECT    # Direct URL construction
ResolutionStrategy.REGISTRY  # Registry API queries
ResolutionStrategy.FALLBACK  # Local package managers
ResolutionStrategy.ALL       # Try all methods
```

### `Ecosystem`

Enum for supported ecosystems.

```python
from purl2src import Ecosystem

Ecosystem.NPM       # Node.js packages
Ecosystem.PYPI      # Python packages
Ecosystem.MAVEN     # Java packages
Ecosystem.CARGO     # Rust packages
Ecosystem.NUGET     # .NET packages
Ecosystem.GITHUB    # GitHub repositories
Ecosystem.GEM       # Ruby gems
Ecosystem.GOLANG    # Go modules
Ecosystem.CONDA     # Conda packages
Ecosystem.GENERIC   # Generic packages
```

### `PURLComponents`

Parsed PURL components.

```python
from purl2src import parse_purl

components = parse_purl("pkg:npm/@scope/name@1.0.0?qualifier=value")

print(components.type)       # "npm"
print(components.namespace)  # "@scope"
print(components.name)       # "name"
print(components.version)    # "1.0.0"
print(components.qualifiers) # {"qualifier": "value"}
```

## Exceptions

### `PURLError`

Base exception for all PURL-related errors.

### `InvalidPURLError`

Raised when PURL format is invalid.

```python
from purl2src import InvalidPURLError

try:
    get_download_url("invalid-purl")
except InvalidPURLError as e:
    print(f"Invalid PURL: {e}")
```

### `ResolutionError`

Raised when PURL cannot be resolved.

```python
from purl2src import ResolutionError

try:
    get_download_url("pkg:npm/nonexistent@1.0.0")
except ResolutionError as e:
    print(f"Resolution failed: {e}")
```

### `ValidationError`

Raised when URL validation fails.

```python
from purl2src import ValidationError

try:
    get_download_url("pkg:npm/private-package@1.0.0", validate=True)
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### `UnsupportedEcosystemError`

Raised for unsupported package ecosystems.

```python
from purl2src import UnsupportedEcosystemError

try:
    get_download_url("pkg:unknown/package@1.0.0")
except UnsupportedEcosystemError as e:
    print(f"Unsupported: {e}")
```

## Examples

### Basic Usage

```python
from purl2src import get_download_url

# Simple resolution
result = get_download_url("pkg:npm/express@4.17.1")
print(result.download_url)
```

### Batch Processing

```python
from purl2src import process_purls

# Read PURLs from file
with open("purls.txt") as f:
    purls = [line.strip() for line in f]

# Process all PURLs
results = process_purls(purls, validate=True, parallel=True)

# Save results
import json
with open("results.json", "w") as f:
    json.dump([r.__dict__ for r in results], f, indent=2)
```

### Custom Configuration

```python
from purl2src import PURLResolver, ResolutionStrategy

# Configure resolver
resolver = PURLResolver(
    validate=True,
    timeout=60,
    cache_enabled=True,
    cache_dir="~/.purl2src/cache",
    max_retries=5,
    user_agent="MyApp/1.0"
)

# Use specific strategy
resolver.set_strategy(ResolutionStrategy.REGISTRY)

# Resolve
result = resolver.resolve("pkg:pypi/django@4.0.0")
```

### Error Handling

```python
from purl2src import (
    get_download_url,
    InvalidPURLError,
    ResolutionError,
    ValidationError
)

def safe_resolve(purl):
    try:
        result = get_download_url(purl, validate=True)
        return result.download_url
    except InvalidPURLError:
        return f"Invalid PURL format: {purl}"
    except ResolutionError:
        return f"Could not resolve: {purl}"
    except ValidationError:
        return f"URL not accessible: {purl}"
    except Exception as e:
        return f"Unexpected error: {e}"

url = safe_resolve("pkg:npm/express@4.17.1")
print(url)
```

### Registry Direct Access

```python
from purl2src import PackageRegistry

# Access npm registry directly
npm_registry = PackageRegistry("npm")
info = npm_registry.get_package_info("express", "4.17.1")

print(f"Description: {info['description']}")
print(f"License: {info['license']}")
print(f"Download: {info['dist']['tarball']}")
```

### Async Support

```python
import asyncio
from purl2src import async_get_download_url

async def resolve_async():
    tasks = [
        async_get_download_url("pkg:npm/express@4.17.1"),
        async_get_download_url("pkg:pypi/django@4.0.0"),
        async_get_download_url("pkg:cargo/serde@1.0.0")
    ]

    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(resolve_async())
for result in results:
    print(f"{result.purl} -> {result.download_url}")
```

### Integration with SEMCL.ONE

```python
from purl2src import get_download_url
import subprocess

def download_and_analyze(purl):
    # Resolve PURL to download URL
    result = get_download_url(purl, validate=True)

    # Download the package
    subprocess.run([
        "wget", result.download_url,
        "-O", f"{result.name}-{result.version}.tar.gz"
    ])

    # Extract and analyze with other SEMCL.ONE tools
    subprocess.run([
        "tar", "xzf", f"{result.name}-{result.version}.tar.gz"
    ])

    # Run ossnotices on extracted content
    subprocess.run([
        "ossnotices", f"{result.name}-{result.version}",
        "-o", f"{result.name}-NOTICE.txt"
    ])

    return f"{result.name}-NOTICE.txt"

notice_file = download_and_analyze("pkg:npm/express@4.17.1")
print(f"Notices generated: {notice_file}")
```

## See Also

- [User Guide](user-guide.md) - Complete usage documentation
- [Examples](examples.md) - More code examples
- [PURL Specification](https://github.com/package-url/purl-spec)
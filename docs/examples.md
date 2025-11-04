# PURL2SRC - Examples

## Table of Contents
- [Basic Examples](#basic-examples)
- [Ecosystem-Specific Examples](#ecosystem-specific-examples)
- [Batch Processing](#batch-processing)
- [Integration Workflows](#integration-workflows)
- [Advanced Scenarios](#advanced-scenarios)

## Basic Examples

### Example 1: Simple PURL Resolution

```bash
# Resolve a single PURL
purl2src "pkg:npm/express@4.17.1"

# With validation
purl2src "pkg:npm/express@4.17.1" --validate

# JSON output
purl2src "pkg:npm/express@4.17.1" --format json
```

### Example 2: Multiple Output Formats

```bash
# Text format (default)
purl2src "pkg:pypi/requests@2.28.0"
# Output: pkg:pypi/requests@2.28.0 -> https://files.pythonhosted.org/...

# JSON format
purl2src "pkg:pypi/requests@2.28.0" --format json
# Output: {"purl": "pkg:pypi/requests@2.28.0", "download_url": "...", ...}

# CSV format
purl2src "pkg:pypi/requests@2.28.0" --format csv
# Output: "pkg:pypi/requests@2.28.0","https://files.pythonhosted.org/..."
```

## Ecosystem-Specific Examples

### NPM (Node.js)

```bash
# Regular package
purl2src "pkg:npm/lodash@4.17.21"

# Scoped package
purl2src "pkg:npm/@angular/core@14.0.0"

# Beta version
purl2src "pkg:npm/typescript@4.8.0-beta"

# With specific registry
purl2src "pkg:npm/express@4.17.1?registry=https://npm.pkg.github.com"
```

### PyPI (Python)

```bash
# Standard package
purl2src "pkg:pypi/numpy@1.23.0"

# Pre-release version
purl2src "pkg:pypi/scipy@1.9.0rc1"

# Package with hyphen
purl2src "pkg:pypi/django-rest-framework@3.13.0"
```

### Maven (Java)

```bash
# Basic artifact
purl2src "pkg:maven/org.springframework/spring-core@5.3.20"

# With classifier for sources
purl2src "pkg:maven/org.apache.commons/commons-lang3@3.12.0?classifier=sources"

# With type specification
purl2src "pkg:maven/org.junit.jupiter/junit-jupiter@5.8.2?type=pom"

# Android library
purl2src "pkg:maven/com.google.android.material/material@1.6.0"
```

### Cargo (Rust)

```bash
# Popular crates
purl2src "pkg:cargo/serde@1.0.140"
purl2src "pkg:cargo/tokio@1.20.0"
purl2src "pkg:cargo/async-trait@0.1.56"
```

### NuGet (.NET)

```bash
# Microsoft packages
purl2src "pkg:nuget/Microsoft.Extensions.Logging@6.0.0"

# Popular libraries
purl2src "pkg:nuget/Newtonsoft.Json@13.0.1"
purl2src "pkg:nuget/AutoMapper@11.0.0"
```

### GitHub

```bash
# Release by tag
purl2src "pkg:github/facebook/react@v18.2.0"

# Specific commit
purl2src "pkg:github/torvalds/linux@5f9e832c1370"

# Branch reference
purl2src "pkg:github/nodejs/node@main"
```

### RubyGems

```bash
# Rails framework
purl2src "pkg:gem/rails@7.0.3"

# Popular gems
purl2src "pkg:gem/devise@4.8.1"
purl2src "pkg:gem/sidekiq@6.5.0"
```

### Go Modules

```bash
# Standard library extension
purl2src "pkg:golang/golang.org/x/crypto@v0.0.0-20220622213112-05595931fe9d"

# Popular frameworks
purl2src "pkg:golang/github.com/gin-gonic/gin@v1.8.1"
purl2src "pkg:golang/github.com/gorilla/mux@v1.8.0"
```

### Conda

```bash
# With channel specification
purl2src "pkg:conda/pandas@1.4.3?channel=conda-forge&subdir=linux-64"

# With build string
purl2src "pkg:conda/tensorflow@2.9.1?channel=anaconda&build=gpu_py39h8c0d9a2_0"
```

## Batch Processing

### File-Based Processing

Create a file `purls.txt`:
```text
pkg:npm/express@4.17.1
pkg:npm/@angular/core@14.0.0
pkg:pypi/django@4.0.0
pkg:pypi/requests@2.28.0
pkg:maven/org.springframework.boot/spring-boot@2.7.0
pkg:cargo/serde@1.0.140
pkg:gem/rails@7.0.3
pkg:golang/github.com/gin-gonic/gin@v1.8.1
```

Process the file:
```bash
# Basic processing
purl2src -f purls.txt

# With validation and JSON output
purl2src -f purls.txt --validate --format json -o results.json

# CSV format for spreadsheet import
purl2src -f purls.txt --format csv -o results.csv
```

### Shell Script for Downloading

```bash
#!/bin/bash
# download_packages.sh

OUTPUT_DIR="packages"
mkdir -p "$OUTPUT_DIR"

while IFS= read -r purl; do
    echo "Processing: $purl"

    # Get download URL
    url=$(purl2src "$purl" | awk '{print $3}')

    if [ ! -z "$url" ]; then
        # Extract filename from URL
        filename=$(basename "$url")

        # Download the package
        wget -q "$url" -O "$OUTPUT_DIR/$filename"
        echo "  Downloaded: $filename"
    else
        echo "  Failed to resolve"
    fi
done < purls.txt

echo "Downloads complete. Files in $OUTPUT_DIR/"
```

### Python Script for Batch Processing

```python
#!/usr/bin/env python3
"""batch_resolver.py - Resolve and download packages"""

import json
import subprocess
import requests
from pathlib import Path

def resolve_and_download(purls_file, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Resolve all PURLs
    result = subprocess.run(
        ["purl2src", "-f", purls_file, "--format", "json"],
        capture_output=True,
        text=True
    )

    packages = json.loads(result.stdout)

    for package in packages:
        if package.get("download_url"):
            print(f"Downloading {package['name']}@{package['version']}...")

            # Download file
            response = requests.get(package["download_url"])
            filename = package["download_url"].split("/")[-1]

            # Save file
            output_file = output_dir / filename
            output_file.write_bytes(response.content)

            print(f"  Saved: {filename}")

if __name__ == "__main__":
    resolve_and_download("purls.txt", "downloads")
```

## Integration Workflows

### CI/CD Pipeline Integration

#### GitHub Actions

```yaml
name: Download Dependencies

on:
  push:
    paths:
      - 'dependencies.txt'

jobs:
  download:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Install purl2src
      run: pip install purl2src

    - name: Resolve PURLs
      run: |
        purl2src -f dependencies.txt \
          --validate \
          --format json \
          -o resolved-urls.json

    - name: Download packages
      run: |
        mkdir -p packages
        cat resolved-urls.json | \
          jq -r '.[] | .download_url' | \
          xargs -I {} wget {} -P packages/

    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: packages
        path: packages/
```

#### Jenkins Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'pip install purl2src'
            }
        }

        stage('Resolve Dependencies') {
            steps {
                sh '''
                    purl2src -f dependencies.txt \
                      --validate \
                      --format json \
                      -o resolved.json
                '''
            }
        }

        stage('Download Packages') {
            steps {
                sh '''
                    mkdir -p packages
                    cat resolved.json | \
                      jq -r '.[] | .download_url' | \
                      while read url; do
                        wget "$url" -P packages/
                      done
                '''
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'packages/*'
            }
        }
    }
}
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install purl2src
RUN pip install purl2src

# Copy PURLs list
COPY purls.txt /app/

WORKDIR /app

# Resolve and download packages
RUN purl2src -f purls.txt --format json -o resolved.json && \
    mkdir -p packages && \
    apt-get update && apt-get install -y wget jq && \
    cat resolved.json | jq -r '.[] | .download_url' | \
    xargs -I {} wget {} -P packages/

# Continue with your application setup
COPY . /app
```

### Makefile Integration

```makefile
# Makefile
.PHONY: deps download-deps clean-deps update-deps

DEPS_FILE = dependencies.txt
DEPS_DIR = vendor

# Resolve and download dependencies
deps: $(DEPS_DIR)
	@echo "Dependencies up to date"

$(DEPS_DIR): $(DEPS_FILE)
	@echo "Resolving dependencies..."
	@purl2src -f $(DEPS_FILE) --validate --format json -o resolved.json
	@echo "Downloading packages..."
	@mkdir -p $(DEPS_DIR)
	@cat resolved.json | jq -r '.[] | .download_url' | \
		xargs -n1 -I {} sh -c 'wget -q {} -P $(DEPS_DIR)/ && echo "  Downloaded: $$(basename {})"'
	@touch $(DEPS_DIR)

# Update dependency URLs
update-deps:
	@purl2src -f $(DEPS_FILE) --validate --format json -o resolved.json
	@echo "Updated resolved.json"

# Clean downloaded dependencies
clean-deps:
	@rm -rf $(DEPS_DIR) resolved.json
	@echo "Cleaned dependencies"

# Download specific ecosystem
download-npm:
	@grep "pkg:npm" $(DEPS_FILE) | \
		purl2src -f - --format json | \
		jq -r '.[] | .download_url' | \
		xargs -I {} wget {} -P $(DEPS_DIR)/npm/

download-pypi:
	@grep "pkg:pypi" $(DEPS_FILE) | \
		purl2src -f - --format json | \
		jq -r '.[] | .download_url' | \
		xargs -I {} wget {} -P $(DEPS_DIR)/pypi/
```

## Advanced Scenarios

### Mirror Creation

```bash
#!/bin/bash
# create_mirror.sh - Create local package mirror

MIRROR_DIR="/var/packages/mirror"
PURLS_FILE="all-dependencies.txt"

# Create directory structure
mkdir -p "$MIRROR_DIR"/{npm,pypi,maven,cargo,gem}

# Process each ecosystem separately
for ecosystem in npm pypi maven cargo gem; do
    echo "Processing $ecosystem packages..."

    grep "pkg:$ecosystem" "$PURLS_FILE" | \
    purl2src -f - --validate --format json | \
    jq -r '.[] | .download_url' | \
    while read url; do
        filename=$(basename "$url")
        wget -q "$url" -O "$MIRROR_DIR/$ecosystem/$filename"
        echo "  $ecosystem/$filename"
    done
done

# Create index
find "$MIRROR_DIR" -type f -name "*" > "$MIRROR_DIR/index.txt"
echo "Mirror created with $(wc -l < $MIRROR_DIR/index.txt) packages"
```

### License Compliance Check

```python
#!/usr/bin/env python3
"""compliance_check.py - Download and check licenses"""

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

def check_package_license(purl):
    # Resolve PURL
    result = subprocess.run(
        ["purl2src", purl, "--format", "json"],
        capture_output=True,
        text=True
    )

    package_info = json.loads(result.stdout)[0]

    # Download package
    with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp:
        subprocess.run(["wget", "-q", package_info["download_url"], "-O", tmp.name])

        # Extract and look for license
        # (simplified - actual implementation would handle various formats)
        license_found = "Unknown"

        # Run ossnotices on extracted content
        result = subprocess.run(
            ["ossnotices", tmp.name, "--format", "json"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            notices = json.loads(result.stdout)
            if notices.get("packages"):
                license_found = notices["packages"][0].get("license", "Unknown")

    return {
        "package": f"{package_info['name']}@{package_info['version']}",
        "license": license_found
    }

# Check all packages
with open("purls.txt") as f:
    purls = [line.strip() for line in f]

results = []
for purl in purls:
    print(f"Checking {purl}...")
    results.append(check_package_license(purl))

# Report
print("\nLicense Report:")
print("-" * 40)
for result in results:
    print(f"{result['package']}: {result['license']}")
```

### Dependency Graph Building

```python
#!/usr/bin/env python3
"""dep_graph.py - Build dependency graph from PURLs"""

import json
import subprocess
import networkx as nx
import matplotlib.pyplot as plt

def resolve_purl(purl):
    result = subprocess.run(
        ["purl2src", purl, "--format", "json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)[0]

# Build graph
G = nx.DiGraph()

# Read main dependencies
with open("purls.txt") as f:
    main_deps = [line.strip() for line in f]

# Add nodes
for purl in main_deps:
    info = resolve_purl(purl)
    node_id = f"{info['name']}@{info['version']}"
    G.add_node(node_id, ecosystem=info['ecosystem'])

# Add edges (simplified - actual deps would come from package metadata)
# This is just for visualization
if len(G.nodes) > 1:
    nodes = list(G.nodes)
    for i in range(len(nodes) - 1):
        G.add_edge("root", nodes[i])

# Visualize
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue',
        node_size=1000, font_size=8, arrows=True)
plt.savefig("dependency_graph.png")
print("Dependency graph saved as dependency_graph.png")
```

### Automated Updates

```bash
#!/bin/bash
# check_updates.sh - Check for package updates

PURLS_FILE="dependencies.txt"
UPDATES_FILE="available_updates.txt"

> "$UPDATES_FILE"

while IFS= read -r purl; do
    # Extract package and version
    pkg=$(echo "$purl" | sed 's/@[^@]*$//')
    current_version=$(echo "$purl" | sed 's/.*@//')

    # Get latest version (simplified - would need registry queries)
    latest_purl="${pkg}@latest"

    echo "Checking $pkg..."

    # Try to resolve latest
    if latest_url=$(purl2src "$latest_purl" 2>/dev/null | awk '{print $3}'); then
        if [ ! -z "$latest_url" ]; then
            echo "$purl -> $latest_purl" >> "$UPDATES_FILE"
        fi
    fi
done < "$PURLS_FILE"

if [ -s "$UPDATES_FILE" ]; then
    echo "Updates available:"
    cat "$UPDATES_FILE"
else
    echo "All packages up to date"
fi
```

## See Also

- [User Guide](user-guide.md) - Complete usage documentation
- [API Reference](api.md) - Python API documentation
- [SEMCL.ONE Integration](https://semcl.one) - Ecosystem tools
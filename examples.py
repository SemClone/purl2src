#!/usr/bin/env python
"""Examples of using purl2src library."""

from purl2src import get_download_url


def main():
    """Run examples."""
    # Example PURLs from different ecosystems
    examples = [
        "pkg:npm/express@4.17.1",
        "pkg:npm/@angular/core@12.0.0",
        "pkg:pypi/requests@2.28.0",
        "pkg:cargo/serde@1.0.0",
        "pkg:nuget/Newtonsoft.Json@13.0.1",
        "pkg:maven/org.apache.commons/commons-lang3@3.12.0",
        "pkg:gem/rails@7.0.0",
        "pkg:golang/github.com/gin-gonic/gin@v1.8.0",
        "pkg:github/facebook/react@v18.0.0",
    ]
    
    print("Package URL to Download URL Examples")
    print("=" * 80)
    
    for purl in examples:
        print(f"\nPURL: {purl}")
        try:
            result = get_download_url(purl, validate=False)
            if result.download_url:
                print(f"Download URL: {result.download_url}")
                print(f"Method: {result.method}")
                if result.fallback_command:
                    print(f"Fallback command: {result.fallback_command}")
            else:
                print(f"Error: {result.error}")
        except Exception as e:
            print(f"Exception: {e}")
    
    # Example with qualifiers
    print("\n" + "=" * 80)
    print("\nExamples with qualifiers:")
    
    # Maven with sources
    purl = "pkg:maven/org.apache.xmlgraphics/batik-anim@1.9.1?classifier=sources"
    print(f"\nPURL: {purl}")
    result = get_download_url(purl, validate=False)
    print(f"Download URL: {result.download_url}")
    
    # Generic with download URL
    purl = "pkg:generic/mypackage@1.0.0?download_url=https://example.com/package.tar.gz"
    print(f"\nPURL: {purl}")
    result = get_download_url(purl, validate=False)
    print(f"Download URL: {result.download_url}")


if __name__ == "__main__":
    main()
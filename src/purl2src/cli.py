"""Command-line interface for purl2src."""

import json
import sys
from pathlib import Path
from typing import List, Optional

import click

from . import __version__
from .handlers import get_download_url


@click.command()
@click.version_option(version=__version__, prog_name="purl2src")
@click.argument("purl", required=False)
@click.option(
    "-f", "--file",
    type=click.Path(exists=True, path_type=Path),
    help="Read PURLs from file (one per line)"
)
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    help="Write results to file (JSON format)"
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate that download URLs are accessible"
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "plain"]),
    default="plain",
    help="Output format"
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose output"
)
def main(
    purl: Optional[str],
    file: Optional[Path],
    output: Optional[Path],
    validate: bool,
    format: str,
    verbose: bool,
) -> None:
    """
    Translate Package URLs (PURLs) to download URLs.
    
    Examples:
    
        purl2src "pkg:npm/express@4.17.1"
        
        purl2src "pkg:pypi/requests@2.28.0" --validate
        
        purl2src -f purls.txt --output results.json
    """
    # Collect PURLs to process
    purls: List[str] = []
    
    if purl:
        purls.append(purl)
    
    if file:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    purls.append(line)
    
    if not purls:
        click.echo("Error: No PURLs provided. Use --help for usage.", err=True)
        sys.exit(1)
    
    # Process PURLs
    results = []
    errors = 0
    
    # Only show progress bar for multiple PURLs in verbose mode
    if len(purls) > 1 and verbose:
        purl_list = click.progressbar(
            purls,
            label="Processing PURLs",
            show_pos=True,
        )
    else:
        purl_list = purls
    
    for purl_str in purl_list:
        try:
            result = get_download_url(purl_str, validate=validate)
            results.append(result.to_dict())
            
            if result.status == "failed":
                errors += 1
                
        except Exception as e:
            result_dict = {
                "purl": purl_str,
                "download_url": None,
                "status": "failed",
                "error": str(e),
            }
            results.append(result_dict)
            errors += 1
    
    # Format and output results
    if format == "json":
        output_data = json.dumps(results, indent=2)
    elif format == "csv":
        # Simple CSV output
        lines = ["purl,download_url,status,method"]
        for r in results:
            lines.append(
                f"{r['purl']},{r.get('download_url', '')},"
                f"{r.get('status', 'failed')},{r.get('method', '')}"
            )
        output_data = "\n".join(lines)
    else:  # plain
        lines = []
        for r in results:
            if r.get("download_url"):
                lines.append(f"{r['purl']} -> {r['download_url']}")
            else:
                error_msg = r.get("error", "Failed to resolve")
                lines.append(f"{r['purl']} -> ERROR: {error_msg}")
        output_data = "\n".join(lines)
    
    # Write output
    if output:
        with open(output, "w") as f:
            f.write(output_data)
        if verbose:
            click.echo(f"Results written to {output}")
    else:
        click.echo(output_data)
    
    # Exit with error code if any failures
    if errors > 0:
        if verbose:
            click.echo(f"\nCompleted with {errors} error(s)", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
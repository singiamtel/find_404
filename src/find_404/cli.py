"""Command-line interface for 404 Finder."""

import argparse
import importlib.metadata
import json
import sys
from urllib.parse import urlparse

from .crawler import crawl_site, is_same_domain, setup_logging


def main() -> int:
    """Main entry point for the CLI."""
    # Check if no arguments provided and show examples
    if len(sys.argv) == 1:
        print("find_404 - Crawl websites and find broken links\n")
        print("Usage: find_404 <URL> [options]\n")
        print("Examples:")
        print("  # Check for broken links (console output)")
        print("  find_404 example.com")
        print("")
        print("  # Check for broken links with JSONL output")
        print("  find_404 example.com --format jsonl")
        print("")
        print("For more options, use: find_404 --help")
        return 0
    
    parser = argparse.ArgumentParser(
        description="Crawl a website and check for broken links and size limits",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["console", "jsonl"],
        default="console",
        help="Output format: console (default) or jsonl"
    )
    parser.add_argument(
        "--output", "-o",
        default="-",
        help="Output destination: filename, stdout (default), or '-' for stdout"
    )
    parser.add_argument(
        "--version", action="version", version=f"find_404 {importlib.metadata.version('find_404')}",
    )
    parser.add_argument("URL", help="The URL to start crawling from")
    parser.add_argument(
        "--max-size",
        type=int,
        help="Maximum allowed size in bytes for any page",
        default=None,
    )
    parser.add_argument(
        "--workers", type=int, help="Number of parallel workers", default=10,
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum depth to crawl (default: no limit)",
        default=None,
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Normalize output argument
    if args.output == "-":
        output_destination = "stdout"
        output_file = None
    else:
        output_destination = "file"
        output_file = args.output

    # Setup logging with the new options
    logger = setup_logging(
        verbose=args.verbose,
        format_type=args.format,
        output_destination=output_destination,
        output_file=output_file
    )

    # Get domain name for potential default file naming (fallback)
    if not args.url.startswith(("http://", "https://")):
        args.url = "http://" + args.url
    domain = urlparse(args.url).netloc

    report = crawl_site(args.url, max_workers=args.workers, max_depth=args.max_depth)

    has_errors = False
    size_exceeded = False
    final_errors = []
    
    # Sort URLs by size before output
    sorted_items = sorted(report.items(), key=lambda x: x[1]["size"])
    
    # Output results based on format
    if args.format == "jsonl":
        for url, info in sorted_items:
            result = {
                "url": url,
                "status_code": info["status_code"],
                "size": info["size"],
                "referrer": info.get("referrer"),
            }
            logger.info(json.dumps(result))
    else:  # console format
        logger.info(f"Crawl Results for {args.url}")
        logger.info("=" * 50)
        for url, info in sorted_items:
            status = info["status_code"]
            size = info["size"]
            referrer = info.get("referrer", "N/A")
            logger.info(f"URL: {url}")
            logger.info(f"  Status: {status}")
            logger.info(f"  Size: {size} bytes")
            logger.info(f"  Referrer: {referrer}")
            logger.info("")

    # Check for errors and size violations
    for url, info in sorted_items:
        if isinstance(info["status_code"], int) and 400 <= info["status_code"] < 600:
            final_errors.append(
                f"Error: {url} returned status code {info['status_code']}",
            )
            has_errors = True
        if (
            args.max_size
            and info["size"] > args.max_size
            and is_same_domain(url, args.url)
        ):
            final_errors.append(
                f"Error: {url} exceeds maximum size of {args.max_size} bytes (actual size: {info['size']} bytes)",
            )
            size_exceeded = True

    # Print all collected errors at the end
    for error in final_errors:
        logger.error(error)

    if has_errors or size_exceeded:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

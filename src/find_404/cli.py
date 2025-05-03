"""Command-line interface for 404 Finder."""

import argparse
import json
import sys
from urllib.parse import urlparse
from . import crawl_site, setup_logging
from .crawler import is_same_domain
import importlib.metadata


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Crawl a website and check for broken links and size limits"
    )
    importlib.metadata.version('find_404')
    parser.add_argument(
        "--version", action="version", version=f"find_404 {importlib.metadata.version('find_404')}"
    )
    parser.add_argument("url", help="The URL to start crawling from")
    parser.add_argument(
        "--max-size",
        type=int,
        help="Maximum allowed size in bytes for any page",
        default=None,
    )
    parser.add_argument(
        "--workers", type=int, help="Number of parallel workers", default=10
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        help="Maximum depth to crawl (default: no limit)",
        default=None,
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Get domain name for the output file
    if not args.url.startswith(("http://", "https://")):
        args.url = "http://" + args.url
    domain = urlparse(args.url).netloc
    output_file = f"result_{domain}.jsonl"

    # Setup logging with the output file
    logger = setup_logging(args.verbose, output_file)

    report = crawl_site(args.url, max_workers=args.workers, max_depth=args.max_depth)

    has_errors = False
    size_exceeded = False
    final_errors = []
    # Sort URLs by size before output
    sorted_items = sorted(report.items(), key=lambda x: x[1]["size"])
    # Output in JSONL format
    for url, info in sorted_items:
        result = {
            "url": url,
            "status_code": info["status_code"],
            "size": info["size"],
            "referrer": info.get("referrer"),
        }
        logger.info(json.dumps(result))
        if isinstance(info["status_code"], int) and 400 <= info["status_code"] < 600:
            final_errors.append(
                f"Error: {url} returned status code {info['status_code']}"
            )
            has_errors = True
        if (
            args.max_size
            and info["size"] > args.max_size
            and is_same_domain(url, args.url)
        ):
            final_errors.append(
                f"Error: {url} exceeds maximum size of {args.max_size} bytes (actual size: {info['size']} bytes)"
            )
            size_exceeded = True

    # Print all collected errors at the end
    for error in final_errors:
        logger.error(error)

    print(f"Results written to {output_file}", file=sys.stderr)

    if has_errors or size_exceeded:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

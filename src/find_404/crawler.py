"""Core crawler functionality for finding broken links."""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


def setup_logging(debug=False, output_file=None):
    """Configure logging with handlers for file (INFO) and stderr (ERROR and DEBUG)"""
    # Create our own logger
    logger = logging.getLogger("crawler")
    logger.handlers = []  # Clear any existing handlers
    logger.propagate = False  # Don't propagate to root logger

    # Set base level based on debug flag
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Create formatter
    formatter = logging.Formatter("%(message)s")

    # Create file handler for INFO level (JSONL output)
    if output_file:
        file_handler = logging.FileHandler(output_file, mode="w")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(lambda record: record.levelno == logging.INFO)
        logger.addHandler(file_handler)

    # Create stderr handler for ERROR and DEBUG
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.DEBUG)
    stderr_handler.setFormatter(formatter)
    stderr_handler.addFilter(lambda record: record.levelno != logging.INFO)
    logger.addHandler(stderr_handler)

    return logger


def get_domain(url):
    """Extracts the (scheme, netloc) part of a URL to identify its domain."""
    parsed = urlparse(url)
    return parsed.scheme, parsed.netloc


def normalize_url(url):
    """Normalize URL by removing fragment identifier."""
    parsed = urlparse(url)
    return urljoin(url, parsed.path + ("?" + parsed.query if parsed.query else ""))


def is_same_domain(url, base_domain):
    """Checks whether 'url' is in the same domain or a subdomain of 'base_domain'."""
    scheme, netloc = get_domain(url)
    base_scheme, base_netloc = base_domain

    # Extract the main domain from both URLs by taking the last two parts
    # e.g., 'sub.example.com' -> 'example.com'
    main_domain = ".".join(netloc.split(".")[-2:])
    base_main_domain = ".".join(base_netloc.split(".")[-2:])

    # Don't consider scheme change if it's just http vs https
    schemes_match = (scheme == base_scheme) or (
        scheme in ("http", "https") and base_scheme in ("http", "https")
    )

    return schemes_match and main_domain == base_main_domain


def is_valid_url(url):
    """Check if the URL is valid and not a JavaScript pseudo-URL."""
    if url.startswith(("javascript:", "void(", "#", "tel:", "mailto:")):
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def process_url(url_info):
    """Process a single URL and return its data."""
    url, base_domain, should_recurse, referrer, depth = url_info
    result = {"url": url, "links": [], "referrer": referrer}
    logger = logging.getLogger("crawler")

    if not is_valid_url(url):
        logger.debug(f"Skipping invalid URL: {url}")
        return url, {
            "status_code": "invalid",
            "size": 0,
            "links": [],
            "referrer": referrer,
        }

    try:
        headers = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}
        response = requests.get(url, timeout=10, allow_redirects=True, headers=headers)
        status_code = response.status_code

        if 400 <= status_code < 600:
            logger.error(f"Found error status code {status_code}: {url}")
            return url, {
                "status_code": status_code,
                "size": 0,
                "links": [],
                "referrer": None,
            }
        elif status_code == "error":
            logger.info(f"Found status code {status_code}: {url}")
            return url, {"status_code": 0, "size": 0, "links": [], "referrer": None}

        page_content = response.content
        size_in_bytes = len(page_content)

        # Check if the final URL after redirects is still in our domain
        final_url = response.url
        if not is_same_domain(final_url, base_domain):
            logger.debug(f"URL {url} redirected outside our domain to {final_url}")
            return url, {
                "status_code": status_code,
                "size": size_in_bytes,
                "links": [],
                "referrer": referrer,
            }

        result.update({"status_code": status_code, "size": size_in_bytes})

        # Only proceed if it's HTML
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type.lower():
            soup = BeautifulSoup(page_content, "html.parser")
            for link_tag in soup.find_all("a", href=True):
                raw_link = link_tag.get("href")
                # Use final_url instead of original url
                next_link = urljoin(final_url, raw_link)
                normalized_link = normalize_url(next_link)

                # For internal links - continue crawling with no depth limit
                if is_same_domain(normalized_link, base_domain):
                    # Keep recursing for internal links if within depth limit
                    result["links"].append((normalized_link, True, url, depth + 1))
                # For external links - only check them once (no recursion)
                elif should_recurse:  # Only add external links from internal pages
                    # External links never recurse
                    result["links"].append((normalized_link, False, url, depth + 1))

            logger.debug(f"Found {len(result['links'])} new links from {url}")

    except requests.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return url, {"status_code": "error", "size": 0, "links": [], "referrer": None}

    return url, result


def crawl_site(start_url, max_workers=10, max_depth=None):
    """
    Crawl a website starting from start_url and check for broken links.

    Args:
        start_url (str): The URL to start crawling from
        max_workers (int): Number of parallel workers
        max_depth (int, optional): Maximum depth to crawl

    Returns:
        dict: Results containing status codes and sizes for all URLs
    """
    logger = logging.getLogger("crawler")
    logger.debug(f"Starting crawl from {start_url}")
    if not start_url.startswith(("http://", "https://")):
        start_url = "http://" + start_url

    base_domain = get_domain(start_url)
    logger.debug(f"Base domain: {base_domain[0]}://{base_domain[1]}")

    # Track URLs to process and those we've seen, along with their original referrers
    normalized_start = normalize_url(start_url)
    to_process = [(normalized_start, base_domain, True, None, 0)]
    seen_urls = {normalized_start: None}  # Track referrers in seen_urls
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while to_process:
            future_to_url = {
                executor.submit(process_url, url_info): url_info[0]
                for url_info in to_process
            }

            to_process = []

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    url, data = future.result()
                    data["referrer"] = seen_urls[url]
                    results[url] = data

                    for new_url, new_should_recurse, _, new_depth in data.get(
                        "links", []
                    ):
                        if new_url not in seen_urls and (
                            max_depth is None or new_depth <= max_depth
                        ):
                            seen_urls[new_url] = url
                            to_process.append(
                                (
                                    new_url,
                                    base_domain,
                                    new_should_recurse,
                                    url,
                                    new_depth,
                                )
                            )

                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    results[url] = {
                        "status_code": "error",
                        "size": 0,
                        "referrer": seen_urls.get(url),
                    }

    logger.debug(f"Crawl complete. Visited {len(results)} URLs")
    return results

# 404 Finder

A Python tool to crawl websites and find broken links (404s) and oversized pages.

## Installation

```bash
pip install find_404
```

## Usage

```bash
find_404 example.com [options]
```

### Options

- `--max-size BYTES`: Maximum allowed size in bytes for any page
- `--workers N`: Number of parallel workers (default: 10)
- `--max-depth N`: Maximum depth to crawl (default: no limit)
- `--verbose`: Enable verbose logging

### Example

```bash
# Check for broken links on example.com
find_404 example.com

# Check for broken links and pages larger than 1MB
find_404 example.com --max-size 1000000

# Crawl with 20 parallel workers and verbose logging
find_404 example.com --workers 20 --verbose
```

### Output

The tool generates a JSONL file named `result_domain.jsonl` containing details about each URL visited, including:

- URL
- Status code
- Page size
- Referrer (the page that linked to this URL)

## Features

- Parallel crawling with configurable number of workers
- Finds broken links (HTTP status codes 4xx and 5xx)
- Checks page sizes against a configurable limit
- Follows redirects while staying within the same domain
- Handles both internal and external links
- Generates detailed JSONL reports 
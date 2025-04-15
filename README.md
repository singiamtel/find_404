# 404 Finder

A Python tool to crawl websites and find broken links (404s) and oversized pages.

## Install the CLI

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
- `--version`: Show the version number

### Example

```bash
# Check for broken links on example.com
find_404 example.com

# Check for broken links and pages larger than 1MB
find_404 example.com --max-size 1000000

# Crawl with 20 parallel workers and verbose logging
find_404 example.com --workers 20 --verbose
```

## Use in Github Actions

```yml
name: Check Website Links

on:
  workflow_dispatch: # Manual trigger
  schedule:
    # Every Sunday at midnight
    - cron: '0 0 * * 0'

jobs:
  check-links:
    uses: singiamtel/find_404/.github/workflows/check-links.yml@main
    with:
      url: 'https://example.com'
      max_size: 5000000  # Optional: 5MB limit
      # workers: 12        # Optional: 12 parallel workers
      # max_depth: 5       # Optional: Crawl up to a maximum depth of 5 (only in the original domain, others always have depth 1)
      # verbose: true      # Optional: Enable verbose logging
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

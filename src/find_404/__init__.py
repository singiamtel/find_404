"""find_404 - A tool to find broken links and oversized pages in websites."""

__version__ = "1.1.7"

from .crawler import crawl_site as crawl_site, setup_logging as setup_logging

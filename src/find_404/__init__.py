"""find-404 - A tool to find broken links and oversized pages in websites."""

__version__ = "1.1.3"

from .crawler import crawl_site, setup_logging 

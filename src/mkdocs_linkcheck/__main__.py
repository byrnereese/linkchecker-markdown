"""
Check links in Mkdocs markdown files (as used for static site generation)

% mkdocs-linkcheck ~/myHugoSite/content/posts github.com
% mkdocs-linkcheck ~/myMkdocsSite/docs
"""

import argparse
import logging
import time

from .base import check_links

def main():
    p = argparse.ArgumentParser(description="Check links in markdown files common to mkdocs-generated websites")
    p.add_argument(
        "path",
        help="Path to markdown files")
    p.add_argument(
        "domain",
        help="check only links to this domain (say github.com without https etc.)",
        nargs="?")
    p.add_argument(
        "--ext",
        help="file extension to scan",
        default=".md")
    p.add_argument(
        "-m","--method",
        choices=["get", "head"],
        help="The HTTP method to use when checking external links. The HEAD method is faster but gives false positives. Get is reliable but slower",
        default="get")
    p.add_argument(
        "-v", "--verbose",
        action="store_true")
    p.add_argument(
        "--sync",
        help="don't use asyncio",
        action="store_true")
    p.add_argument(
        "--exclude",
        help="a pattern for a file or path to exclude",
        action="append")
    p.add_argument(
        "-l","--local",
        help="only check local links",
        action="store_true")
    p.add_argument(
        "-r", "--recurse",
        help="recurse directories under path",
        action="store_true")
    P = p.parse_args()

    if P.verbose:
        logging.basicConfig(level=logging.INFO)

    tic = time.monotonic()
    bad = check_links(
        P.path,
        ext=P.ext,
        domain=P.domain,
        method=P.method,
        use_async=not P.sync,
        local=P.local,
        recurse=P.recurse,
        exclude=P.exclude
    )

    print(f"{time.monotonic() - tic:0.3} seconds to check links")

    if bad:
        # using 22 following cURL
        # https://everything.curl.dev/usingcurl/returns
        raise SystemExit(22)


if __name__ == "__main__":
    main()

from __future__ import annotations
import re
import typing as T
from pathlib import Path
import warnings
import asyncio
import itertools
import logging
import os

import aiohttp

from . import files

# tuples, not lists

CWD = os.path.abspath(os.getcwd())
EXC = (
    aiohttp.client_exceptions.ClientConnectorError,
    aiohttp.client_exceptions.ServerDisconnectedError,
)
OKE = asyncio.TimeoutError
TIMEOUT = 10


async def check_urls(
    urls,
    hdr: dict[str, str] = None,
    method: str = "get"
) -> list[tuple[str, str, T.Any]]:
    tasks = [check_url(u, hdr, method=method) for u in urls]


    urls = await asyncio.gather(*tasks)


    # this is per aiohttp manual, when using HTTPS SSL sites, just before closing
    # the event loop, do a 250ms sleep (not for each site)
    await asyncio.sleep(0.250)

    return list(itertools.chain(*urls))  # flatten list of lists


async def check_url(
    url, hdr: dict[str, str] = None, *, method: str = "get"
) -> list[tuple[str, str, T.Any]]:

    bad: list[tuple[str, str, T.Any]] = []

    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    rel_path = os.path.relpath(os.path.abspath(str(url['fn'])), start=CWD)

    try:
        # anti-crawling behavior doesn't like .head() method--.get() is slower but avoids lots of false positives
        async with aiohttp.ClientSession(headers=hdr, timeout=timeout) as session:
            if method == "get":
                async with session.get(url['url'], allow_redirects=True) as response:
                    code = response.status
                    if code != 200: bad.append( [ url['fn'], url['url'], code ] )
            elif method == "head":
                async with session.head(url['url'], allow_redirects=True) as response:
                    code = response.status
                    if code != 200: bad.append( [ url['fn'], url['url'], code ] )
            else:
                raise ValueError(f"Unknown retreive method {method}")
#    except OKE:
#        continue
    except EXC as e:
        bad.append( [ url['fn'], url['url'], e ] )  # e, not str(e)
#        print(f"ERROR: '{rel_path}' '{url['url']}' '{e}'")
#        continue

#    if code != 200:
#        bad.append( [ url['fn'], url['url'], code ] )
#        print(f"ERROR: '{rel_path}' '{url}' {code}")
#    else:
#        logging.info(f"OK: {url['url']:80s}")

    return bad

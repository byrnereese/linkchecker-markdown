from __future__ import annotations
from pathlib import Path
import typing as T
import logging
import re
import asyncio
import os
from operator import itemgetter

from .coro import check_urls as check_urls_async
from .sync import check_urls as check_urls_sync
from . import files

# http://www.useragentstring.com
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0"
SUMMARY = {
    'total': 0,
    'valid': 0,
    'broken': 0,
    'local': 0,
    'remote': 0,
    'empty': 0,
    'skipped': 0,
    'files_checked': 0,
    'problems': {},
    'failure': False
    }

STATUS_LABELS = {
    'alive': '✓',
    'dead': '✖',
    'empty': '-',
    'ignored': '/',
    'error': '⚠'
}

def print_summary():
    total   = SUMMARY['total']
    local   = SUMMARY['local']
    remote  = SUMMARY['remote']
    broken  = SUMMARY['broken']
    empty   = SUMMARY['empty']
    skipped = SUMMARY['skipped']
    files_checked = SUMMARY['files_checked']
    print(f'Total files checked: {files_checked}')
    print(f'Total links checked: {total}')
    print(f'        Local links: {local}')
    print(f'       Remote links: {remote}')
    print(f'        Empty links: {empty}')
    print(f'       Broken links: {broken}')
    print(f'      Skipped links: {skipped}')

    for f in SUMMARY['problems']:
        print(f'\n{f}:')
        urls = SUMMARY['problems'][f]
        for url, problem in urls:
            print(f'[{STATUS_LABELS[problem]}] {url}')

def check_links(
    path: Path,
    domain: str = None,
    *,
    ext: str,
    hdr: dict[str, str] = None,
    method: str = "get",
    use_async: bool = True,
    local: bool = False,
    remote: bool = False,
    recurse: bool = False,
    exclude: [str] = None
) -> T.Iterable[tuple]:

    local_links, remote_links = extract_links( path, ext=ext, recurse=recurse, domain=domain, exclude=exclude )

    if not remote:
        for l in local_links:
            link = l['url']
            if len(link) > 0 and link[0] == "#":
                continue
            # strip any hashtags
            link = re.sub(r'#.*$','',str(link))
            SUMMARY['local'] += 1
            SUMMARY['total'] += 1
            check_local( link, ext=ext, fn=l['fn'], path=l['path'] )        

    """
    This is kind of broken. At this point all of the remote URLs have been discovered, yet
    the legacy library will scan paths again.
    We should pass the list of URLs to test to the helper functions, and not have the 
    helper functons rescan paths. 
    """    
    if not local:
        # TODO: check to see if the URL is in the exclusion list
        SUMMARY['total'] += len(remote_links)
        SUMMARY['remote'] += len(remote_links)
        missing = check_remotes( urls=remote_links, hdr=hdr, method=method, use_async=use_async )
        for fn, url, status in missing:
            if fn not in SUMMARY['problems']: SUMMARY['problems'][fn] = [] 
            SUMMARY['problems'][fn].append( [ url, 'dead' ] )
            SUMMARY['broken'] += 1
        
    bad = None
    if SUMMARY['broken'] > 0: bad = 1

    print_summary()
    return bad

def exclude_link( link, exclude ) -> bool:
    for e in exclude:
        regex = re.compile(e)
        if regex.search( link ):
            return True
    return False

def extract_links( path: Path, ext: str, recurse: bool, domain: str, exclude: [] = None
                  ) -> tuple[ T.Iterable, T.Iterable ]:
    path = Path(path).resolve().expanduser()  # must have .resolve()
    # these look for local and relative links only
    # markdown regex to extract links from [Link label](link url)
    md_regex = r"\]\(([^\)]*)\)"
    md_glob = re.compile(md_regex)
    # markup regex to extract links from <a href="">
    mu_regex = r"<a\s+(?:[^>]*?\s+)?href=([\"\'])(.*?)\1"
    mu_glob = re.compile(mu_regex)
    # TODO: scan for <img src="">

    local = []
    remote = []
    for fn in files.get(path, ext, recurse):
        SUMMARY['files_checked'] += 1 
        mu_hrefs = mu_glob.findall(fn.read_text(errors="ignore"))
        mu_urls = list(map(itemgetter(1), mu_hrefs))
        md_urls = md_glob.findall(fn.read_text(errors="ignore"))
        links = mu_urls + md_urls
        for link in links:
            if link.startswith('mailto:'):
                # Ignore mail links, do nothing for now.
                continue
            elif exclude and exclude_link( link, exclude ):
                SUMMARY['skipped'] += 1
                if fn not in SUMMARY['problems']: SUMMARY['problems'][fn] = [] 
                SUMMARY['problems'][fn].append( [ link, 'ignored' ] )
                continue
            if is_remote_url( link, domain, ext ):
                remote.append( { 'url': link, 'fn': fn, 'path': path } )
            else:
                local.append( { 'url': link, 'fn': fn, 'path': path } )
    return local, remote
                
def is_remote_url( url, domain, ext ) -> bool:
    if domain:
        pat = "https?://" + domain + r"[=a-zA-Z0-9\_\/\?\&\%\+\#\.\-]*"
    else:
        pat = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        #pat = r"https?://[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[=a-zA-Z0-9\_\/\?\&\%\+\#\.\-]+"
    glob = re.compile(pat)
    return glob.search( url )
    
def check_local(url: str, ext: str, fn: str, path: str ): #-> T.Iterable[tuple[str, str]]:
    """check internal links of Markdown files
    this is a simple static analysis; only plain filename references are handled.
    """
    stem = url.strip("/")
    simp_fn = str(fn).strip(ext)
    simp_fn = re.sub(r'index$','',str(simp_fn)) 
    full_path = Path( os.path.join( simp_fn, url ) ).resolve()
    img_glob = re.compile(r'.(png|jpeg|jpg|gif|svg)$',flags=re.IGNORECASE)
    
    if len(url) == 0:
        # URL is empty
        SUMMARY['empty'] += 1
        if fn not in SUMMARY['problems']: SUMMARY['problems'][fn] = [] 
        SUMMARY['problems'][fn].append( [ url, 'empty' ] )
        logging.info(f"Empty link in: {fn}")
    elif img_glob.search(str(full_path)):
        # File is an image
        if not Path(full_path).is_file():
            SUMMARY['broken'] += 1
            if fn not in SUMMARY['problems']: SUMMARY['problems'][fn] = [] 
            logging.info(f"Broken image: {url}")
            SUMMARY['problems'][fn].append( [ url, 'dead' ] )
    else:
        fn1 = str(full_path).rstrip("/") + ext
        fn2 = str(full_path) + '/index' + ext
        if not Path(fn1).is_file() and not Path(fn2).is_file():
            SUMMARY['broken'] += 1
            if fn not in SUMMARY['problems']: SUMMARY['problems'][fn] = [] 
            logging.info(f"Broken link: {url}")
            SUMMARY['problems'][fn].append( [ url, 'dead' ] )
 
def check_remotes(
    urls,
    *,
    hdr: dict[str, str] = None,
    method: str = "get",
    use_async: bool = True
) -> list[tuple[str, str, T.Any]]:

    if not hdr:
        hdr = {"User-Agent": USER_AGENT}

    # %% session
    if use_async:
        missing = asyncio.run(
            check_urls_async( urls, hdr=hdr, method=method )
        )
    else:
        missing = check_urls_sync( urls=urls, hdr=hdr )

    return missing

# Link Checker for Mkdocs-based static generated sites

This project was designed to help validate links associated with markdown-based, staticly generated website -- especially those published via [Mkdocs](https://www.mkdocs.org/). It is a fork of [linkcheckmd](https://github.com/scivision/linkchecker-markdown), and offers many enhancements over its predecessor. This project has the following features:

* Scan and validate links for over 10,000 markdown files per second
* Check local (relative) and remote links
* Recurse through an entire documentation tree
* Check remote links using a synchronous or asynchronous process
* Exclude links from being checked
* Output useful summary reports to help you track down and fix broken links

*While development focused on testing mkdocs-generated sites, this project should in theory work with any markdown-based website generator.*

## Install

For latest release:

```sh
% python -m pip install mkdocs-linkcheck
```

Or, for latest development version.

```sh
% git clone https://github.com/byrnereese/linkchecker-mkdocs
% pip install -e linkchecker-mkdocs
```

## Usage

The static site generator does NOT have to be running for these tests. This program looks at the Markdown .md files directly.

If any local or remote links are determined to be missing, the following happens:

* the file containing the bad link and the link is printed to "stdout"
* the program will exit with code 22 instead of 0 after all files are checked

The bad links are printed to stdout since the normal operation of this program is to check for errors.
Due to the fast, concurrent checking and numerous pages checked, there may be diagnostics printed to stderr.
That way library error messages can be kept separate from the missing page locations printed on stdout.

The examples assume webpage Markdown files have top-level directory ~/docs.

### Python code

```python
import mkdocs-linkcheck as lc
lc.check_links("~/docs")
```

### Command-line

This program may be invoked by either:

```sh
mkdocs-linkcheck
```

or

```sh
python -m mkdocs-linkcheck
```

#### Command link arguments

Usage

> mkdocs-linkcheck [-h] [-ext EXT] [-m {get,head}] [-v] [--sync] [--exclude EXCLUDE] [-local] [-r] path [domain]

Positional arguments:

* `path` - path to Markdown files
* `domain` - check only links to this domain (say github.com without https etc.)

Optional arguments:

* `-h`, `--help` - show a help message and exit
* `-ext <str>` - file extension to scan
* `-m {get,head}`, `--method {get,head}` - The HTTP method to use when testing remote links. The "head" method is faster but gives false positives. The "get" method is reliable but slower
* `--sync` - enable synchronous checking of remote links, or do not use asyncio
* `--exclude str` - a pattern for a file or path to exclude from being checked; use this argument multiple times to exclude multiple files. Regular expressions are ok. 
* `-local` - check local files only
* `-remote` - check remote links only 
* `-r`, `--recurse` - recurse through all directories under path
* `-v` or `--verbose` -prints the URLs as they are checked

### Git precommit

See [./examples/pre-commit](./examples/pre-commit) script for a [Git hook pre-commit](https://www.scivision.dev/git-markdown-pre-commit-linkcheck) Python script.

### Tox and CI

This program can also be used as a check for bad links during continuous integration testing or when using [`tox`](https://tox.readthedocs.io/).


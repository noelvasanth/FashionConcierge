# bs4 shim

This folder provides a minimal, self-contained substitute for BeautifulSoup used by the product parsing tools. It implements only the subset of the API required by the ingestion pipeline to keep parsing deterministic in offline or sandboxed environments.

## When to use

- Local development without installing the full `beautifulsoup4` dependency.
- Test runs that should avoid non-deterministic network or parser behavior.

## Notes

- The shim lives in `__init__.py` and supports `find`, attribute access, and `text` aggregation.
- If you need broader HTML parsing features, prefer adding targeted helpers here rather than pulling in heavy dependencies that may break reproducibility.

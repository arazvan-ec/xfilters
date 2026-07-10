.PHONY: install ingest enrich render build test lint package pages

install:
	pip install -e ".[dev]"

# Usage: make ingest INPUT=path/to/bookmarks.json
ingest:
	python -m xbookmarks ingest $(INPUT)

enrich:
	python -m xbookmarks enrich

render:
	python -m xbookmarks render

build:
	python -m xbookmarks build

test:
	pytest

lint:
	ruff check .

# Package extension/ into dist/xfilters-extension.zip (installable on mobile
# Chromium browsers and attached to GitHub releases by CI).
package:
	./scripts/package-extension.sh

# Refresh the GitHub Pages entry: rebuild the site, then mirror it to docs/,
# which Pages can serve directly (Settings -> Pages -> deploy from branch, /docs).
pages: build
	mkdir -p docs
	cp site/index.html docs/index.html

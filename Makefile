.PHONY: install ingest enrich render build test lint

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

# Plan — X bookmarks catalog

> Plan de implementación para el spec `x-bookmarks-catalog` (SIGNED OFF).
> Status: **PENDING APPROVAL**. Cada tarea lleva su *check local* (lo que prueba que está hecha).

**Dependencias nuevas:** runtime → `anthropic`, `httpx`; dev → `pytest`, `ruff`.
**Paso más arriesgado:** **T4** (fetch al endpoint de sindicación de X) — API pública no
documentada que puede cambiar/romper. Mitigado: mockeado en tests, tolerante a fallos en runtime.
**Modelo de enriquecido:** `claude-sonnet-5` por defecto (equilibrio coste/calidad),
override por env `XBOOKMARKS_MODEL`.

| # | Tarea | Cambia | Check local | Test-first |
| --- | --- | --- | --- | --- |
| T0 | Scaffold del proyecto | `pyproject.toml` (pkg `xbookmarks`, deps), `Makefile` (ingest/enrich/render/build/test), `.gitignore` (`.env`, `__pycache__`, venv), `README.md` esqueleto, `xbookmarks/__init__.py` | `pip install -e .[dev]` ok; `python -c "import xbookmarks"` ok; `ruff check .` limpio; `pytest` corre (0 tests) | no |
| T1 | Modelo `Bookmark` | `xbookmarks/models.py` (dataclass + `to_json_line`/`from_json_line`, defaults de enriquecido) | `tests/test_models.py`: round-trip serialización == original; defaults correctos | **sí** |
| T2 | Store NDJSON | `xbookmarks/store.py` (read/write atómico temp+rename; `merge()` idempotente por `id`, preserva `tags_source=manual`) | `tests/test_store.py`: merge x2 → 0 cambios; tags manuales preservados; fichero válido | **sí** |
| T3 | Adaptadores de ingesta | `xbookmarks/ingest/{base,json_export,url_list}.py` (Protocol `Ingestor`, autodetección) | `tests/test_ingest.py`: JSON export → `RawBookmark`s correctos; lista URLs → `id` parseado | **sí** |
| T4 | Fetch de contenido | `xbookmarks/enrich/fetch.py` (sindicación vía `httpx`, parseo, reintentos+backoff, marca error) | `tests/test_fetch.py` (httpx mockeado): parsea ok; 404 → marcador de error; reintenta transitorios | **sí** |
| T5 | Enriquecido IA | `xbookmarks/enrich/ai.py` (prompt desde `Bookmark`, `anthropic` SDK, parseo `summary`/`topic`/`tags`) | `tests/test_ai.py` (cliente mockeado): devuelve summary + tags; parseo robusto | **sí** |
| T6 | Orquestación enrich | `xbookmarks/enrich/__init__.py` (`enrich_pending(store, limit, force)`: fetch+ai, write-back, preserva manual, `enrich_error` y continúa) | `tests/test_enrich.py` (fetch+ai mockeados): pendientes obtienen summary+tags+`enriched=True`; manual preservado; error no aborta el lote | **sí** |
| T7 | Render catálogo Markdown | `xbookmarks/render/catalog.py` (`catalog/index.md` agrupado por tag) | `tests/test_catalog.py`: el md contiene cada id/url y secciones por tag | **sí** |
| T8 | Render sitio estático | `xbookmarks/render/site.py` (`site/index.html` autocontenido: datos embebidos + JS de búsqueda/filtro por tag, sin deps externas) | `tests/test_site.py`: el html contiene los ids y un `<script>` con los datos | **sí** |
| T9 | CLI + `build` (métrica) | `xbookmarks/cli.py` + `__main__.py` (argparse: ingest/enrich/render/build), `tests/fixtures/sample_bookmarks.json` (N=5) | `tests/test_cli.py` (**test de la métrica de éxito**, fetch/ai mockeados): `build` → ndjson con 5 recs (cada uno summary + ≥1 tag) + site con 5 ids; 2ª ejecución → 0 líneas cambiadas | **sí** |
| T10 | Snippet export + docs | `scripts/export-bookmarks.js` (snippet de consola), README completo (uso, export, `ANTHROPIC_API_KEY`, ToS) | fixture JSON válido; README documenta los 4 comandos + env; suite completa `pytest` verde y `ruff check .` limpio | no |

## Cobertura de las Salvaguardas del spec

- **Secretos** → T0 (`.gitignore` `.env`) + T5 (key desde entorno).
- **Idempotencia** → T2 (merge) + T9 (2ª ejecución = 0 cambios).
- **Fallos de red / ratelimit** → T4 (reintentos, marca error) + T6 (error no aborta el lote).
- **Escrituras atómicas / no pérdida de datos** → T2 (temp+rename).
- **Coste** → T6 (`--limit`, solo pendientes).
- **ToS / adquisición manual** → T10 (snippet de sesión propia + documentación).

## Orden de ejecución

Secuencial T0 → T10. El bucle interno *test-first* (write-failing-test → implement → run →
observe → fix) aplica en T1–T9. Verificación objetiva final con `/flywheel-verify` contra la
métrica del spec (el test de T9), luego `/flywheel-review`.

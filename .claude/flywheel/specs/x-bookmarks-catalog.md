# Spec — X bookmarks catalog

> REASONS contract. Status: **SIGNED OFF (2026-07-08)** · Slug: `x-bookmarks-catalog`

## R — Requirements

**Objetivo:** importar mis bookmarks de X, guardarlos versionados en este repo, enriquecerlos
(resumen, tema, tags) y presentarlos en un formato navegable y buscable.

Diseño en torno a una tubería de 4 etapas desacopladas — **ingest → enrich → store → render** —
para que la parte frágil/cara (obtener los bookmarks) no contamine la parte valiosa
(enriquecer + presentar).

**Dentro (primer corte):**
- Ingesta desde un **JSON de export** (volcado con un snippet de consola que usa la propia
  sesión del usuario) y desde una **lista de URLs de tweets**, vía adaptadores enchufables.
- Almacenamiento como **NDJSON** versionado (fuente de verdad, un registro por tweet).
- Enriquecido **híbrido**: recuperar contenido faltante del endpoint público de sindicación de
  X y generar con Claude `summary`, `topic` y `tags`; los tags manuales del usuario se respetan.
- Presentación: **sitio HTML estático buscable** (filtros por tag + búsqueda, un solo fichero,
  apto para GitHub Pages) + **catálogo Markdown** agrupado por tag.
- Todas las etapas **idempotentes**.

**Fuera (después):**
- Integración con la X API oficial (tier de pago) y automatización de navegador para la ingesta.
- Sync incremental programado, descarga/hosting de media, autenticación/multi-usuario.

## E — Entities

| Entidad | Campos clave |
| --- | --- |
| `Bookmark` | `id` (PK, tweet id) · `url` · `author_handle` · `author_name` · `text` · `created_at` · `media[]` · `thread_ids[]?` · `source` (`json-export`\|`url-list`) · `imported_at` |
| `Bookmark` (enriquecido) | `summary` · `topic` · `tags[]` · `tags_source` (`auto`\|`manual`\|`hybrid`) · `enriched` (bool) · `enriched_at` · `enrich_error?` |
| `RawBookmark` | forma normalizada que devuelve cualquier adaptador de ingesta antes de fusionar en el store |

Relación: el store es una colección de `Bookmark` con **clave única = `id`**; la fusión por id
es lo que garantiza la idempotencia y la preservación de ediciones manuales.

## A — Approach

**Elegido:** tubería con adaptadores enchufables. Ingesta detrás de una interfaz `Ingestor` que
produce `list[RawBookmark]`; el resto (enrich/store/render) no conoce el origen. La adquisición
v1 es manual/gratuita (snippet de consola sobre la sesión propia del usuario, o lista de URLs).

**Alternativa rechazada:** integrar directamente la X API v2 desde el día 1 — más limpio pero
cuesta ~$100/mes (el tier gratis no da bookmarks) y acopla todo el sistema a un proveedor de
pago. Con adaptadores, añadir la API luego es solo otro `Ingestor`.

## S — Structure

```
xbookmarks/                package Python
  models.py                dataclass Bookmark + (de)serialización NDJSON
  ingest/base.py           Protocol Ingestor -> list[RawBookmark]
  ingest/json_export.py    adaptador: JSON del snippet de consola
  ingest/url_list.py       adaptador: lista de URLs de tweets
  enrich/fetch.py          contenido del tweet vía endpoint de sindicación (sin auth)
  enrich/ai.py             Claude: summary/topic/tags
  store.py                 leer/escribir data/bookmarks.ndjson; merge idempotente por id
  render/site.py           genera site/index.html (autocontenido, buscable)
  render/catalog.py        genera catalog/*.md agrupado por tag
  cli.py                   python -m xbookmarks {ingest,enrich,render,build}
data/bookmarks.ndjson      fuente de verdad (en git)
site/index.html            sitio generado
catalog/*.md               catálogo generado
scripts/export-bookmarks.js  snippet de consola para exportar bookmarks
tests/                     pytest (fetch + IA mockeados)
pyproject.toml · Makefile · README.md
```

Dependencias: `render/catalog` y `render/site` leen del `store`; `enrich` escribe al `store`;
`ingest` escribe al `store`. `cli` orquesta. `enrich/ai` es la única que llama a la API de Claude.

## O — Operations

1. `ingest <input>` — detecta el adaptador (JSON export / lista de URLs), normaliza a
   `RawBookmark`, **fusiona en el store por id** (sin enriquecer todavía).
2. `enrich [--force] [--limit N]` — para registros con `enriched=false`: recupera contenido
   faltante vía sindicación, llama a Claude para `summary`/`topic`/`tags`, escribe de vuelta;
   **no pisa** `tags` con `tags_source=manual`.
3. `render` — genera `site/index.html` (búsqueda + filtros por tag) y `catalog/*.md` desde el store.
4. `build` — `enrich` (pendientes) + `render` en una sola orden. `make build` como atajo.

## N — Norms

- Python 3.11+, tipado estático, `dataclasses`. Librería estándar primero; `anthropic` para
  Claude, `httpx` para fetch. Efectos (fs/red) en los bordes; núcleo puro y testeable.
- `ruff` (lint+format) y `pytest`. Los tests **no tocan la red**: `enrich/fetch` y `enrich/ai`
  se mockean. Escrituras de fichero **atómicas** (temp + rename).
- Convenciones de nombres/estilo consistentes en todo el paquete; comentarios sobrios.

## S — Safeguards

- **Secretos:** `ANTHROPIC_API_KEY` desde entorno, nunca en git (`.gitignore`). No se almacenan
  credenciales de X (el snippet usa la sesión del propio navegador del usuario, lado cliente).
- **Idempotencia:** re-ejecutar `ingest`/`enrich`/`render` con entradas iguales cambia 0 filas;
  el merge preserva ediciones manuales (`tags_source=manual`).
- **Fallos de red/ratelimit:** un fetch fallido marca `enrich_error` y continúa (reintentos con
  backoff); nunca aborta el lote entero.
- **Datos:** escritura atómica del NDJSON (temp+rename); un error no trunca la fuente de verdad.
- **Coste:** `enrich` solo procesa pendientes; flag `--limit` para acotar llamadas a la IA.
- **ToS:** v1 no incluye scraping automatizado; la adquisición es manual/sesión propia. Documentado.

## Success metric (lo que comprueba /flywheel-verify)

> Ejecutar `python -m xbookmarks build` sobre el fixture versionado
> `tests/fixtures/sample_bookmarks.json` (N=5) produce:
> 1. `data/bookmarks.ndjson` con **exactamente 5 registros**, cada uno con `summary` no vacío y
>    **≥1 `tag`**;
> 2. `site/index.html` que contiene los 5 tweet ids;
> 3. una **segunda** ejecución de `build` cambia **0 líneas** en `data/bookmarks.ndjson`.
>
> Verificado por `pytest` con `enrich/fetch` y `enrich/ai` **mockeados** (métrica determinista y
> offline). Condición de PASS: toda la suite en verde.

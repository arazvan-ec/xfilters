# Spec — Postgres persistence (Supabase)

> REASONS contract. Status: **DRAFT (2026-07-10)** · Slug: `postgres-persistence`
>
> Makes `CLAUDE.md` point 4 real: agent-run processes persist to Postgres, not
> just NDJSON. An existing (paused) Supabase project **`tweets`**
> (`gwmcfndhxxjnlwqhkace`, org `claude-org`) is the target DB.

## R — Requirements

**Objetivo:** que los procesos ejecutados por una sesión (bookmarks, análisis de
coche, y futuros) puedan persistir en **Postgres/Supabase** a través de la misma
interfaz de store que ya usan, sin reescribir cada proceso.

**Dentro:**
- Backend `supabase` para `xbookmarks/records.RecordStore` (mismo interfaz:
  `load/all/get/upsert/save`), seleccionable con `XBOOKMARKS_BACKEND=supabase`.
- Una tabla genérica por colección **o** una tabla `records(collection, id, data
  jsonb, updated_at)` — decidir en A. Empezar por la genérica `records` (menos
  fricción, una migración sirve para todas las colecciones).
- Migración de datos existentes NDJSON → Postgres (bookmarks) idempotente.
- El adaptador NDJSON sigue siendo el default y el modo offline/test.

**Fuera (después):** RLS/multiusuario, realtime, hosting del site desde la DB,
búsqueda full-text en Postgres.

## E — Entities

| Entidad | Campos |
| --- | --- |
| `records` (tabla genérica) | `collection text` · `id text` · `data jsonb` · `updated_at timestamptz default now()` · PK `(collection, id)` |
| `SupabaseRecordStore` | espejo de `RecordStore`; `save()` hace upsert por `(collection,id)`; `load()` lee las filas de la colección |

## A — Approach

- Añadir `xbookmarks/records_supabase.py` con `SupabaseRecordStore` (import de
  `supabase`/`httpx` perezoso, como en el adaptador Playwright, para no romper el
  import ni los tests sin la dependencia).
- Conexión por env: `SUPABASE_URL`, `SUPABASE_KEY` (service o anon según uso).
  Nunca commitear claves.
- `open_store` ya enruta a este backend (hoy lanza `NotImplementedError` a
  propósito hasta que aterrice el módulo).
- La escritura en Supabase es inmediata en `upsert`+`save` (no hay fichero
  atómico); `save()` puede hacer batch upsert.

## S — Structure

- `xbookmarks/records_supabase.py` (nuevo)
- `supabase/migrations/0001_records.sql` (nuevo — DDL de la tabla `records`)
- `scripts/migrate_ndjson_to_pg.py` (nuevo — vuelca `data/*.ndjson` a la tabla)
- `pyproject.toml`: extra opcional `supabase = ["supabase"]`
- tests: `tests/test_records_supabase.py` con un cliente Supabase **fake**
  inyectado (sin red), igual que el patrón de `test_ai.py`.

## O — Operations

1. Restaurar el proyecto `tweets` (está INACTIVE). **Requiere OK del owner.**
2. Aplicar `0001_records.sql` vía el MCP de Supabase (`apply_migration`).
3. `XBOOKMARKS_BACKEND=supabase python scripts/migrate_ndjson_to_pg.py` para
   subir los bookmarks actuales.
4. A partir de ahí, procesos con `XBOOKMARKS_BACKEND=supabase` escriben en la DB.

## N — Norms

- NDJSON sigue siendo el default y el backend de tests (offline, determinista).
- Ningún proceso habla con Postgres directamente: todo pasa por `open_store`.
- Claves solo por entorno; el `.gitignore` ya cubre `.env`.

## S — Safeguards

- Import perezoso: sin `supabase` instalado, el resto del repo y los tests siguen
  verdes.
- Backend desconocido → `ValueError`; `supabase` sin módulo → `NotImplementedError`.
- La migración de datos es idempotente (upsert por PK), re-ejecutable sin duplicar.
- No se toca el proyecto cloud (restore / DDL / claves) sin confirmación explícita
  del owner — es infraestructura suya.

## Success metric

`XBOOKMARKS_BACKEND=supabase` + credenciales → `analyze-car` y el store de
bookmarks leen/escriben en Postgres y `pytest` sigue verde con el backend NDJSON
por defecto (tests del backend supabase con cliente fake, sin red).

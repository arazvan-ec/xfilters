-- Generic record store for agent-run processes (see
-- .claude/flywheel/specs/postgres-persistence.md). One row per record; `data`
-- holds the whole record as JSONB. One table serves every collection.

create table if not exists public.records (
    collection  text        not null,
    id          text        not null,
    data        jsonb       not null,
    updated_at  timestamptz not null default now(),
    primary key (collection, id)
);

-- Keep updated_at fresh on upsert.
-- search_path pinned to '' so the trigger can't be hijacked via a mutable path
-- (Supabase linter 0011). now() lives in pg_catalog, always resolvable.
create or replace function public.records_touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists records_touch_updated_at on public.records;
create trigger records_touch_updated_at
    before update on public.records
    for each row execute function public.records_touch_updated_at();

-- Fast listing/filtering per collection.
create index if not exists records_collection_idx on public.records (collection);

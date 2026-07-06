# flywheel upgrades applied

## 2026-07-06 — v0.8.0

Applied the strategy from `upgrades/v0.8.0.md` (xmarks@2af19c9):

1. Manifest verified — `.claude/flywheel/.manifest` present (21 entries).
2. Auto-update PR workflow offered to the user — **declined**; this repo
   updates manually via `/flywheel-update` (the SessionStart hook already
   surfaces a notice when a new version is available).
3. No `*.pre-flywheel` backups found — no local edits were overwritten.

---
name: flywheel-update
description: Update flywheel to the latest version — detects whether this repo uses the marketplace install (local CLI/IDE) or the vendored install (Claude Code web), or takes the mode as an argument, then refreshes it and reports old → new version. Use when the user wants to upgrade flywheel or asks which flywheel version a repo carries.
argument-hint: "[vendored|marketplace] (optional — autodetected)"
allowed-tools: Bash, Read, Grep, Glob
---

# /flywheel-update — update flywheel in this repo

Mode requested: **$ARGUMENTS**

flywheel can be installed two ways, and each updates differently. First resolve the mode, then run the matching procedure, then report.

## 1. Resolve the mode

If `$ARGUMENTS` names one, use it — accept aliases: `vendored` / `web` → **vendored**; `marketplace` / `local` / `plugin` → **marketplace**. Otherwise autodetect from the project root:

- **vendored** — `.claude/skills/flywheel-*/` directories exist, or `.claude/flywheel/VERSION` exists.
- **marketplace** — `.claude/settings.json` contains `"flywheel@xmarks"` under `enabledPlugins`.
- **Both present** → do the vendored procedure here, and also give the marketplace instruction at the end.
- **Neither** → flywheel isn't installed in this repo. Point the user to `docs/add-flywheel-to-a-repo.md` in `arazvan-ec/xmarks` and stop.

## 2. Vendored update (the Claude Code web install)

1. **Record the current version**: read `.claude/flywheel/VERSION`. If it doesn't exist, the repo carries a pre-0.5.0 vendored copy — note that as "unknown (< 0.5.0)".
2. **Get the latest xmarks checkout**:
   - If an `arazvan-ec/xmarks` checkout is already available in this session, `git pull origin main` in it.
   - Otherwise `git clone https://github.com/arazvan-ec/xmarks` into a temp/scratchpad directory.
   - In a Claude Code web session where that clone is blocked by the network proxy, add `arazvan-ec/xmarks` to the session first (the `add_repo` tool), then use that checkout.
3. **Run the installer** from the checkout against this repo's root:
   `bash <xmarks>/scripts/install-vendored.sh <repo-root>` — it is idempotent and refreshes the vendored copies in place.
4. **Show what changed**: `.claude/flywheel/VERSION` before → after, plus `git diff --stat -- .claude/`. If the diff is empty, report "already up to date" and stop — do not commit.
5. **Warn about overwritten local edits**: any hand-edits inside `.claude/skills/flywheel-*` or `.claude/agents/` vendored files are clobbered by the refresh; if the diff shows unexpected reverts, surface them before committing.
6. **Commit and push**: commit only the `.claude/` changes with a message like `Update vendored flywheel to <new version>`, and push to the current branch.

## 3. Marketplace update (local CLI/IDE install)

This can't be done from inside the conversation — the plugin manager owns it. Tell the user to run:

```
/plugin update flywheel@xmarks
```

then `/reload-plugins` (or restart the session) to pick it up. No repo changes are involved.

## 4. Report

End with: which mode(s) were updated, old → new version, and the list of changed files (vendored) or the command the user still has to run (marketplace).

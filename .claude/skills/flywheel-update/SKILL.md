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
   `bash <xmarks>/scripts/install-vendored.sh <repo-root>` — it is idempotent and refreshes the vendored copies in place. Keep `--auto-update` if the repo already has `.github/workflows/flywheel-update.yml`.
4. **Apply upgrade strategies** — refreshing files is not always enough; some versions need action in this repo:
   - In the xmarks checkout, list `upgrades/v*.md` and select the notes in the range **(old version, new version]** (compare with `sort -V`; if the old version is unknown, take every note up to the new version).
   - Read each selected note. For notes with `requires-action: true`, execute the steps in its **Strategy** section here in this repo. Strategies are written to be idempotent and verifiable — check each step's "already done" condition before acting, and if a step cannot be automated (e.g. a GitHub UI setting), tell the user exactly what to do instead of skipping it silently.
   - Log what you applied: append a dated entry per executed strategy to `.claude/flywheel/UPGRADES.md` (create it with a `# flywheel upgrades applied` header if missing). Check this log first — a strategy already logged does not need to run again.
   - **Fallback when notes are missing** (updating from a pre-0.8.0 vendor): read the old `source-commit` from the pre-refresh VERSION content and analyze `git -C <xmarks> diff <old-commit>..HEAD -- skills agents scripts hooks` yourself; decide whether anything beyond the file refresh is needed and act accordingly.
5. **Show what changed**: `.claude/flywheel/VERSION` before → after, plus `git diff --stat -- .claude/`. If the diff is empty AND no strategy was applied, report "already up to date" and stop — do not commit. If files are unchanged but a pending strategy was found (e.g. the auto-update PR already refreshed the files), still apply the strategies — that is not a no-op.
6. **Warn about overwritten local edits**: the installer backs up pre-flywheel files as `*.pre-flywheel`; list any under `.claude/` and surface them before committing.
7. **Commit and push**: commit the `.claude/` changes (and `.github/` if a strategy touched the auto-update workflow) with a message like `Update vendored flywheel to <new version>`, noting applied strategies in the body, and push to the current branch.

## 3. Marketplace update (local CLI/IDE install)

This can't be done from inside the conversation — the plugin manager owns it. Tell the user to run:

```
/plugin update flywheel@xmarks
```

then `/reload-plugins` (or restart the session) to pick it up. No repo changes are involved.

Upgrade notes can still require action on marketplace installs: if you can reach the `upgrades/` directory of `arazvan-ec/xmarks` (checkout or raw fetch), review the notes for the new version range and apply any `requires-action` strategy that is relevant to this repo, logging it as in §2.4.

## 4. Report

End with: which mode(s) were updated, old → new version, and the list of changed files (vendored) or the command the user still has to run (marketplace).

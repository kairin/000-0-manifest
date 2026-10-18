# 000-0-manifest — AI Agent Guidelines

Single source of truth for AI agents in this repository. If `CLAUDE.md` or `GEMINI.md` exists, it points to this file.

## Security and secrets

Read `~/Apps/000-0-workspace/docs/repository-protection.md` for shared secret rules.

## Protected files

Do not rewrite these without an explicit per-file instruction from the user: `.gitignore`. Read them freely. If a task needs one changed, stop and ask. `git show origin/main:<file>` is the authoritative original.

## Project overview

This repository lists the repositories in the kairin GitHub account by tier, purpose and status. `scripts/sync_manifest.py` reads the repository list from GitHub and generates the tables in `README.md`, `PERSONAL-PROJECTS.md`, `FORKS.md` and `ARCHIVED.md`. Do not edit the generated tables by hand, because the next sync replaces them. A systemd user timer runs the sync each night on one computer. There is no GitHub Actions workflow.

## Technologies

- Python 3 standard library (`scripts/sync_manifest.py`).
- GitHub CLI (`gh api`) to read repository data.
- JSON configuration: `inventory-config.json` holds approved repository IDs and categories.
- systemd user units in `systemd/`.
- Python `unittest` tests in `tests/`.

## Development workflow

```bash
python3 scripts/sync_manifest.py --dry-run
python3 scripts/sync_manifest.py --check
python3 -m unittest discover -s tests -v
```

`--write` updates the four local pages. `--publish` updates the pages from a dedicated checkout and merges them through a pull request; it never pushes to `main`. See `docs/local-sync.md` for installation, logs and troubleshooting.

A task is done only when you show evidence: command output, a log line or a screenshot.

## Branches and pull requests

- Never push to `main` directly. Make a branch, push it, and open a pull request.
- Keep `CHANGELOG.md` up to date if the repository has one.

## Documentation

- `README.md`: for users.
- `AGENTS.md` (this file): for agents. Update it when a tool, a command or a rule changes.

## Shared workspace policy

Read `~/Apps/000-0-workspace/docs/repository-protection.md` for delivery,
branches, external isolated worktrees, visibility, Git identity, and secrets. Read
`~/Apps/000-0-workspace/docs/agent-instruction-files.md` for pointer rules,
policy routing, owner decisions, unchecked claims, and shared conduct. Read
`~/Apps/000-0-workspace/docs/project-quality-checks.md` for the local baseline
and verification. Read `~/Apps/000-0-workspace/docs/update-and-development-tools.md`
before maintenance work, including retired-boundary rules. These references are
instructions to read. If required policy is missing, the affected task is
incomplete; do not clone, install, or reconstruct it.

## Workflow review follow-up

Keep inventory facts separate from runtime assurance. Do not turn the manifest
job into a doctor or installer. Preserve generated tables and the GitHub About
description source. Link the dated workspace review when workflow ownership or
acceptance evidence changes.

## Inventory metadata and maintenance commands

Descriptions come from GitHub About. Do not edit generated rows by hand.
See `docs/local-sync.md#core-description-maintenance` for the core descriptions.
The nightly inventory sync and AI-owned `update` command are separate.
Do not add tool installation or sudo repair to the inventory job.

# 000-0-manifest — AI Agent Guidelines

Single source of truth for AI agents in this repository. If `CLAUDE.md` or `GEMINI.md` exists, it points to this file.

## Security and secrets

- Never expose, print, log, commit, or include in diffs, prompts, fixtures, screenshots, or generated files any API key, token, password, credential, private key, session cookie, or other secret. Redact with `<REDACTED>`.
- Never ask the user to paste a secret into chat. Do not read or display secret-file contents. If a credential is missing, stop and explain how to provide it securely.
- Secrets live in the owner's `pass` password store. A command gets a secret only through `with-secret <service>/<name> -- <command>`. Never put a secret in `.env`, `.envrc`, `.envrc.local`, source code, config or documentation.
- Do not send personal or sensitive data to an external service unless the user explicitly authorizes it.

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

`--write` updates the four local pages. `--publish` updates and pushes from a dedicated checkout. See `docs/local-sync.md` for installation, logs and troubleshooting.

A task is done only when you show evidence: command output, a log line or a screenshot.

## Branches and pull requests

- Never push to `main` directly. Make a branch, push it, and open a pull request.
- Keep `CHANGELOG.md` up to date if the repository has one.

## Documentation

- `README.md`: for users.
- `AGENTS.md` (this file): for agents. Update it when a tool, a command or a rule changes.

## Git identity

Commit as `Mister K <678459+kairin@users.noreply.github.com>`. This is the
public GitHub name and the GitHub noreply email. Do not commit with another
name or with a personal email address. Check with `git config user.name` and
`git config user.email` before you commit.

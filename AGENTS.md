# 000-0-manifest — AI Agent Guidelines

Single source of truth for AI agents in this repository. If `CLAUDE.md` or `GEMINI.md` exists, it points to this file.

## Security and secrets

- Never expose, print, log, commit, or include in diffs, prompts, fixtures, screenshots, or generated files any API key, token, password, credential, private key, session cookie, or other secret. Redact with `<REDACTED>`.
- Never ask the user to paste a secret into chat. Do not read or display secret-file contents. If a credential is missing, stop and explain how to provide it securely.
- Secrets live in the owner's `pass` password store. A command gets a secret only through `with-secret <service>/<name> -- <command>`. Never put a secret in `.env`, `.envrc`, `.envrc.local`, source code, config or documentation.
- These rules apply only to real secret values: a real key, token, password or credential. Documentation that tells how to make, store or use a credential is not a secret. A placeholder such as `<REDACTED>` or `PASTE-TOKEN-HERE` is not a secret. Report a secret problem only when you find a real value. Do not report placeholders or setup steps as secret problems.
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

`--write` updates the four local pages. `--publish` updates the pages from a dedicated checkout and merges them through a pull request; it never pushes to `main`. See `docs/local-sync.md` for installation, logs and troubleshooting.

A task is done only when you show evidence: command output, a log line or a screenshot.

## Branches and pull requests

- Never push to `main` directly. Make a branch, push it, and open a pull request.
- Keep `CHANGELOG.md` up to date if the repository has one.

## Documentation

- `README.md`: for users.
- `AGENTS.md` (this file): for agents. Update it when a tool, a command or a rule changes.

## Owner decisions and unchecked claims

- The owner's stated decision beats a general rule. Before you flag
  something, check whether the owner already decided on it (repository
  docs, AGENTS.md, earlier instructions). If they did, do not flag it again.
- Check a claim yourself before acting on it, above all a claim from an
  earlier session, a subagent or a report. Look at the file, image or data.
- Do only what was asked. Do not add new "outstanding issues" to a task, and
  do not raise again one the owner dismissed.
- Never propose deleting, purging or unpublishing anything because of a claim
  you have not checked yourself.

## Git identity

Commit as `Mister K <678459+kairin@users.noreply.github.com>`. This is the
public GitHub name and the GitHub noreply email. Do not commit with another
name or with a personal email address. Check with `git config user.name` and
`git config user.email` before you commit.

## Routine core sync

The owner requires `update` to sync all nine core repositories before release
and application checks. It must save and restore unfinished local work and
the original branch. Routine sync does not commit or push that work. A failed
sync or restoration blocks updater replacement and application updates.
See `../000-0-workspace/docs/repository-protection.md` for this exception to
the delivery workflow. The implementation belongs to `000-0-ai`.

## Development tool ownership and startup

Use `../000-0-workspace/docs/update-and-development-tools.md` for the procedure.
`000-0-ai` owns `update`. `000-0-dotfiles` owns the non-AI doctor, installer and
catalog. This new system does not restore the retired dotfiles engine.

Run `update` as the owner. It syncs core repos, checks its published release,
then calls the doctor and repairs missing or broken required tools.
Do not repeat those calls manually during routine updates.
Do not reinstall healthy tools or reinstall for PATH or authentication problems.
Incomplete checks or repairs block app updates. The local quality checker never installs tools.
Only DNF repairs use `sudo -n`. Use `sudo -v` first when needed.
If authorization expires, report the failure. Never run `sudo update`.

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

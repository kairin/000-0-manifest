# Next steps

**Status:** to do.

This repository has follow-up work from the review of 2026-10-07 (task T25).
The owner keeps the full instructions in private notes, because they contain
local paths. Ask the owner for them before you start.

When the work is done, delete this file.

## Follow-ups from the inventory check of 2026-10-12

Each item needs an owner decision. Remove an item when it is resolved.

- [ ] Make `000-333-stay-up` private. Every Tier 333 repository must be
      private. Only the owner changes visibility, in the repository's GitHub
      settings. Its approved entry in `inventory-config.json` keeps it listed.
- [ ] Give every Tier 333 repository the same main-branch ruleset name. Ten
      repositories protect `main` with a ruleset named `Protect main` or
      `Minimal main protection` instead of `protect-main`; nine of those let a
      repository role bypass it. The `no-branch-deletion` and
      `no-branch-rewrite` rulesets already cover `main`, so protection is
      equivalent. Repositories: `000-333-BCM`, `000-333-cas-leave`,
      `000-333-eml-convert`, `000-333-kyo-m`, `000-333-OG-tools`,
      `000-333-screenforge-signage`, `000-333-vba-scripts`, `000-333-WOG-Ref`,
      `000-333-workday-procurement-forms`, `000-333-workday-supplier-kyocera`.
- [ ] Change `--publish` to deliver through a pull request. The
      `require-pull-request` ruleset rejects its direct push to `main`. See
      [docs/local-sync.md](docs/local-sync.md#publishing-rules-and-schedule).
- [ ] Archived repositories with open Dependabot pull requests. Archived
      repositories are read-only. To close a pull request, unarchive the
      repository, close it, and archive the repository again:
      `MetaSpec-Kyocera` #10, `win-qemu` #2, `google-gemini-codes` #6,
      `stable-diffusion-webui-forge` #1.
- [ ] Archived repositories whose default branch is not `main`: `master` in
      `comf-agx-orin`, `gitg`, `linformer`, `ubuntu-video-playback` and
      `Vizy-Unsupported-Remake`; `main-kairin` in `jetson-containers`. Decide
      whether to leave them as they are.

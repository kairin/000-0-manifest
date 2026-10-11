# Next steps

**Status:** to do.

This repository has follow-up work from the review of 2026-10-07 (task T25).
The owner keeps the full instructions in private notes, because they contain
local paths. Ask the owner for them before you start.

When the work is done, delete this file.

## Follow-ups from the inventory check of 2026-10-12

Each item needs an owner decision. Remove an item when it is resolved.

- [ ] Finish the `000-333-stay-up` privacy clean-up. The owner decided on
      2026-10-12 that it stays public as a tool for anyone, with no personal
      or work details. The repository files are clean; the remaining items
      are on GitHub and need the owner. Details are in the owner's notes.
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

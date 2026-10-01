# Local nightly inventory sync

The script copies GitHub About metadata into the four inventory pages. It reads every API page before writing. The account and approved repository IDs are in `inventory-config.json`; IDs keep category assignments stable when a repository is renamed. Existing personal and work categories are preserved.

Run a read-only preview from this repository:

```sh
python3 scripts/sync_manifest.py --dry-run
python3 scripts/sync_manifest.py --check
python3 -m unittest discover -s tests -v
```

`--dry-run` is the default. `--check` exits 2 when content would change. `--write` updates only the four local pages without committing. Descriptions come from GitHub About, with Markdown characters escaped for safe table display. Missing descriptions use `—`. A changed date alone never creates an update.

The classification order is archived, active fork, `000-111-` learning, other `000-` core/public, then configured personal/work. Unknown public archived/fork/core repositories can be included automatically. A new private or internal repository always needs an explicit config entry before publication. Every previously approved ID must be present; deletion, transfer, and lost access require review. To add an entry, use its numeric REST API `id`, name, and category (`personal`, `work`, or `auto` for core/fork/archive). Remove an entry only after confirming why it disappeared. An unarchived noncore original needs personal/work classification.

## Install after the changes are committed to GitHub

Requires Python 3.9 or later with timezone data, Git, GitHub CLI, and a systemd user session. The existing `gh` login must read every owned repository and push to this manifest repository. Configure Git commit identity and GitHub HTTPS authentication once if needed (`gh auth setup-git`).

Use a dedicated clean checkout so the scheduled job does not touch the development checkout:

```sh
mkdir -p ~/.local/share ~/.config/systemd/user
git clone https://github.com/kairin/000-0-manifest.git ~/.local/share/manifest-sync
cp ~/.local/share/manifest-sync/systemd/manifest-sync.service ~/.config/systemd/user/
cp ~/.local/share/manifest-sync/systemd/manifest-sync.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user start manifest-sync.service
journalctl --user -u manifest-sync.service -n 30 --no-pager
systemctl --user enable --now manifest-sync.timer
systemctl --user list-timers manifest-sync.timer
```

Review the first service run before enabling the timer. The service publishes directly to `main` using a normal push. It requires the dedicated path above, a clean checkout, branch `main`, and the expected GitHub origin. It fetches and fast-forwards before rendering, and commits only the four generated pages. If a push fails, the next run can retry commits with the sync commit message that touch only those pages. Diverged history, unexpected commits, or a dirty checkout stop the job for review. Fix a dirty checkout by inspecting its diff; do not discard it blindly. A remote branch protection rule may require a different publication workflow.

The timer runs at **02:00 Asia/Singapore** and catches up once after a missed night. Without lingering, the user manager normally starts at login; a keyring-backed `gh` login may also need the desktop unlocked. First-login catch-up is the default. If the timer fires before the desktop keyring unlocks, authentication can fail; unlock the keyring and start the service manually. Automatic completion at login is therefore not guaranteed. The timer does not wake a powered-off computer. Pre-login operation additionally needs lingering (`loginctl enable-linger kkk`), available home storage, and credentials that work without desktop unlock.

Temporary connection, rate-limit, and server failures exit 75 and retry every five minutes. Authentication, inventory validation, Git conflicts, and configuration failures exit 1 and stop retries. A successful check exits 0. The service timeout is five minutes; if killed by that timeout, inspect the journal and start it again. A persistent timer remembers a trigger, so temporary-failure retries come from the service. Run manual refreshes through `systemctl --user start manifest-sync.service` to avoid overlapping service runs. A checkout lock also prevents concurrent direct `--publish` runs.

To stop the schedule and any active retry:

```sh
systemctl --user disable --now manifest-sync.timer
systemctl --user stop manifest-sync.service
```

# Local nightly inventory sync

The script copies GitHub About metadata into the four inventory pages. It reads every API page before writing. The account and approved repository IDs are in `inventory-config.json`; IDs keep category assignments stable when a repository is renamed. Existing personal and work categories are preserved.

There is no GitHub Actions workflow. The sync runs only on a computer where the systemd timer below is installed.

## What runs, and where

| Part | Location | Role |
|---|---|---|
| Timer | `~/.config/systemd/user/manifest-sync.timer` (copied from `systemd/`) | Starts the service at 02:00 Asia/Singapore, after a missed night, and one minute after the user manager starts. |
| Service | `~/.config/systemd/user/manifest-sync.service` (copied from `systemd/`) | Runs `python3 ~/.local/share/manifest-sync/scripts/sync_manifest.py --publish` once, with a five-minute timeout. |
| Script | `scripts/sync_manifest.py` in the dedicated checkout `~/.local/share/manifest-sync` | Fetches, validates, renders, commits, and merges the change through a pull request. |
| Config | `inventory-config.json` | Account name and approved repository IDs with their categories. |
| Tests | `tests/test_sync_manifest.py` | Unit tests for classification, rendering, and publish safety checks. |

A `--publish` run does these steps in order:

1. Takes a lock in `.git/manifest-sync.lock`. If another run holds it, the run exits 0 without changes.
2. Checks that the checkout is at `~/.local/share/manifest-sync`, is clean, is on `main`, and has an accepted origin. Then it fetches and fast-forwards `main`.
3. Reads all owned repositories with `gh api --paginate user/repos?affiliation=owner&visibility=all`.
4. Validates the full snapshot against `inventory-config.json` and sorts each repository into a group. Any validation error stops the run before a page is written. When configured, it reports only a count of omitted unlisted private or internal repositories.
5. Renders the four pages. If a page changed, it commits only those pages with the message `docs: sync GitHub repository inventory`. It pushes the commit to a new branch named `YYYYMMDD-HHMMSS-inventory-sync`, opens a pull request into `main`, merges it with a merge commit, and fast-forwards the local `main`. It never pushes to `main` and never deletes the branch. If nothing changed, it makes no commit.

Run a read-only preview from this repository:

```sh
python3 scripts/sync_manifest.py --dry-run
python3 scripts/sync_manifest.py --check
python3 -m unittest discover -s tests -v
```

`--dry-run` is the default. `--check` exits 2 when content would change. `--write` updates only the four local pages without committing. Descriptions come from GitHub About, with Markdown characters escaped for safe table display. Missing descriptions use `—`. A changed date alone never creates an update.

## What the script overwrites

The script is not a general formatter. In `README.md`, `PERSONAL-PROJECTS.md`, `ARCHIVED.md`, and `FORKS.md` it replaces only these parts:

- Every table that starts with `| Repository |`. Rows, column order, sort order (case-insensitive by name), and cell escaping come from the script. The next run replaces any edit made by hand inside these tables, and publishes the replacement.
- The repository counts in the summary sentences of each page.
- The "Inventory retrieved" date in `README.md`. The date changes only when other content changes.

Other text on these pages, such as headings and prose, stays as written. The script finds its parts by pattern. If an edit adds or removes a `| Repository |` table, or changes the wording of a count or date sentence, the run stops with `Page layout changed` and writes nothing. To add a table, a section, or a category, change `render()` and the tests in the same commit.

The script does not change any other file. Change `inventory-config.json` and the documentation by hand. `unlisted_private` is an optional policy enum: leave it unset (or set it to `error`) to refuse unlisted private or internal repositories, or set it to `omit` to exclude only those unlisted non-public records. The omission diagnostic contains a count only; no repository name, ID, URL, or metadata is written to generated pages or logs.

## Classification and new repositories

The classification order is archived (tier 999), active fork (tier 444), then the name prefix of an active original: `000-111-` learning, `000-222-` personal, `000-333-workday-` work (Workday), other `000-333-` work (other projects), other `000-` core (private) or core (public). Remaining originals, including `000-444-` and `000-999-` names that are no longer forks or archived, use their configured personal/work category. Unknown public archived/fork/core repositories can be included automatically. By default, a new private or internal repository stops the sync until it has an explicit config entry. With `unlisted_private: "omit"`, only unlisted private or internal records are excluded; explicitly configured private records remain included, and public records follow normal classification. Omitted records do not contribute to generated tables or counts. Every previously approved ID must be present; deletion, transfer, and lost access require review. To add an entry, use its numeric REST API `id`, name, and category (`personal`, `work`, or `auto` for core/fork/archive). Remove an entry only after confirming why it disappeared. An unarchived noncore original needs personal/work classification.

To get the ID of a repository:

```sh
gh api repos/kairin/REPOSITORY-NAME --jq .id
```

Add the entry in a development checkout, then run `python3 scripts/sync_manifest.py --write` and the tests. Commit the config and the four pages together, and deliver them through a branch and pull request. Do not make this change in the dedicated checkout, because the scheduled job stops when that checkout is dirty or has unexpected commits.

## Fixed values

These values are in the code and the unit files, not in a settings file. To change one, edit the files listed and run the tests.

| Value | Where it is set |
|---|---|
| Account `kairin` | `inventory-config.json` (`account`), and the `--publish` origin check in `scripts/sync_manifest.py` |
| Dedicated checkout `~/.local/share/manifest-sync` | `scripts/sync_manifest.py` and `systemd/manifest-sync.service` |
| Time zone `Asia/Singapore` for the schedule and the page date | `systemd/manifest-sync.timer` and `scripts/sync_manifest.py` |
| Run time 02:00 | `systemd/manifest-sync.timer` |
| Commit message and pull request title `docs: sync GitHub repository inventory` | `scripts/sync_manifest.py` |
| Branch name `YYYYMMDD-HHMMSS-inventory-sync` (Asia/Singapore time) | `scripts/sync_manifest.py` |
| Accepted origins | `https://github.com/kairin/000-0-manifest(.git)` and `git@github.com:kairin/000-0-manifest.git` |

## Install after the changes are committed to GitHub

Install the timer on **one computer only**. Two computers with the timer make the same change in two pull requests. The second merge then fails or stops for review, which causes failed runs but no lost data. To move the sync to a different computer, see [Move the sync to a different computer](#move-the-sync-to-a-different-computer).

Requires Python 3.9 or later with timezone data, Git, GitHub CLI, and a systemd user session. The `gh` credentials must read every owned repository, including private repositories. Git must be able to push a branch to this manifest repository through the origin of the dedicated checkout, and `gh` must be able to open and merge pull requests in it. Configure a Git commit identity once (`git config --global user.name` and `user.email`). For an HTTPS origin, run `gh auth setup-git` once so Git uses the `gh` login. For a headless computer, use the credentials in [Headless computers](#headless-computers) instead.

Use a dedicated clean checkout so the scheduled job does not touch the development checkout:

```sh
mkdir -p ~/.local/share ~/.config/systemd/user
git clone https://github.com/kairin/000-0-manifest.git ~/.local/share/manifest-sync
cp ~/.local/share/manifest-sync/systemd/manifest-sync.service ~/.config/systemd/user/
cp ~/.local/share/manifest-sync/systemd/manifest-sync.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user start manifest-sync.service
systemctl --user status manifest-sync.service --no-pager
systemctl --user enable --now manifest-sync.timer
systemctl --user list-timers manifest-sync.timer
```

`systemctl --user status` shows the last log lines of the first run. A successful run ends with `Validated N repositories; N pages changed.` and `Finished manifest-sync.service`.

## Logs

Review recent runs, including entries retained from earlier boots, with:

```sh
journalctl --user -u manifest-sync.service --since '7 days ago' --no-pager
```

Some systems, for example some RHEL installations, do not keep a separate journal for each user. On these systems, the command above shows `No journal files were found`. Use this command instead:

```sh
journalctl --user-unit manifest-sync.service --since '7 days ago' --no-pager
```

Successful runs report how many repositories were checked and how many pages changed. Errors appear in the same journal. Journal retention follows this computer's systemd settings.

## Publishing rules and schedule

Review the first service run before enabling the timer. The service never pushes to `main`. The `require-pull-request` ruleset has no bypass, so every change goes through a pull request: the service pushes a new branch, opens a pull request, and merges it with a merge commit. The merge commit keeps the local commit in the history of `main`, so the local `main` fast-forwards afterwards. It requires the dedicated path above, a clean checkout, branch `main`, and an accepted origin (see [Fixed values](#fixed-values)). It fetches and fast-forwards before rendering, and commits only the four generated pages. If a push, pull request, or merge fails, the local commit stays on `main` and the next run retries it. Commits are accepted for retry only when they have the sync commit message and touch only those pages. When an open pull request from an earlier run already has the same commit, the next run merges that pull request instead of opening another one. If you merge a sync pull request by hand, use a merge commit; a squash or rebase merge makes the dedicated checkout diverge and stops the job for review. Diverged history, unexpected commits, or a dirty checkout stop the job for review. Fix a dirty checkout by inspecting its diff; do not discard it blindly.

The timer runs at **02:00 Asia/Singapore**, catches up once after a missed night, and also checks one minute after the user manager starts. With lingering enabled, the startup check follows boot; otherwise it follows login. This extra check is harmless when the pages have no changes, and restores retries after another reboot. Without lingering, the user manager normally starts at login; a keyring-backed `gh` login may also need the desktop unlocked. First-login catch-up is the default. If the timer fires before the desktop keyring unlocks, local GitHub CLI credential errors retry every five minutes. Unlock the desktop keyring to let a later attempt complete. The timer does not wake a powered-off computer. Pre-login operation additionally needs lingering (`loginctl enable-linger "$USER"`), available home storage, and credentials that work without desktop unlock.

Temporary connection, rate-limit, server, and recognized local GitHub CLI credential-unavailable errors exit 75 and retry every five minutes. The local credential cases include the `gh auth login` startup hint and a locked or unavailable keyring. If credentials were never configured, sign in with `gh auth login` to resolve these retries. Invalid remote credentials (HTTP 401), permission failures (HTTP 403, except rate limits), other authentication failures, inventory validation, Git conflicts, and configuration failures exit 1 and stop retries. A successful check exits 0. The service timeout is five minutes; if killed by that timeout, inspect the journal and start it again. A persistent timer remembers a trigger, so temporary-failure retries come from the service. Run manual refreshes through `systemctl --user start manifest-sync.service` to avoid overlapping service runs. A checkout lock also prevents concurrent direct `--publish` runs.

To stop the schedule and any active retry:

```sh
systemctl --user disable --now manifest-sync.timer
systemctl --user stop manifest-sync.service
```

## Headless computers

A computer without a desktop session, such as a small always-on ARM board running Armbian, can run the sync at 02:00 every night. Use two limited tokens instead of a full `gh auth login`. If the computer is lost, these tokens can only list repository metadata and change this one repository.

The tokens are secrets, so they live in the `pass` store and the service gets them only through `with-secret` (from the `000-0-password` repository). They are never in a file in plain text, in the service unit, or in shell history. The tracked file `.secrets.allow` in this repository lists the two entry names and their variables; it holds no values. The project name for `with-secret` is the name of the dedicated checkout folder, `manifest-sync`.

The `gh` packages for Debian and Ubuntu include ARM builds. Install `python3`, `tzdata`, `git`, `gh`, `pass`, and `gnupg` with the package manager. Set up the `pass` store and install `with-secret` in `~/.local/bin` as `SECRETS-GUIDE.md` in `000-0-password` describes.

### 1. Tokens in `pass`

On GitHub, create two fine-grained personal access tokens.

Read token, for the inventory:

- Resource owner: `kairin`
- Repository access: **All repositories**
- Repository permissions: **Metadata: Read-only** only

Pull request token, to open and merge the sync pull request (the read token cannot do this):

- Resource owner: `kairin`
- Repository access: **Only select repositories**, `kairin/000-0-manifest`
- Repository permissions: **Contents: Read and write** and **Pull requests: Read and write**

Write down both expiry dates. After a token expires, runs fail with exit 1 until you replace it. Store each token in `pass`. `pass insert` asks for the value without showing it, so the value does not go into shell history:

```sh
pass insert apps/manifest-sync/github/inventory-read
pass insert apps/manifest-sync/github/pull-request
```

The service gets `GH_TOKEN` and `MANIFEST_SYNC_PR_TOKEN` from these entries. You install the service drop-in in step 3, after the clone.

**Unlock limit:** `with-secret` reuses the gpg-agent unlock for up to 24 hours. A headless computer has no askpass dialog, so a run after the unlock expires, or after a reboot, stops with exit 3 and does not retry. To unlock, sign in over SSH and run `pass show apps/manifest-sync/github/inventory-read >/dev/null` and `pass show apps/manifest-sync/github/pull-request >/dev/null`, then start the service again. For unattended nightly runs, unlock at least once every 24 hours.

### 2. Write access: deploy key for Git

Create an SSH key without a passphrase on the headless computer:

```sh
ssh-keygen -t ed25519 -N '' -C manifest-sync -f ~/.ssh/manifest_deploy
```

Add the public key as a deploy key with write access. Run this command on a computer that has a full `gh` login, after you copy `manifest_deploy.pub` to it:

```sh
gh repo deploy-key add manifest_deploy.pub -R kairin/000-0-manifest --allow-write --title "manifest-sync on HOSTNAME"
```

Add the GitHub host key to `known_hosts` before the first run, because the service cannot answer a host key prompt. Compare the fingerprint that `ssh-keygen -l` shows with the SSH key fingerprints that GitHub publishes in its documentation:

```sh
ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts
ssh-keygen -l -F github.com -f ~/.ssh/known_hosts
```

### 3. Clone and install

Clone with the SSH origin, then tell this checkout to use the deploy key:

```sh
git clone git@github.com:kairin/000-0-manifest.git ~/.local/share/manifest-sync \
  --config core.sshCommand='ssh -i ~/.ssh/manifest_deploy -o IdentitiesOnly=yes'
git -C ~/.local/share/manifest-sync config user.name kairin
git -C ~/.local/share/manifest-sync config user.email 678459+kairin@users.noreply.github.com
```

Give the tokens to the service with a drop-in file. A drop-in keeps `systemd/manifest-sync.service` unchanged. It runs the script through `with-secret` once for each token:

```sh
mkdir -p ~/.config/systemd/user/manifest-sync.service.d
cat > ~/.config/systemd/user/manifest-sync.service.d/with-secret.conf <<'UNIT'
[Service]
ExecStart=
ExecStart=%h/.local/bin/with-secret github/inventory-read -- %h/.local/bin/with-secret github/pull-request -- /usr/bin/python3 %h/.local/share/manifest-sync/scripts/sync_manifest.py --publish
UNIT
```

Make sure that the read token can read the private repositories. The result must be the total number of repositories in the account:

```sh
cd ~/.local/share/manifest-sync
with-secret github/inventory-read -- gh api --paginate 'user/repos?affiliation=owner&visibility=all&per_page=100' --jq '.[].id' | wc -l
with-secret --check github/pull-request
```

Then do the steps in [Install after the changes are committed to GitHub](#install-after-the-changes-are-committed-to-github), but skip the `git clone` command. Enable lingering so the timer runs without a login:

```sh
loginctl enable-linger "$USER"
```

## Move the sync to a different computer

1. On the old computer, stop and remove the schedule:

   ```sh
   systemctl --user disable --now manifest-sync.timer
   systemctl --user stop manifest-sync.service
   rm ~/.config/systemd/user/manifest-sync.service ~/.config/systemd/user/manifest-sync.timer
   systemctl --user daemon-reload
   ```

2. On the old computer, make sure that the dedicated checkout has no unpublished commits. `git -C ~/.local/share/manifest-sync status -sb` must show `## main...origin/main` with no `ahead` count. Then you can delete `~/.local/share/manifest-sync`.
3. Install on the new computer. Use [Headless computers](#headless-computers) if it has no desktop session.
4. If the old computer used a deploy key, remove the key on GitHub (`gh repo deploy-key list -R kairin/000-0-manifest` and `gh repo deploy-key delete KEY-ID -R kairin/000-0-manifest`). If the new computer uses new tokens, revoke the old tokens in the GitHub token settings. The `pass` entries can stay; `pass insert` replaces their values.

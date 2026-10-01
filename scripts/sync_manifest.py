#!/usr/bin/env python3
"""Sync GitHub About metadata; exit 75 for temporary failures, 1 otherwise."""
import argparse
import datetime
import difflib
import html
import fcntl
import json
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FILES = ('README.md', 'PERSONAL-PROJECTS.md', 'ARCHIVED.md', 'FORKS.md')
MESSAGE = 'docs: sync GitHub repository inventory'


class SyncError(Exception):
    pass


class TemporaryError(SyncError):
    pass


def run(args, cwd=ROOT):
    try:
        result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired as exc:
        raise TemporaryError(f'{args[0]} timed out') from exc
    if result.returncode:
        error = result.stderr.strip()
        temporary = ('error connecting', 'could not resolve', 'connection timed out',
                     'connection reset', 'network is unreachable', 'http 502',
                     'http 503', 'http 504', 'rate limit', 'http 429')
        diagnostic = error.lower()
        retry = any(s in diagnostic for s in temporary)
        if Path(args[0]).name == 'gh':
            # A lingering user service can run before the desktop unlocks its keyring.
            local_credentials = (
                'to get started with github cli, please run: gh auth login',
                'not logged into any github hosts', 'not logged in to any github hosts',
                'keyring is locked', 'keyring is not available', 'keyring is unavailable',
                'locked keyring', 'cannot get secret of a locked object',
            )
            normalized = ' '.join(diagnostic.split())
            retry = retry or any(s in normalized for s in local_credentials)
            if re.search(r'http\s+(401|403)\b', diagnostic) and 'rate limit' not in diagnostic:
                retry = False
        cls = TemporaryError if retry else SyncError
        raise cls(f'{args[0]} failed: {error}')
    return result.stdout


def fetch():
    # gh follows every Link header; --slurp keeps page boundaries for validation.
    return json.loads(run(['gh', 'api', '--paginate', '--slurp',
                          'user/repos?affiliation=owner&visibility=all&per_page=100']))


def classify(pages, config):
    if not isinstance(pages, list) or not pages or any(not isinstance(p, list) for p in pages):
        raise SyncError('Invalid API page list')
    approved = config['repositories']
    account = config['account'].lower()
    groups = {k: [] for k in ('core', 'public', 'learning', 'personal', 'work', 'archived', 'forks')}
    seen = set()
    for page in pages:
        for repo in page:
            try:
                rid = str(repo['id'])
                name = repo['name']
                owner = repo['owner']['login']
                if not isinstance(repo['id'], int) or not isinstance(name, str) or not name:
                    raise ValueError('invalid identity')
                if not isinstance(owner, str):
                    raise ValueError('invalid owner')
                for key in ('archived', 'fork', 'private'):
                    if not isinstance(repo[key], bool):
                        raise ValueError('invalid boolean')
                for key in ('description', 'default_branch'):
                    if repo[key] is not None and not isinstance(repo[key], str):
                        raise ValueError('invalid text')
                if repo['visibility'] not in ('public', 'private', 'internal'):
                    raise ValueError('invalid visibility')
            except (KeyError, TypeError, ValueError) as exc:
                raise SyncError('Incomplete or invalid repository metadata') from exc
            if owner.lower() != account:
                continue
            if rid in seen:
                raise SyncError(f'Duplicate repository ID: {rid}')
            seen.add(rid)
            if repo['visibility'] != 'public' and rid not in approved:
                raise SyncError(f'New private repository needs an explicit publish entry: {name} ({rid})')
            if repo['archived']:
                group = 'archived'
            elif repo['fork']:
                group = 'forks'
            elif name.startswith('000-111-'):
                group = 'learning'
            elif name.startswith('000-'):
                group = 'public' if repo['visibility'] == 'public' else 'core'
            else:
                group = approved.get(rid, {}).get('category')
                if group not in ('personal', 'work'):
                    raise SyncError(f'Repository needs personal/work classification: {name} ({rid})')
            groups[group].append(repo)
    missing = set(approved) - seen
    if missing:
        names = ', '.join(approved[r]['name'] for r in sorted(missing))
        raise SyncError(f'Expected repositories missing; check access/deletion before changing config: {names}')
    for rows in groups.values():
        rows.sort(key=lambda r: (r['name'].casefold(), r['name']))
    return groups


def escape(value):
    if not value:
        return '—'
    value = ' '.join(value.splitlines())
    value = html.escape(value, quote=False)
    for char in ('\\', '|', '`', '*', '_', '[', ']'):
        value = value.replace(char, '\\' + char)
    return value


def table(rows, account, description=True, kind=True):
    columns = ['Repository', 'Visibility'] + (['Type'] if kind else [])
    columns += ['State', 'Default branch'] + (['Description'] if description else [])
    lines = ['| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
    for r in rows:
        # GitHub repository names cannot contain URL control characters.
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', r['name']):
            raise SyncError('Invalid repository name')
        cells = [f"[{r['name']}](https://github.com/{account}/{r['name']})",
                 r['visibility'].title()]
        if kind:
            cells.append('Fork' if r['fork'] else 'Original')
        branch = r['default_branch']
        # HTML code safely handles branch names containing Markdown punctuation.
        branch_cell = f'`{branch}`' if branch and re.fullmatch(r'[\w./-]+', branch) else (
            '<code>' + html.escape(branch).replace('|', '&#124;').replace('`', '&#96;') + '</code>' if branch else '—')
        cells += ['Archived' if r['archived'] else 'Active', branch_cell]
        if description:
            cells.append(escape(r['description']))
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def replace_tables(text, tables):
    matches = list(re.finditer(r'^\| Repository \|[^\n]*\n(?:\|[^\n]*\n?)+', text, re.M))
    if len(matches) != len(tables):
        raise SyncError('Page layout changed: unexpected number of tables')
    for match, replacement in reversed(list(zip(matches, tables))):
        text = text[:match.start()] + replacement + '\n' + text[match.end():]
    return text


def replace_once(pattern, replacement, text):
    result, count = re.subn(pattern, replacement, text)
    if count != 1:
        raise SyncError("Page layout changed: expected one count/date field")
    return result


def render(original, groups, account, today=None):
    total = sum(map(len, groups.values()))
    active = sum(len(groups[k]) for k in ('core', 'public', 'learning', 'personal', 'work'))
    personal = len(groups['personal'])
    result = dict(original)
    result['README.md'] = replace_tables(original['README.md'], [
        table(groups[k], account, description=k not in ('personal', 'work'))
        for k in ('core', 'public', 'learning', 'personal', 'work')])
    text = result['README.md']
    text = replace_once(r'\*\*Total: \d+ repositories', f'**Total: {total} repositories', text)
    text = replace_once(r'lists \d+ repositories across its tables \(\d+ of \d+\)',
                  f'lists {active} repositories across its tables ({active} of {total})', text)
    text = replace_once(r'descriptions for the \d+ personal-project entries',
                  f'descriptions for the {personal} personal-project entries', text)
    result['README.md'] = text
    for filename, group in (('PERSONAL-PROJECTS.md', 'personal'), ('ARCHIVED.md', 'archived'), ('FORKS.md', 'forks')):
        text = replace_tables(original[filename], [table(groups[group], account, kind=group != 'forks')])
        text = replace_once(r'This table lists \d+ (projects|archived repositories|active forks) out of \d+',
                      lambda m: f'This table lists {len(groups[group])} {m[1]} out of {total}', text)
        result[filename] = text
    if result != original:
        date = today or datetime.datetime.now(ZoneInfo('Asia/Singapore')).date().isoformat()
        result['README.md'] = replace_once(r'Inventory retrieved with GitHub CLI .*? on \d{4}-\d{2}-\d{2}',
                                     f'Inventory retrieved with GitHub CLI (`gh api`) on {date}', result['README.md'])
    return result


def prepare_publish(root, account):
    expected = Path.home() / '.local/share/manifest-sync'
    if root.resolve() != expected.resolve():
        raise SyncError(f'Publish requires the dedicated checkout at {expected}')
    git = lambda *args: run(['git', *args], root).strip()
    if git('status', '--porcelain'):
        raise SyncError('Dedicated checkout must be clean')
    if git('branch', '--show-current') != 'main':
        raise SyncError('Dedicated checkout must be on main')
    origins = (f'https://github.com/{account}/000-0-manifest.git',
               f'git@github.com:{account}/000-0-manifest.git',
               f'https://github.com/{account}/000-0-manifest')
    if git('remote', 'get-url', 'origin') not in origins or git('remote', 'get-url', '--push', 'origin') not in origins:
        raise SyncError('Unexpected origin URL')
    git('fetch', 'origin', 'main')
    ahead, behind = map(int, git('rev-list', '--left-right', '--count', 'HEAD...origin/main').split())
    if ahead:
        # Recover only our own unpublished commits. Divergence needs human review.
        if behind:
            raise SyncError('Local sync commit and remote main diverged; review the dedicated checkout')
        for commit in git('rev-list', 'origin/main..HEAD').splitlines():
            if len(git('show', '-s', '--format=%P', commit).split()) != 1:
                raise SyncError('Unpublished merge or root commit needs review')
            if git('show', '-s', '--format=%s', commit) != MESSAGE:
                raise SyncError('Unexpected unpublished commit')
            paths = set(git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).splitlines())
            if not paths or not paths <= set(FILES):
                raise SyncError('Unpublished commit changes files outside the four pages')
    else:
        git('merge', '--ff-only', 'origin/main')
    return bool(ahead)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='show diff; write nothing (default)')
    mode.add_argument('--check', action='store_true', help='exit 2 when pages would change')
    mode.add_argument('--write', action='store_true', help='update only the four local pages')
    mode.add_argument('--publish', action='store_true', help='update and push from dedicated checkout')
    args = parser.parse_args()
    lock = None
    try:
        ahead = False
        if args.publish:
            expected = Path.home() / '.local/share/manifest-sync'
            if ROOT.resolve() != expected.resolve():
                raise SyncError(f'Publish requires the dedicated checkout at {expected}')
            lock = (ROOT / '.git/manifest-sync.lock').open('a')
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print('Manifest sync is already running.')
                return 0
            ahead = prepare_publish(ROOT, 'kairin')
        config = json.loads((ROOT / 'inventory-config.json').read_text())
        if config['account'] != 'kairin':
            raise SyncError('Unexpected account in config')
        pages = fetch()
        groups = classify(pages, config)  # Validate entire snapshot before page writes.
        original = {name: (ROOT / name).read_text() for name in FILES}
        rendered = render(original, groups, config['account'])
        changed = [name for name in FILES if original[name] != rendered[name]]
        if not args.write and not args.publish:
            for name in changed:
                print(''.join(difflib.unified_diff(original[name].splitlines(True), rendered[name].splitlines(True),
                                                  fromfile=name, tofile=name)), end='')
        else:
            for name in changed:
                (ROOT / name).write_text(rendered[name])
            if args.publish and changed:
                run(['git', 'add', '--', *FILES])
                run(['git', 'commit', '-m', MESSAGE, '--', *FILES])
            if args.publish and (changed or ahead):
                run(['git', 'push', 'origin', 'HEAD:refs/heads/main'])
        print(f'Validated {sum(map(len, groups.values()))} repositories; {len(changed)} pages changed.')
        return 2 if args.check and changed else 0
    except TemporaryError as exc:
        print(f'Temporary failure: {exc}', file=sys.stderr)
        return 75
    except (SyncError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Sync stopped: {exc}', file=sys.stderr)
        return 1
    finally:
        if lock is not None:
            lock.close()


if __name__ == '__main__':
    sys.exit(main())

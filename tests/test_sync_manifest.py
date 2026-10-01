import importlib.util
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_manifest', ROOT / 'scripts/sync_manifest.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def repo(rid=1, name='project', **changes):
    value = dict(id=rid, name=name, owner={'login': 'kairin'}, archived=False,
                 fork=False, private=False, visibility='public', description=None, default_branch='main')
    value.update(changes)
    return value


def config(*rows):
    return {'account': 'kairin', 'repositories': {str(r['id']): {'name': r['name'], 'category': 'personal'} for r in rows}}


class InventoryTests(unittest.TestCase):
    def test_multiple_pages_rename_and_archived_fork_precedence(self):
        rows = [repo(i, f'project-{i}') for i in range(1, 103)]
        cfg = config(*rows)
        rows[0].update(name='renamed', archived=True, fork=True)
        groups = sync.classify([rows[:100], rows[100:]], cfg)
        self.assertEqual(len(groups['personal']), 101)
        self.assertEqual(groups['archived'][0]['name'], 'renamed')
        self.assertEqual(groups['forks'], [])

    def test_private_requires_approval_even_if_archived(self):
        r = repo(private=True, visibility='private', archived=True)
        with self.assertRaisesRegex(sync.SyncError, 'explicit publish'):
            sync.classify([[r]], config())
        self.assertEqual(len(sync.classify([[r]], config(r))['archived']), 1)

    def test_missing_duplicate_and_incomplete_fail(self):
        r = repo()
        for pages in ([[]], [[r, r]], [[{'id': 1}]], [], {}):
            with self.subTest(pages=pages), self.assertRaises(sync.SyncError):
                sync.classify(pages, config(r))

    def test_unclassified_public_and_core_routing(self):
        with self.assertRaisesRegex(sync.SyncError, 'classification'):
            sync.classify([[repo()]], config())
        rows = [repo(1, '000-111-learn'), repo(2, '000-0-public'),
                repo(3, '000-0-secret', private=True, visibility='private'),
                repo(4, 'fork', fork=True)]
        groups = sync.classify([rows], config(*rows))
        for key in ('learning', 'public', 'core', 'forks'):
            self.assertEqual(len(groups[key]), 1)

    def test_order_and_missing_text_and_injection(self):
        rows = [repo(1, 'z'), repo(2, 'Alpha', description='<script>x</script> | [bad](url)\nnext')]
        groups = sync.classify([rows], config(*rows))
        self.assertEqual([r['name'] for r in groups['personal']], ['Alpha', 'z'])
        text = sync.table(groups['personal'], 'kairin')
        self.assertIn('&lt;script&gt;', text)
        self.assertIn(r'\| \[bad\](url) next', text)
        self.assertIn('| — |', text)
        self.assertEqual(len(text.splitlines()), 4)

    def test_render_idempotent_and_counts(self):
        originals = {name: (ROOT / name).read_text() for name in sync.FILES}
        rows = [repo(1, 'sample'), repo(2, '000-0-core'), repo(3, 'fork', fork=True), repo(4, 'old', archived=True)]
        groups = sync.classify([rows], config(*rows))
        first = sync.render(originals, groups, 'kairin', '2026-10-01')
        self.assertIn('Total: 4 repositories', first['README.md'])
        self.assertIn('lists 2 repositories across its tables (2 of 4)', first['README.md'])
        self.assertIn('lists 1 projects out of 4', first['PERSONAL-PROJECTS.md'])
        self.assertEqual(first, sync.render(first, groups, 'kairin', '2026-10-02'))

    def test_changed_count_prose_refuses_output(self):
        originals = {name: (ROOT / name).read_text() for name in sync.FILES}
        originals['README.md'] = originals['README.md'].replace('**Total:', '**Inventory:')
        r = repo()
        with self.assertRaisesRegex(sync.SyncError, 'count/date'):
            sync.render(originals, sync.classify([[r]], config(r)), 'kairin')

    def test_publish_loads_remote_config_after_fast_forward(self):
        r = repo(private=True, visibility='private')
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            root = home / '.local/share/manifest-sync'
            (root / '.git').mkdir(parents=True)
            (root / 'inventory-config.json').write_text(json.dumps(config()))
            for name in sync.FILES:
                (root / name).write_text((ROOT / name).read_text())
            def prepare(path, account):
                (path / 'inventory-config.json').write_text(json.dumps(config(r)))
                return True  # Recover a previous failed push even without new edits.
            with patch.object(sync, 'ROOT', root), patch.object(Path, 'home', return_value=home), \
                 patch.object(sync, 'prepare_publish', side_effect=prepare), \
                 patch.object(sync, 'fetch', return_value=[[r]]), \
                 patch.object(sync, 'render', side_effect=lambda original, *args: original), \
                 patch.object(sync, 'run', return_value='') as run, \
                 patch.object(sync.sys, 'argv', ['sync_manifest.py', '--publish']):
                self.assertEqual(sync.main(), 0)
                run.assert_called_once_with(['git', 'push', 'origin', 'HEAD:refs/heads/main'])

    def test_fetch_pagination_arguments(self):
        with patch.object(sync, 'run', return_value='[[{"id":1}],[]]') as run:
            self.assertEqual(sync.fetch(), [[{'id': 1}], []])
            args = run.call_args.args[0]
            self.assertIn('--paginate', args)
            self.assertIn('--slurp', args)

    def test_retry_classification(self):
        from subprocess import CompletedProcess
        for message, cls in [('error connecting to api.github.com', sync.TemporaryError),
                             ('HTTP 401: Bad credentials', sync.SyncError)]:
            with patch.object(sync.subprocess, 'run', return_value=CompletedProcess([], 1, '', message)):
                with self.assertRaises(cls) as caught:
                    sync.run(['gh', 'api', 'user'])
                self.assertIs(type(caught.exception), cls)

    def test_only_local_gh_credentials_retry(self):
        from subprocess import CompletedProcess
        cases = [
            ('gh', 'To get started with GitHub CLI, please run:  gh auth login', sync.TemporaryError),
            ('gh', 'You are not logged into any GitHub hosts. Run gh auth login.', sync.TemporaryError),
            ('gh', 'failed to get token: keyring is locked', sync.TemporaryError),
            ('gh', 'failed to get token: keyring is not available', sync.TemporaryError),
            ('gh', 'Cannot get secret of a locked object', sync.TemporaryError),
            ('gh', 'HTTP 401: Bad credentials. To get started with GitHub CLI, please run: gh auth login', sync.SyncError),
            ('gh', 'HTTP 403: Resource not accessible by personal access token', sync.SyncError),
            ('gh', 'HTTP 403: API rate limit exceeded', sync.TemporaryError),
            ('gh', 'Authentication failed: token invalid', sync.SyncError),
            ('git', 'keyring is locked', sync.SyncError),
            ('git', 'To get started with GitHub CLI, please run: gh auth login', sync.SyncError),
        ]
        for executable, message, expected in cases:
            with self.subTest(message=message, executable=executable), \
                 patch.object(sync.subprocess, 'run', return_value=CompletedProcess([], 1, '', message)):
                with self.assertRaises(sync.SyncError) as caught:
                    sync.run([executable, 'test'])
                self.assertIs(type(caught.exception), expected)

    def test_pending_push_recovery_and_unrelated_commit_refusal(self):
        root = Path.home() / '.local/share/manifest-sync'
        def output(args, cwd):
            command = tuple(args[1:])
            values = {
                ('status', '--porcelain'): '', ('branch', '--show-current'): 'main',
                ('remote', 'get-url', 'origin'): 'https://github.com/kairin/000-0-manifest.git',
                ('remote', 'get-url', '--push', 'origin'): 'https://github.com/kairin/000-0-manifest.git',
                ('fetch', 'origin', 'main'): '',
                ('rev-list', '--left-right', '--count', 'HEAD...origin/main'): '1 0',
                ('rev-list', 'origin/main..HEAD'): 'abc',
                ('show', '-s', '--format=%s', 'abc'): sync.MESSAGE,
                ('show', '-s', '--format=%P', 'abc'): 'parent',
                ('diff-tree', '--no-commit-id', '--name-only', '-r', 'abc'): 'README.md',
            }
            return values[command]
        with patch.object(sync, 'run', side_effect=output):
            self.assertTrue(sync.prepare_publish(root, 'kairin'))
        def unrelated(args, cwd):
            return 'other.txt' if 'diff-tree' in args else output(args, cwd)
        with patch.object(sync, 'run', side_effect=unrelated), self.assertRaisesRegex(sync.SyncError, 'outside'):
            sync.prepare_publish(root, 'kairin')


if __name__ == '__main__':
    unittest.main()

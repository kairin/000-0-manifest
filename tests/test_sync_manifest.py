import importlib.util
import io
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_manifest', ROOT / 'scripts/sync_manifest.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def repo(rid=1, name='project', **changes):
    value = dict(id=rid, name=name, owner={'login': 'kairin'}, archived=False,
                 fork=False, private=False, visibility='public', description=None, default_branch='main')
    value.update(changes)
    return value


def config(*rows, unlisted_private=None):
    value = {'account': 'kairin',
             'repositories': {str(r['id']): {'name': r['name'], 'category': 'personal'} for r in rows}}
    if unlisted_private is not None:
        value['unlisted_private'] = unlisted_private
    return value


class InventoryTests(unittest.TestCase):
    def test_multiple_pages_rename_and_archived_fork_precedence(self):
        rows = [repo(i, f'project-{i}') for i in range(1, 103)]
        cfg = config(*rows)
        rows[0].update(name='renamed', archived=True, fork=True)
        groups, omitted = sync.classify([rows[:100], rows[100:]], cfg)
        self.assertEqual(len(groups['personal']), 101)
        self.assertEqual(groups['archived'][0]['name'], 'renamed')
        self.assertEqual(groups['forks'], [])
        self.assertEqual(omitted, 0)

    def test_private_requires_approval_even_if_archived(self):
        r = repo(private=True, visibility='private', archived=True)
        with self.assertRaisesRegex(sync.SyncError, 'requires approval') as caught:
            sync.classify([[r]], config())
        self.assertNotIn(r['name'], str(caught.exception))
        self.assertNotIn(str(r['id']), str(caught.exception))
        groups, omitted = sync.classify([[r]], config(r))
        self.assertEqual(len(groups['archived']), 1)
        self.assertEqual(omitted, 0)

    def test_unlisted_private_omit_is_counted_without_rendering(self):
        private = repo(11, 'private-fixture', private=True, visibility='private')
        internal = repo(12, 'internal-fixture', private=True, visibility='internal')
        approved = repo(13, 'approved-private', private=True, visibility='private')
        public = repo(14, '000-111-public-fixture')
        groups, omitted = sync.classify([[private, internal, approved, public]],
                                         config(approved, public, unlisted_private='omit'))
        self.assertEqual(omitted, 2)
        self.assertEqual([r['id'] for r in groups['personal']], [approved['id']])
        self.assertEqual([r['id'] for r in groups['learning']], [public['id']])
        rendered = sync.render({name: (ROOT / name).read_text() for name in sync.FILES}, groups,
                               'kairin', '2026-10-11')
        text = '\n'.join(rendered.values())
        self.assertNotIn(private['name'], text)
        self.assertNotIn(internal['name'], text)

    def test_main_reports_a_count_only_omission_diagnostic(self):
        private = repo(11, 'private-fixture', private=True, visibility='private')
        output = io.StringIO()
        with patch.object(sync.json, 'loads', return_value=config(unlisted_private='omit')), \
             patch.object(sync, 'fetch', return_value=[[private]]), \
             patch.object(sync, 'render', side_effect=lambda original, *args: original), \
             patch.object(sync.sys, 'argv', ['sync_manifest.py', '--check']), \
             redirect_stdout(output):
            self.assertEqual(sync.main(), 0)
        self.assertIn('Omitted 1 unlisted private/internal repositories.', output.getvalue())
        self.assertNotIn(private['name'], output.getvalue())
        self.assertNotIn(str(private['id']), output.getvalue())

    def test_unlisted_private_policy_and_config_entries_are_strict(self):
        private = repo(11, 'private-fixture', private=True, visibility='private')
        public = repo(12, 'public-fixture')
        invalid_configs = [
            {'account': 'kairin', 'repositories': {}, 'unlisted_private': 'skip'},
            {'account': 'kairin', 'repositories': {'11': {'name': '', 'category': 'personal'}}},
            {'account': 'kairin', 'repositories': {'11': {'name': 'x', 'category': 'omit'}}},
            {'account': 'kairin', 'repositories': {'not-an-id': {'name': 'x', 'category': 'personal'}}},
            {'account': 'kairin', 'repositories': {'11': {'name': 'x', 'category': 'personal', 'extra': True}}},
        ]
        for cfg in invalid_configs:
            with self.subTest(cfg=cfg), self.assertRaisesRegex(sync.SyncError, 'Invalid inventory configuration'):
                sync.classify([[private]], cfg)
        groups, omitted = sync.classify([[public]], config(public, unlisted_private='omit'))
        self.assertEqual(groups['personal'][0]['id'], public['id'])
        self.assertEqual(omitted, 0)
        with self.assertRaisesRegex(sync.SyncError, 'classification'):
            sync.classify([[repo(13, 'unclassified-public')]], config(unlisted_private='omit'))

    def test_missing_approved_entry_has_count_only_diagnostic(self):
        missing = repo(11, 'missing-fixture')
        with self.assertRaisesRegex(sync.SyncError, '1 approved repositories missing') as caught:
            sync.classify([[]], config(missing))
        self.assertNotIn(missing['name'], str(caught.exception))
        self.assertNotIn(str(missing['id']), str(caught.exception))

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
        groups, omitted = sync.classify([rows], config(*rows))
        for key in ('learning', 'public', 'core', 'forks'):
            self.assertEqual(len(groups[key]), 1)
        self.assertEqual(omitted, 0)

    def test_tier_prefix_routing(self):
        rows = [repo(1, '000-222-fun', private=True, visibility='private'),
                repo(2, '000-333-job', private=True, visibility='private'),
                repo(3, '000-444-copy', fork=True), repo(4, '000-999-old', archived=True),
                repo(6, '000-333-workday-suppliers', private=True, visibility='private')]
        cfg = config(*rows)
        for rid in ('1', '2', '6'):
            cfg['repositories'][rid]['category'] = 'auto'
        groups, omitted = sync.classify([rows], cfg)
        for key, name in (('personal', '000-222-fun'), ('work', '000-333-job'),
                          ('workday', '000-333-workday-suppliers'),
                          ('forks', '000-444-copy'), ('archived', '000-999-old')):
            self.assertEqual([r['name'] for r in groups[key]], [name])
        self.assertEqual(groups['core'], [])
        self.assertEqual(omitted, 0)
        # An unarchived 000-999- original is not core; it needs personal/work classification.
        with self.assertRaisesRegex(sync.SyncError, 'classification'):
            sync.classify([[repo(5, '000-999-back')]], config())

    def test_game_family_routing(self):
        rows = [repo(1, 'ABN-124-shooter', private=True, visibility='private'),
                repo(2, 'ABN-685-wheel', private=True, visibility='private'),
                repo(3, 'ABN-000-index'),
                repo(4, 'ZQX-210-old', archived=True),
                repo(5, 'ABN-999-copy', fork=True)]
        cfg = config(*rows)
        for rid in ('1', '2'):
            cfg['repositories'][rid]['category'] = 'auto'
        groups, omitted = sync.classify([rows], cfg)
        self.assertEqual([r['name'] for r in groups['games']],
                         ['ABN-000-index', 'ABN-124-shooter', 'ABN-685-wheel'])
        self.assertEqual([r['name'] for r in groups['archived']], ['ZQX-210-old'])
        self.assertEqual([r['name'] for r in groups['forks']], ['ABN-999-copy'])
        self.assertEqual(omitted, 0)
        # Names that break the game family rule are not games.
        for name in ('abn-124-shooter', 'BON-124-x', '1BN-124-x', 'ABN-050-x',
                     'ABN-124-Shooter', 'ABN-124--x', 'ABN-124-x-', 'ABN-12-x'):
            with self.subTest(name=name), self.assertRaisesRegex(sync.SyncError, 'classification'):
                sync.classify([[repo(9, name)]], config())
        # An unlisted private game repository is omitted, as other private repositories.
        hidden = repo(10, 'ABN-777-secret', private=True, visibility='private')
        groups, omitted = sync.classify([[hidden]], config(unlisted_private='omit'))
        self.assertEqual(groups['games'], [])
        self.assertEqual(omitted, 1)

    def test_game_family_table_renders_with_description(self):
        originals = {name: (ROOT / name).read_text() for name in sync.FILES}
        rows = [repo(1, 'ABN-124-shooter', description='ABN family. Base game.')]
        groups, _ = sync.classify([rows], config(*rows))
        text = sync.render(originals, groups, 'kairin', '2026-10-15')['README.md']
        self.assertIn('| [ABN-124-shooter](https://github.com/kairin/ABN-124-shooter) | Public | Original | Active | `main` | ABN family. Base game. |', text)
        self.assertIn('lists 1 repositories across its tables (1 of 1)', text)

    def test_order_and_missing_text_and_injection(self):
        rows = [repo(1, 'z'), repo(2, 'Alpha', description='<script>x</script> | [bad](url)\nnext')]
        groups, _ = sync.classify([rows], config(*rows))
        self.assertEqual([r['name'] for r in groups['personal']], ['Alpha', 'z'])
        text = sync.table(groups['personal'], 'kairin')
        self.assertIn('&lt;script&gt;', text)
        self.assertIn(r'\| \[bad\](url) next', text)
        self.assertIn('| — |', text)
        self.assertEqual(len(text.splitlines()), 4)

    def test_render_idempotent_and_counts(self):
        originals = {name: (ROOT / name).read_text() for name in sync.FILES}
        rows = [repo(1, 'sample'), repo(2, '000-0-core'), repo(3, 'fork', fork=True), repo(4, 'old', archived=True)]
        groups, _ = sync.classify([rows], config(*rows))
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
            groups, _ = sync.classify([[r]], config(r))
            sync.render(originals, groups, 'kairin')

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
                 patch.object(sync, 'publish') as publish, \
                 patch.object(sync.sys, 'argv', ['sync_manifest.py', '--publish']):
                self.assertEqual(sync.main(), 0)
                run.assert_not_called()
                publish.assert_called_once_with(root, 'kairin')

    def test_publish_opens_and_merges_pull_request_without_pushing_main(self):
        import datetime
        calls = []
        def output(args, cwd, env=None):
            calls.append(args)
            if args[:2] == ['git', 'rev-parse']:
                return 'abc\n'
            if args[:3] == ['gh', 'pr', 'list']:
                return json.dumps([{'number': 7, 'headRefName': 'feature', 'headRefOid': 'abc'}])
            return ''
        now = datetime.datetime(2026, 10, 12, 2, 0, 5)
        with patch.object(sync, 'run', side_effect=output), patch.dict(sync.os.environ, clear=True):
            sync.publish(ROOT, 'kairin', now)
        branch = '20261012-020005-inventory-sync'
        self.assertIn(['git', 'push', 'origin', f'HEAD:refs/heads/{branch}'], calls)
        self.assertIn(['gh', 'pr', 'merge', branch, '--merge', '--match-head-commit', 'abc',
                       '--repo', 'kairin/000-0-manifest'], calls)
        self.assertEqual(calls[-1], ['git', 'merge', '--ff-only', 'origin/main'])
        self.assertFalse(any('HEAD:refs/heads/main' in a for a in calls))
        self.assertFalse(any('--delete-branch' in a or '-d' in a for a in calls))

    def test_publish_reuses_pending_pull_request_and_pr_token(self):
        calls = []
        def output(args, cwd, env=None):
            calls.append((args, env and env.get('GH_TOKEN')))
            if args[:2] == ['git', 'rev-parse']:
                return 'abc'
            if args[:3] == ['gh', 'pr', 'list']:
                return json.dumps([{'number': 9, 'headRefName': '20261011-020000-inventory-sync',
                                    'headRefOid': 'abc'}])
            return ''
        with patch.object(sync, 'run', side_effect=output), \
             patch.dict(sync.os.environ, {sync.PR_TOKEN: 'pr-token'}, clear=True):
            sync.publish(ROOT, 'kairin')
        commands = [args for args, _ in calls]
        self.assertFalse(any(a[:2] == ['git', 'push'] for a in commands))
        self.assertFalse(any(a[:3] == ['gh', 'pr', 'create'] for a in commands))
        self.assertIn(['gh', 'pr', 'merge', '9', '--merge', '--match-head-commit', 'abc',
                       '--repo', 'kairin/000-0-manifest'], commands)
        self.assertTrue(all(token == 'pr-token' for args, token in calls if args[0] == 'gh'))

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

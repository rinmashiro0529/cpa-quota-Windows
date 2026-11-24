"""Offline negative controls for the planning gate; only mutate a temporary copy."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PlanningGate(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for directory in ('docs', 'planning'):
            shutil.copytree(ROOT / directory, self.root / directory)
        # Link checks need the real top-level entry points and planning tools, not .git.
        for directory in ('.github', 'tools'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for filename in ('AGENTS.md', 'README.md'):
            shutil.copyfile(ROOT / filename, self.root / filename)
        self.registry = self.root / 'planning/tasks.json'
        self.data = json.loads(self.registry.read_text(encoding='utf-8'))
        self.tasks = {t['id']: t for t in self.data['tasks']}

    def gate(self, error=None):
        self.registry.write_text(json.dumps(self.data), encoding='utf-8')
        p = subprocess.run([sys.executable, '-I', str(ROOT / 'tools/planning/validate_plan.py'),
                            '--root', str(self.root)], capture_output=True, encoding='utf-8', errors='replace')
        if error is None:
            self.assertEqual(p.returncode, 0, p.stderr)
        else:
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertIn(error, p.stderr)

    def test_unmodified(self):
        self.gate()

    def test_wrong_valid_acceptance(self):
        self.tasks['WP-007']['acceptance_ids'][0] = 'AT-PLAT-010'
        self.gate('acceptance mapping')

    def test_missing_cross(self):
        self.tasks['WP-031']['acceptance_ids'].pop()
        self.gate('acceptance mapping')

    def test_unknown_invariant(self):
        self.tasks['WP-007']['invariant_ids'].append('INV-999')
        self.gate('invariant mapping')

    def test_release_cannot_orphan_required_package(self):
        self.tasks['WP-031']['depends_on'].remove('WP-030')
        self.gate('release dependency closure')

    def test_done_cannot_omit_locked_source(self):
        task = self.tasks['WP-000']
        task.update(status='done', evidence=[dict(schema_version=1, kind='source_audit', status='passed',
                    task_id=task['id'], target_sha='1'*40, feature_ids=[], acceptance_ids=[],
                    checks=[dict(id='baseline', status='passed', expected='locked', actual='locked')],
                    raw_artifacts=['planning/source-lock.json'])])
        self.gate('source_sha')

    def test_cannot_substitute_feature_list_for_acceptance_evidence(self):
        task = self.tasks['WP-007']
        task.update(status='done', depends_on=[], evidence=[dict(schema_version=1, kind='contract', status='passed',
                    task_id=task['id'], source_sha=self.data['source_baseline_sha'], target_sha='1'*40,
                    feature_ids=task['feature_ids'], acceptance_ids=[],
                    checks=[dict(id='fixture', status='passed', expected='ok', actual='ok')],
                    raw_artifacts=['planning/source-lock.json'])])
        self.gate('missing task acceptance evidence')

    def test_cannot_pool_candidate_versions(self):
        task = self.tasks['WP-000']
        task.update(status='done', evidence=[dict(schema_version=1, kind='review', status='passed',
                    task_id=task['id'], source_sha=self.data['source_baseline_sha'], target_sha=c*40,
                    feature_ids=[], acceptance_ids=[], checks=[dict(id='review', status='passed', expected='ok', actual='ok')],
                    raw_artifacts=['planning/source-lock.json']) for c in '12'])
        self.gate('cannot combine different target_sha')

    def test_missing_local_heading(self):
        with (self.root / 'README.md').open('a', encoding='utf-8') as f:
            f.write('\n[backlog row](docs/windows-port/BACKLOG.md#missing-package)\n')
        self.gate('missing Markdown anchor')


if __name__ == '__main__':
    unittest.main()

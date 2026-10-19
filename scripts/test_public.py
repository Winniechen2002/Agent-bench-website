"""Regression tests for public data exports; fixtures use invented source locations."""
import unittest
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from public_data import artifact_id, public_media_entry, public_demo_manifest, validate_document, strict_json


class PublicDataTests(unittest.TestCase):
    def test_detects_private_locations_without_echoing_them(self):
        for value in ('/home/researcher/run.mp4', '/mnt/team/run.json',
                      'gpu-node:/project/run.mp4', 'C:\\Users\\researcher\\run.mp4',
                      '~/.ssh/config', 'ssh researcher@gpu-node', '/Users/researcher/work/data'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as ctx:
                    validate_document({'source_path': value})
                self.assertNotIn(value, str(ctx.exception))

    def test_rejects_private_fields_even_without_absolute_path(self):
        for field in ('source_checkout', 'username', 'source_host', 'command', 'encoding_command', 'api_key'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_document({field: 'unpublished context'})

    def test_accepts_public_references_and_robot_names(self):
        validate_document({'url': 'https://github.com/example/project',
                           'path': 'assets/media/demo.mp4',
                           'source': 'docs/evaluation/hanoi_sharpa.en.md',
                           'counts': {'hanoi_sharpa': 40},
                           'task': 'rubiks_sharpa/floating-sharpa/01'})

    def test_media_projection_preserves_presentation_and_hashes(self):
        raw = {'id': 'demo', 'source_path': '/home/researcher/run.mp4',
               'path': 'assets/media/demo.mp4', 'caption': 'Reference only.',
               'files': [{'path': 'assets/media/demo.mp4', 'sha256': 'a' * 64,
                          'source_path': 'outputs/demo.mp4'}]}
        public = public_media_entry(raw)
        self.assertEqual(public['path'], raw['path'])
        self.assertEqual(public['caption'], raw['caption'])
        self.assertEqual(public['files'][0]['sha256'], 'a' * 64)
        self.assertEqual(public['source_artifact_id'], artifact_id(raw['source_path']))
        self.assertIn('source_path', raw)  # Export must not destroy private input.
        self.assertNotIn('source_path', public)
        validate_document(public)

    def test_manifest_keeps_conditions_and_replay_caveat(self):
        raw = {'version': 2, 'artifacts': [{'id': 'demo',
                'web_asset': {'path': 'assets/media/demo.mp4', 'sha256': 'b' * 64},
                'source_checkout': '/home/researcher/code',
                'trajectory': {'path': '/home/researcher/trace.json', 'kind': 'events only', 'sha256': 'c' * 64},
                'result_paths': ['/home/researcher/result.json'],
                'command': 'python private_runner.py', 'encoding_command': 'ffmpeg private arguments',
                'details': {'seed': 0, 'playback_speed': 6},
                'notes': 'No exact replay claim.'}]}
        public = public_demo_manifest(raw)
        entry = public['artifacts'][0]
        self.assertEqual(entry['web_asset'], raw['artifacts'][0]['web_asset'])
        self.assertEqual(entry['details'], {'seed': 0, 'playback_speed': 6})
        self.assertEqual(entry['notes'], 'No exact replay claim.')
        self.assertEqual(entry['trajectory']['sha256'], 'c' * 64)
        self.assertIn('artifact_id', entry['trajectory'])
        self.assertNotIn('command', entry)
        self.assertNotIn('source_checkout', entry)
        validate_document(public)

    def test_unexpected_private_text_in_caption_fails_closed(self):
        with self.assertRaises(ValueError):
            public_media_entry({'id': 'demo', 'caption': 'Recorded in /home/researcher/work'})

    def test_duplicate_keys_cannot_hide_private_values(self):
        with self.assertRaises(ValueError):
            strict_json('{"note":"/home/researcher/private-run","note":"safe"}')
        with self.assertRaises(ValueError):
            strict_json('{"nested":{"path":"safe","path":"also safe"}}')

    def test_free_text_source_commands_are_rejected(self):
        for value in ('ssh gpu-node', 'python3 private_runner.py --experiment draft',
                      'ffmpeg -i source.mp4 output.mp4'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_document({'note': value})


class ClaudeImportTests(unittest.TestCase):
    """The reported aggregates must survive import independently of outcome counts."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / 'site'
        self.paper = self.root / 'paper'
        self.source_site = Path(__file__).resolve().parents[1]
        (self.site / 'scripts').mkdir(parents=True)
        (self.site / 'data').mkdir()
        (self.paper / 'data').mkdir(parents=True)
        for filename in ('refresh-paper-data.py', 'public_data.py'):
            shutil.copyfile(self.source_site / 'scripts' / filename, self.site / 'scripts' / filename)
        self.original = json.loads((self.source_site / 'data/results.json').read_text())
        self.original['experiments'] = [ex for ex in self.original['experiments']
                                        if ex['id'] != 'claude-opus-5-5-extra-paper']
        self.original['preserved_metadata'] = {'note': 'Keep unrelated snapshot metadata.'}
        (self.site / 'data/results.json').write_text(json.dumps(self.original, ensure_ascii=False, indent=2) + '\n')
        for filename in ('tasks.json', 'ep100-index.json'):
            shutil.copyfile(self.source_site / 'data' / filename, self.site / 'data' / filename)
        self.snapshots = {name: (self.site / 'data' / name).read_bytes()
                          for name in ('tasks.json', 'ep100-index.json')}
        subset_values = {
            'EP-100': (100, 400, 683, 29.22, 35.85),
            'EP-Easy': (50, 200, 332, 33.99, 42.88),
            'EP-Hard': (50, 200, 351, 24.21, 28.48),
            'EP-20': (20, 80, 137, 30.58, 39.13),
        }
        suite_values = {
            'Launch': ((15.51, 27.70), (15.21, 32.60), (15.81, 22.81), (5.65, 19.78)),
            'Tower': ((60.59, 66.14), (71.51, 79.82), (48.58, 51.09), (50.00, 56.25)),
            'Lock': ((39.81, 45.63), (52.03, 60.56), (27.60, 30.70), (37.63, 37.63)),
            'Cube': ((6.04, 10.72), (8.18, 15.03), (3.90, 6.41), (14.82, 27.41)),
            'Home': ((24.17, 29.06), (23.03, 26.41), (25.17, 31.41), (44.80, 54.58)),
        }
        self.source = {
            'model': 'opus-5.5-extra', 'display_name': 'Opus-5.5-extra',
            'reasoning': 'extra', 'status': 'complete',
            'provenance': {
                'source': 'Run-owner-supplied complete empirical run.',
                'scope': '100 tasks, four conditions per task; Home-Long included with zero success.',
                'aggregation': 'Aggregate scores and condition outcomes are independently transcribed.',
                'audit_scope': 'The local GPT audit does not cover this separately supplied run.',
            },
            'subsets': {name: dict(zip(('tasks', 'conditions', 'attempts', 'pass_at_1_percent', 'pass_at_2_percent'), values))
                        for name, values in subset_values.items()},
            'suite_scores_percent': {suite: dict(zip(subset_values, values)) for suite, values in suite_values.items()},
            'suite_outcomes': {
                suite: dict(zip(('conditions', 'successful_conditions', 'failed_conditions', 'gpt_success_reference', 'time_at_success_minutes'), values))
                for suite, values in {
                    'Launch': (136, 36, 100, 35, 6.2), 'Tower': (84, 55, 29, 35, 38.5),
                    'Lock': (64, 20, 44, 9, 37.0), 'Cube': (48, 5, 43, 1, 32.5),
                    'Home': (68, 17, 51, 11, 26.6),
                }.items()
            },
        }
        self.source_path = self.paper / 'data/opus_experiments.json'
        self.source_path.write_text(json.dumps(self.source))
        for name in ('sections/experiments.tex', 'tables/experiment_subsets.tex',
                     'tables/experiment_suites.tex', 'tables/experiment_outcomes.tex'):
            target = self.paper / name
            target.parent.mkdir(exist_ok=True)
            target.write_text('Fixture supporting source: ' + name)

    def run_import(self, *flags):
        return subprocess.run([sys.executable, str(self.site / 'scripts/refresh-paper-data.py'),
                               str(self.paper), '--only-claude', *flags],
                              capture_output=True, text=True)

    def import_successfully(self):
        result = self.run_import()
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads((self.site / 'data/results.json').read_text())
        experiment = next(ex for ex in document['experiments'] if ex['id'] == 'claude-opus-5-5-extra-paper')
        return document, experiment

    def test_preserves_supplied_scores_instead_of_reconstructing_from_conditions(self):
        _, experiment = self.import_successfully()
        expected = {'EP-100': (683, 0.2922, 0.3585), 'EP-Easy': (332, 0.3399, 0.4288),
                    'EP-Hard': (351, 0.2421, 0.2848), 'EP-20': (137, 0.3058, 0.3913)}
        for name, (attempts, first, second) in expected.items():
            subset = experiment['subsets'][name]
            self.assertEqual(subset['valid_attempts'], attempts)
            self.assertAlmostEqual(subset['suite_balanced_pass_at_1'], first)
            self.assertAlmostEqual(subset['suite_balanced_pass_at_2'], second)
            for suite, supplied in self.source['suite_scores_percent'].items():
                self.assertAlmostEqual(subset['suites'][suite]['pass_at_1'], supplied[name][0] / 100)
                self.assertAlmostEqual(subset['suites'][suite]['pass_at_2'], supplied[name][1] / 100)
        self.assertAlmostEqual(experiment['subsets']['EP-100']['suites']['Lock']['pass_at_2'], 0.4563)
        self.assertEqual(experiment['suite_outcomes']['Lock']['successful_conditions'], 20)
        self.assertEqual(experiment['suite_outcomes']['Lock']['conditions'], 64)
        self.assertNotAlmostEqual(experiment['subsets']['EP-100']['suites']['Lock']['pass_at_2'], 20 / 64)
        for suite, outcome in experiment['suite_outcomes'].items():
            expected_outcome = {key: value for key, value in self.source['suite_outcomes'][suite].items()
                                if key != 'gpt_success_reference'}
            self.assertEqual(outcome, expected_outcome)

    def test_reports_provenance_without_fabricating_trial_or_audit_metadata(self):
        document, experiment = self.import_successfully()
        self.assertEqual(experiment['model'], 'opus-5.5-extra')
        self.assertEqual(experiment['display_name'], 'Claude · Opus-5.5-extra')
        self.assertEqual(experiment['reasoning'], 'extra')
        self.assertEqual(experiment['status'], 'complete')
        self.assertEqual(experiment['result_basis'], 'reported_aggregates')
        self.assertEqual(experiment['source']['sha256'], hashlib.sha256(self.source_path.read_bytes()).hexdigest())
        for key, value in self.source['provenance'].items():
            self.assertEqual(experiment['source'][key], value)
        for source in experiment['source']['supporting_sources']:
            self.assertEqual(source['sha256'], hashlib.sha256((self.paper / source['filename']).read_bytes()).hexdigest())
        unsupported = {'audit_counts', 'cold_start_summary', 'disclosure_summary', 'failure_diagnostics',
                       'access_level', 'observation_profile', 'first_successes', 'within_two_successes',
                       'pooled_pass_at_1', 'pooled_pass_at_2', 'task_results_file', 'exclusions'}
        def check_fields(value):
            if isinstance(value, dict):
                self.assertFalse(unsupported.intersection(value))
                for child in value.values():
                    check_fields(child)
            elif isinstance(value, list):
                for child in value:
                    check_fields(child)
        check_fields(experiment)
        codex = next(ex for ex in document['experiments'] if ex['id'] == 'codex-gpt-6-astra-l3-paper')
        for name, subset in experiment['subsets'].items():
            for suite, values in subset['suites'].items():
                self.assertNotIn('valid_attempts', values)
                for key in ('tasks', 'conditions'):
                    self.assertEqual(values[key], codex['subsets'][name]['suites'][suite][key])
        validate_document(experiment)

    def test_only_claude_is_idempotent_and_check_does_not_modify_existing_snapshots(self):
        original_results = (self.site / 'data/results.json').read_bytes()
        self.assertNotEqual(self.run_import('--check').returncode, 0)
        self.assertEqual((self.site / 'data/results.json').read_bytes(), original_results)
        document, _ = self.import_successfully()
        preserved = copy.deepcopy(document)
        preserved['experiments'] = [ex for ex in preserved['experiments'] if ex['id'] != 'claude-opus-5-5-extra-paper']
        self.assertEqual(preserved, self.original)
        imported = (self.site / 'data/results.json').read_bytes()
        self.assertEqual(self.run_import('--check').returncode, 0)
        self.import_successfully()
        self.assertEqual((self.site / 'data/results.json').read_bytes(), imported)
        self.source['subsets']['EP-100']['pass_at_1_percent'] = 29.23
        self.source_path.write_text(json.dumps(self.source))
        self.assertNotEqual(self.run_import('--check').returncode, 0)
        self.assertEqual((self.site / 'data/results.json').read_bytes(), imported)
        for filename, content in self.snapshots.items():
            self.assertEqual((self.site / 'data' / filename).read_bytes(), content)


if __name__ == '__main__':
    unittest.main()

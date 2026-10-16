"""Sync regression fixtures contain invented artifacts and never use the live upstream."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from sync_benchmark import FAMILIES
from build_site import build_release
from test_release import fixture as release_fixture


def digest(content):
    return hashlib.sha256(content).hexdigest()


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


class MediaSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'website'
        self.source = Path(self.temp.name) / 'upstream'
        self.root.mkdir()
        shutil.copytree(Path(__file__).parent, self.root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
        self.source.mkdir()
        self.original = b'upstream image or long source video'
        self.derivative = b'website short video'
        (self.source / 'outputs').mkdir()
        (self.source / 'outputs/demo.png').write_bytes(self.original)
        (self.root / 'assets/media').mkdir(parents=True)
        (self.root / 'assets/media/demo.mp4').write_bytes(self.derivative)
        entry = dict(id='demo', task='marble', case_ids=['marble/panda/01'], media_kind='image',
            path='assets/media/demo.mp4', caption='Historical reference.', source_path='outputs/demo.png',
            files=[dict(path='assets/media/demo.mp4', source_path='outputs/demo.png',
                        sha256=digest(self.original), bytes=len(self.original))])
        write(self.source, 'docs/website_media_catalog.json', dict(entries=[entry], evidence_sources={}))
        self.override = dict(id='demo', task='marble', case_ids=['marble/panda/01'], media_kind='video',
            path='assets/media/demo.mp4', caption='Historical reference. Playback: 4×.', playback_speed=4,
            duration_seconds=12.5, source_artifacts=[dict(artifact_id='source-original', sha256=digest(self.original))],
            files=[dict(path='assets/media/demo.mp4', sha256=digest(self.derivative), bytes=len(self.derivative))])
        self.overlay = dict(schema_version=1, entries=[self.override], group_media={'marble': ['demo']}, removed_media_ids=[])
        write(self.root, 'scripts/media-overrides.json', self.overlay)
        write(self.root, 'data/environment-media.json', [])
        write(self.root, 'data/environment-groups.json', [dict(id='marble', task_ids=['marble/panda/01'])])
        tasks = [dict(task_id=f'{family}/panda/01', configuration_sha256='f'*64,
            budgets={}, groups=[dict(variant='base', trials=[{}]*4)]) for family in FAMILIES]
        source_catalog = 'source/agentbench_platform/agentbench_platform/environment_catalog.py'
        catalog_file = self.source / source_catalog
        catalog_file.parent.mkdir(parents=True)
        catalog_file.write_text('EXPECTED = ' + repr({family: 1 for family in FAMILIES}))
        (catalog_file.parent / 'profiles.py').write_text("CAPABILITY_VERSION = 'fixture'\n")
        write(self.source, 'docs/evaluation/tasks.json', dict(version='fixture', base_seed=0, tasks=tasks,
            task_count=len(tasks), group_count=len(tasks), planned_episodes=len(tasks)*4,
            sources={source_catalog: digest(catalog_file.read_bytes())}))
        for name in ['README.en.md', 'docs/evaluation_protocol.en.md', 'LICENSING.md'] + [f'docs/evaluation/{family}.en.md' for family in FAMILIES]:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Fixture')
        write(self.source, 'env/runtime/release-scope-decision.json', {'full_environment_qualification': 'not_established'})
        write(self.source, 'env/runtime/license-decisions.json', {'source_release_ready': False})

    def run_sync(self, script, *flags):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / script), str(self.source), *flags],
                              capture_output=True, text=True)

    def test_sync_and_check_preserve_short_video_and_original_source_hash(self):
        result = self.run_sync('sync_media.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / self.override['path']).read_bytes(), self.derivative)
        media = json.loads((self.root / 'data/environment-media.json').read_text())
        self.assertEqual(media, [{k: v for k, v in self.override.items() if k != 'files'}])
        provenance = json.loads((self.root / 'data/environment-media-sources.json').read_text())
        self.assertEqual(provenance['entries'], [self.override])
        self.assertEqual(provenance['website_derivative_ids'], ['demo'])
        self.assertEqual(provenance['retired_media'], [])
        self.assertNotEqual(provenance['entries'][0]['files'][0]['sha256'], self.override['source_artifacts'][0]['sha256'])
        result = self.run_sync('sync_media.py', '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_original_catalog_gaps_are_qualified_after_website_overrides(self):
        catalog_path = self.source / 'docs/website_media_catalog.json'
        catalog = json.loads(catalog_path.read_text())
        catalog['gaps'] = ['Bookshelf robot rollout', 'ManiSkill policy-executed rollout']
        write(self.source, 'docs/website_media_catalog.json', catalog)
        result = self.run_sync('sync_media.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        provenance = json.loads((self.root / 'data/environment-media-sources.json').read_text())
        self.assertNotIn('gaps', provenance)
        self.assertEqual(provenance['upstream_catalog_gaps'], catalog['gaps'])
        self.assertIn('before website overrides', provenance['coverage_note'])
        self.assertIn('entries', provenance['coverage_note'])
        self.assertEqual(provenance['entries'], [self.override])
        result = self.run_sync('sync_media.py', '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_final_group_association_survives_sync_and_check(self):
        self.overlay['entries'].append(dict(self.override, id='website-owned'))
        self.overlay['group_media']['marble'] = ['website-owned']
        write(self.root, 'scripts/media-overrides.json', self.overlay)
        result = self.run_sync('sync_benchmark.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        cards = json.loads((self.root / 'data/environment-groups.json').read_text())
        self.assertEqual(next(card['media'] for card in cards if card['id'] == 'marble'), ['website-owned'])
        result = self.run_sync('sync_benchmark.py', '--check')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_group_override_cannot_associate_a_different_native_family(self):
        self.overlay['group_media'] = {'hanoi_panda': ['demo']}
        write(self.root, 'scripts/media-overrides.json', self.overlay)
        result = self.run_sync('sync_benchmark.py')
        self.assertNotEqual(result.returncode, 0, 'sync accepted a cross-family media association')

    def test_tampered_derivative_is_rejected_before_copying(self):
        (self.root / self.override['path']).write_bytes(b'tampered derivative')
        result = self.run_sync('sync_media.py')
        self.assertNotEqual(result.returncode, 0, 'sync accepted tampered website derivative')
        self.assertEqual((self.root / self.override['path']).read_bytes(), b'tampered derivative')

    def test_override_does_not_bypass_upstream_source_hash_guard(self):
        (self.source / 'outputs/demo.png').write_bytes(b'tampered upstream')
        result = self.run_sync('sync_media.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Stale selected media', result.stderr)
        self.assertEqual((self.root / self.override['path']).read_bytes(), self.derivative)

    def test_website_owned_entry_can_replace_nonimported_preview(self):
        self.override['id'] = 'website-only'
        self.overlay['entries'] = [self.override]
        self.overlay['removed_media_ids'] = ['demo']
        write(self.root, 'scripts/media-overrides.json', self.overlay)
        write(self.root, 'data/environment-media.json', [dict(id='website-only', task='marble', media_kind='image')])
        # The overridden derivative has a distinct output from the retired upstream image.
        catalog = json.loads((self.source / 'docs/website_media_catalog.json').read_text())
        catalog['entries'][0]['path'] = catalog['entries'][0]['files'][0]['path'] = 'assets/images/demo.png'
        write(self.source, 'docs/website_media_catalog.json', catalog)
        result = self.run_sync('sync_media.py')
        self.assertEqual(result.returncode, 0, result.stderr)
        live = json.loads((self.root / 'data/environment-media.json').read_text())
        self.assertEqual([item['id'] for item in live], ['website-only'])
        self.assertEqual(live[0]['media_kind'], 'video')

    def test_current_only_retirement_is_idempotent_and_keeps_nonvideo_guard(self):
        write(self.root, 'data/environment-media.json', [dict(id='local-preview', task='marble', media_kind='image')])
        self.overlay['removed_media_ids'] = ['local-preview']
        write(self.root, 'scripts/media-overrides.json', self.overlay)
        for flags in ((), ('--check',), ()):
            result = self.run_sync('sync_media.py', *flags)
            self.assertEqual(result.returncode, 0, result.stderr)
        provenance = json.loads((self.root / 'data/environment-media-sources.json').read_text())
        self.assertEqual(provenance['retired_media'], [dict(id='local-preview', task='marble', media_kind='image')])
        # A video introduced under a previously retired ID still cannot be retired.
        current = json.loads((self.root / 'data/environment-media.json').read_text())
        current.append(dict(id='local-preview', task='marble', media_kind='video'))
        write(self.root, 'data/environment-media.json', current)
        result = self.run_sync('sync_media.py')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Only scene previews', result.stderr)

    def test_release_contains_derivative_but_not_overlay_configuration(self):
        output_root = Path(self.temp.name) / 'release'
        output_root.mkdir()
        release_fixture(output_root)
        write(output_root, 'scripts/media-overrides.json', self.overlay)
        write(output_root, 'data/environment-media.json', [self.override])
        (output_root / 'assets/media/demo.mp4').write_bytes(self.derivative)
        output = build_release(output_root, checks=lambda root: None)
        self.assertEqual((output / self.override['path']).read_bytes(), self.derivative)
        self.assertFalse((output / 'scripts/media-overrides.json').exists())


if __name__ == '__main__':
    unittest.main()

"""Regression tests for public data exports; fixtures use invented source locations."""
import unittest
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


if __name__ == '__main__':
    unittest.main()

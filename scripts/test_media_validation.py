"""Public presentation requirements use tiny files; ffprobe checks real releases separately."""
import json
import hashlib
from pathlib import Path
import tempfile
import shutil
import subprocess
import unittest


def write(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class MediaValidationTests(unittest.TestCase):
    def setUp(self):
        from check_media import validate_media
        self.validate = validate_media
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'assets/media').mkdir(parents=True)
        (self.root / 'assets/media/demo.mp4').write_bytes(b'video fixture')
        self.video = dict(id='clip', path='assets/media/demo.mp4', media_kind='video',
                          duration_seconds=59, playback_speed=4, caption='Playback: 4×.')
        self.write_media()
        write(self.root, 'evidence/demo-manifest.json', {'artifacts': []})
        write(self.root, 'data/environment-media-sources.json', {'entries': []})
        write(self.root, 'data/tasks.json', [dict(id='task', media=['clip'])])
        write(self.root, 'data/environment-groups.json', [dict(id='native', media=['clip'])])

    def write_media(self):
        write(self.root, 'data/media.json', [self.video])
        write(self.root, 'data/environment-media.json', [self.video])

    def test_approved_media_validates_and_soft_target_is_reported(self):
        self.assertEqual(self.validate(self.root)['over_target'], [])
        self.video['duration_seconds'] = 61
        self.write_media()
        self.assertEqual(self.validate(self.root)['over_target'], ['assets/media/demo.mp4'])

    def test_visible_static_image_is_rejected(self):
        self.video['media_kind'] = 'image'
        self.write_media()
        with self.assertRaisesRegex(AssertionError, 'Visible media must be video'):
            self.validate(self.root)

    def test_hard_duration_and_missing_duration_are_rejected(self):
        for duration in (121, None):
            self.video['duration_seconds'] = duration
            self.write_media()
            with self.subTest(duration=duration), self.assertRaisesRegex(AssertionError, 'duration'):
                self.validate(self.root)

    def test_speed_metadata_must_match_public_caption(self):
        self.video['caption'] = 'Playback: 8×.'
        self.write_media()
        with self.assertRaisesRegex(AssertionError, 'speed'):
            self.validate(self.root)

    def test_rendered_playback_badge_is_validated_and_can_supply_label(self):
        self.video['playback_label'] = '8× playback'
        self.write_media()
        with self.assertRaisesRegex(AssertionError, 'speed'):
            self.validate(self.root)
        self.video['caption'] = 'Reference execution.'
        self.video['playback_label'] = '4× playback'
        self.write_media()
        self.validate(self.root)

    def test_source_and_stage_apply_identical_new_video_size_policy(self):
        with (self.root / self.video['path']).open('wb') as file:
            file.truncate(5_000_001)
        source_overlay = self.root / 'scripts/media-overrides.json'
        for is_new in (False, True):
            write(self.root, 'data/environment-media-sources.json', dict(entries=[self.video],
                website_derivative_ids=['clip'] if is_new else []))
            for source_tree in (True, False):
                if source_tree:
                    write(self.root, 'scripts/media-overrides.json', dict(entries=[self.video] if is_new else []))
                else:
                    source_overlay.unlink()
                with self.subTest(is_new=is_new, source_tree=source_tree):
                    if is_new:
                        with self.assertRaisesRegex(AssertionError, '5 MB'):
                            self.validate(self.root)
                    else:
                        self.validate(self.root)

    def test_single_new_video_must_be_below_five_megabytes(self):
        write(self.root, 'scripts/media-overrides.json', dict(entries=[self.video]))
        write(self.root, 'data/environment-media-sources.json', dict(entries=[self.video], website_derivative_ids=['clip']))
        with (self.root / self.video['path']).open('wb') as file:
            file.truncate(5_000_000)
        with self.assertRaisesRegex(AssertionError, '5 MB'):
            self.validate(self.root)

    def add_promo(self, **changes):
        promo = dict(id='embodied-playground-film', path='assets/media/promo.mp4', media_kind='video',
            media_usage='hero-promo', showcase=False, duration_seconds=180, playback_speed=1, playback_label='3:00')
        promo.update(changes)
        (self.root / promo['path']).write_bytes(b'promo fixture')
        write(self.root, 'data/media.json', [self.video, promo])
        return promo

    def test_hero_exception_is_limited_to_named_unassociated_original_timing_film(self):
        for changes in (dict(id='another-film'), dict(duration_seconds=181), dict(playback_speed=2), dict(showcase=True)):
            self.add_promo(**changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(AssertionError, 'hero'):
                self.validate(self.root)
        promo = self.add_promo()
        write(self.root, 'data/tasks.json', [dict(id='task', media=['clip', promo['id']])])
        with self.assertRaisesRegex(AssertionError, 'hero'):
            self.validate(self.root)
        write(self.root, 'data/tasks.json', [dict(id='task', media=['clip'])])
        write(self.root, 'data/environment-media.json', [self.video, promo])
        with self.assertRaisesRegex(AssertionError, 'hero'):
            self.validate(self.root)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'real duration regression requires FFmpeg')
    def test_actual_three_minute_film_passes_but_same_length_rollout_fails(self):
        promo = self.add_promo()
        for name, duration in ((self.video['path'], 1), (promo['path'], 180)):
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=size=16x16:rate=1',
                '-t', str(duration), '-c:v', 'libx264', '-preset', 'ultrafast', str(self.root / name)], check=True)
        self.video['duration_seconds'] = 1
        write(self.root, 'data/environment-media.json', [self.video])
        write(self.root, 'data/media.json', [self.video, promo])
        result = self.validate(self.root, probe=True)
        self.assertEqual(result['over_target'], [])
        promo.pop('media_usage')
        promo['id'] = 'ordinary-long-rollout'
        write(self.root, 'data/media.json', [self.video, promo])
        with self.assertRaisesRegex(AssertionError, '120'):
            self.validate(self.root, probe=True)

    def test_total_assets_budget_counts_unreferenced_files(self):
        with (self.root / 'assets/media/unreferenced.mp4').open('wb') as file:
            file.truncate(100_000_000)
        with self.assertRaisesRegex(AssertionError, '100 MB'):
            self.validate(self.root)


class ManifestResourceTests(unittest.TestCase):
    def setUp(self):
        from check_media import check_manifest_resources
        self.check = check_manifest_resources
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'assets/media').mkdir(parents=True)
        (self.root / 'assets/posters').mkdir()
        self.video = self.resource('assets/media/current.mp4', b'current short video', 'bytes')
        self.poster = self.resource('assets/posters/current.jpg', b'current poster', 'size_bytes')
        self.artifact = dict(id='clip', source_video={'sha256':'f'*64, 'size_bytes':999999},
            web_asset=dict(self.video, poster=self.poster), web_files=[self.video, self.poster])
        write(self.root, 'data/media.json', [dict(id='clip', media_kind='video', path=self.video['path'])])
        write(self.root, 'data/environment-media.json', [])
        self.save()

    def resource(self, path, content, size_field='bytes'):
        (self.root / path).write_bytes(content)
        return dict(path=path, sha256=hashlib.sha256(content).hexdigest(), **{size_field:len(content)})

    def save(self):
        write(self.root, 'evidence/demo-manifest.json', {'artifacts':[self.artifact]})

    def test_valid_resources_allow_original_source_hash_and_legacy_artifact_id(self):
        self.check(self.root)
        self.artifact['id'] = 'legacy-name-for-same-clip'
        self.save()
        self.check(self.root)

    def test_every_web_resource_and_nested_poster_hash_is_verified(self):
        for resource in (self.artifact['web_asset'], self.poster, self.artifact['web_files'][0]):
            original = resource['sha256']
            resource['sha256'] = 'a'*64
            self.save()
            with self.subTest(path=resource['path']), self.assertRaisesRegex(AssertionError, 'hash'):
                self.check(self.root)
            resource['sha256'] = original

    def test_size_fields_are_verified_for_both_manifest_shapes(self):
        for resource, field in ((self.artifact['web_asset'],'bytes'), (self.poster,'size_bytes')):
            original = resource[field]
            resource[field] += 1
            self.save()
            with self.subTest(field=field), self.assertRaisesRegex(AssertionError, 'size'):
                self.check(self.root)
            resource[field] = original

    def test_old_existing_video_path_is_rejected_despite_correct_hash(self):
        old = self.resource('assets/media/old-long.mp4', b'old complete long source')
        self.artifact.pop('web_asset')
        self.artifact['web_files'] = [old, self.poster]
        self.save()
        with self.assertRaisesRegex(AssertionError, 'canonical'):
            self.check(self.root)
        self.artifact['id'] = 'legacy-name'
        self.artifact['media_ids'] = ['clip']
        self.save()
        with self.assertRaisesRegex(AssertionError, 'canonical'):
            self.check(self.root)

    def test_extra_old_video_cannot_ship_alongside_canonical_video(self):
        self.artifact['web_files'].append(self.resource('assets/media/old-long.mp4', b'old complete long source'))
        self.save()
        with self.assertRaisesRegex(AssertionError, 'canonical'):
            self.check(self.root)


if __name__ == '__main__':
    unittest.main()

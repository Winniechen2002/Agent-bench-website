"""Regression tests for release isolation and the local preview HTTP boundary."""
from contextlib import contextmanager
import http.client
import importlib
import json
from pathlib import Path
import tempfile
import threading
import unittest


DATA_FILES = (
    'benchmark.json', 'environment-catalog.json', 'environment-groups.json',
    'environment-media-sources.json', 'environment-media.json',
    'environment-results.json', 'ep100-index.json', 'media.json',
    'results.json', 'tasks.json',
)


def fixture(root):
    (root / 'data').mkdir()
    (root / 'evidence').mkdir()
    (root / 'assets/images').mkdir(parents=True)
    (root / 'assets/media').mkdir()
    for name in DATA_FILES:
        (root / 'data' / name).write_text('[]')
    (root / 'data/environment-media-sources.json').write_text('{"entries": []}')
    (root / 'data/media.json').write_text(json.dumps([
        {'path': 'assets/media/clip.mp4', 'poster': 'assets/images/poster.png'}
    ]))
    (root / 'evidence/demo-manifest.json').write_text(json.dumps({
        'artifacts': [{'web_files': [{'path': 'assets/images/evidence.png'}]}]
    }))
    (root / 'index.html').write_text('<!doctype html><link href="site.css"><script src="site.js"></script><img src="assets/images/icon.svg"><a href="environment.html">Environment</a>')
    (root / 'environment.html').write_text('<!doctype html><link href="environment.css"><script src="environment.js"></script>')
    for name in ('site.css', 'environment.css', 'site.js', 'environment.js', '.nojekyll'):
        (root / name).write_text('')
    for name in ('poster.png', 'evidence.png', 'icon.svg'):
        (root / 'assets/images' / name).write_bytes(b'public image')
    (root / 'assets/media/clip.mp4').write_bytes(b'0123456789')
    (root / 'assets/images/unlisted.png').write_bytes(b'private unlisted asset')
    (root / 'README.md').write_text('private source documentation')
    (root / '.codex-local').mkdir()
    (root / '.codex-local/secret.json').write_text('{"private": true}')
    (root / 'data/unlisted.json').write_text('{"private": true}')


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((Path(__file__).parent / 'build_site.py').is_file(), 'release builder is missing')
        self.builder = importlib.import_module('build_site')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)

    def build(self):
        return self.builder.build_release(self.root, checks=lambda root: None)

    def test_release_excludes_source_and_unreferenced_files(self):
        output = self.build()
        self.assertEqual(output, self.root / 'dist')
        files = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
        self.assertEqual(len(files), 22)
        self.assertNotIn('README.md', files)
        self.assertNotIn('.codex-local/secret.json', files)
        self.assertNotIn('data/unlisted.json', files)
        self.assertNotIn('assets/images/unlisted.png', files)
        self.assertIn('assets/images/evidence.png', files)
        self.assertIn('.nojekyll', files)

    def test_rebuild_removes_stale_release_files(self):
        output = self.build()
        (output / 'stale.txt').write_text('stale private data')
        (output / 'assets/images/stale.png').write_bytes(b'stale')
        self.build()
        self.assertFalse((output / 'stale.txt').exists())
        self.assertFalse((output / 'assets/images/stale.png').exists())

    def test_checks_cover_source_and_staged_release(self):
        seen = []
        self.builder.build_release(self.root, checks=lambda root: seen.append(root))
        self.assertEqual(seen[0], self.root)
        self.assertEqual(len(seen), 2)
        self.assertNotEqual(seen[1], self.root)

    def test_failed_checks_do_not_publish_release(self):
        def reject(_):
            raise ValueError('sensitive input')
        with self.assertRaises(ValueError):
            self.builder.build_release(self.root, checks=reject)
        self.assertFalse((self.root / 'dist').exists())

    def test_invalid_asset_reference_rejected(self):
        for path in ('../README.md', 'assets/../../README.md', '/etc/passwd',
                     'assets/.private.png', 'assets/images/%2e%2e/secret',
                     'assets\\images\\poster.png', 'https://example.org/image.png'):
            with self.subTest(path=path):
                (self.root / 'data/media.json').write_text(json.dumps([{'path': path}]))
                with self.assertRaises(ValueError):
                    self.build()

    def test_source_file_symlink_rejected(self):
        target = self.root / 'assets/images/poster.png'
        target.unlink()
        target.symlink_to(self.root / 'README.md')
        with self.assertRaises(ValueError):
            self.build()

    def test_source_directory_symlink_rejected(self):
        source = self.root / 'assets/images'
        moved = self.root / 'private-images'
        source.rename(moved)
        source.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.build()

    def test_output_symlink_rejected_without_modifying_target(self):
        target = self.root / 'outside'
        target.mkdir()
        (target / 'keep.txt').write_text('keep')
        (self.root / 'dist').symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual((target / 'keep.txt').read_text(), 'keep')

    def test_html_cannot_request_private_file(self):
        (self.root / 'index.html').write_text('<a href="README.md">Private</a>')
        with self.assertRaises(ValueError):
            self.build()

    @contextmanager
    def server(self):
        preview = importlib.import_module('serve_site')
        output = self.build()
        server = preview.create_server(output, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server, output
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def request(self, server, path, method='GET', headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_root_and_project_prefix_assets_are_served(self):
        with self.server() as (server, _):
            for prefix in ('', '/Agent-bench-website'):
                for path in ('/', '/environment.html', '/site.js', '/data/media.json', '/assets/media/clip.mp4'):
                    with self.subTest(path=prefix + path):
                        self.assertEqual(self.request(server, prefix + path)[0], 200)

    def test_private_paths_encoded_traversal_and_directories_are_404(self):
        paths = ('/.git/config', '/.codex-local/secret.json', '/README.md',
                 '/scripts/build_site.py', '/package.json', '/.nojekyll',
                 '/data/', '/assets/', '/assets/images/unlisted.png',
                 '/../README.md', '/%2e%2e/README.md', '/%252e%252e/README.md',
                 '/assets/%2e%2e/%2e%2e/README.md', '/%2Fetc/passwd',
                 '/assets%5c..%5cREADME.md', '/assets/images//poster.png',
                 '/assets/images/poster.png%00', '/assets/images/%FF')
        with self.server() as (server, _):
            for prefix in ('', '/Agent-bench-website'):
                for path in paths:
                    with self.subTest(path=prefix + path):
                        self.assertEqual(self.request(server, prefix + path)[0], 404)

    def test_files_added_after_start_are_unreachable(self):
        with self.server() as (server, output):
            (output / 'assets/images/private.png').write_bytes(b'private')
            self.assertEqual(self.request(server, '/assets/images/private.png')[0], 404)

    def test_file_and_directory_symlink_replacements_are_unreachable(self):
        with self.server() as (server, output):
            image = output / 'assets/images/poster.png'
            image.unlink()
            image.symlink_to(self.root / 'README.md')
            self.assertEqual(self.request(server, '/assets/images/poster.png')[0], 404)
            directory = output / 'assets/media'
            directory.rename(output / 'moved-media')
            directory.symlink_to(output / 'moved-media', target_is_directory=True)
            self.assertEqual(self.request(server, '/assets/media/clip.mp4')[0], 404)

    def test_head_and_video_ranges(self):
        with self.server() as (server, _):
            status, headers, body = self.request(server, '/assets/media/clip.mp4', 'HEAD')
            self.assertEqual((status, headers['Content-Length'], body), (200, '10', b''))
            for value, expected in (('bytes=2-5', b'2345'), ('bytes=7-', b'789'), ('bytes=-3', b'789')):
                status, headers, body = self.request(server, '/assets/media/clip.mp4', headers={'Range': value})
                self.assertEqual(status, 206)
                self.assertEqual(body, expected)
                self.assertEqual(headers['Accept-Ranges'], 'bytes')
            status, _, body = self.request(server, '/assets/media/clip.mp4', 'HEAD', {'Range': 'bytes=2-5'})
            self.assertEqual((status, body), (206, b''))
            for value in ('bytes=99-', 'bytes=5-2', 'bytes=0-1,4-5', 'bytes=-0'):
                self.assertEqual(self.request(server, '/assets/media/clip.mp4', headers={'Range': value})[0], 416)

    def test_server_rejects_extra_release_files_at_startup(self):
        preview = importlib.import_module('serve_site')
        output = self.build()
        (output / 'private.txt').write_text('private')
        with self.assertRaises(ValueError):
            preview.create_server(output, port=0)


if __name__ == '__main__':
    unittest.main()

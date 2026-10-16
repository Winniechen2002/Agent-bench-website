"""Build an audited static release. Never copy the repository recursively."""
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATIC_FILES = frozenset({
    'index.html', 'environment.html', 'site.css', 'site.js',
    'environment.css', 'environment.js', '.nojekyll',
})
DATA_FILES = frozenset('data/' + name for name in (
    'benchmark.json', 'environment-catalog.json', 'environment-groups.json',
    'environment-media-sources.json', 'environment-media.json',
    'environment-results.json', 'ep100-index.json', 'media.json',
    'results.json', 'tasks.json',
))
BASE_FILES = STATIC_FILES | DATA_FILES | {'evidence/demo-manifest.json'}
ASSET_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.mp4', '.webm', '.avif', '.ico'}


def clean_path(value):
    """Require a literal, relative POSIX filename, without URL decoding aliases."""
    if not isinstance(value, str) or not value or any(c in value for c in '\\%?#:'):
        raise ValueError('Invalid release path')
    parts = value.split('/')
    if any(not part or part in ('.', '..') or part.startswith('.') for part in parts):
        if value != '.nojekyll':
            raise ValueError('Hidden or non-relative release path')
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Control character in release path')
    return value


def source_file(root, relative):
    clean_path(relative)
    current = root
    if current.is_symlink() or not current.is_dir():
        raise ValueError('Release root must be a real directory')
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlinks are not permitted in release inputs')
    if not current.is_file():
        raise ValueError(f'Missing release file: {relative}')
    return current


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def read_json(root, name):
    return json.loads(source_file(root, name).read_text(encoding='utf-8'), object_pairs_hook=unique_object)


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in ('href', 'src', 'poster') and value)


def release_files(root):
    """The exact static allowlist plus assets referenced by audited runtime fields."""
    files = set(BASE_FILES)
    for relative in files:
        source_file(root, relative)

    def asset(value):
        clean_path(value)
        if not value.startswith('assets/') or PurePosixPath(value).suffix.lower() not in ASSET_SUFFIXES:
            raise ValueError('Runtime media must reference a supported file under assets/')
        source_file(root, value)
        files.add(value)

    def media(entry):
        if not isinstance(entry, dict):
            raise ValueError('Media entry must be an object')
        for key in ('path', 'poster', 'fallback'):
            if entry.get(key) and not (key == 'fallback' and entry[key] == 'image'):
                asset(entry[key])

    for name in ('data/media.json', 'data/environment-media.json'):
        entries = read_json(root, name)
        if not isinstance(entries, list):
            raise ValueError('Media collection must be a list')
        for entry in entries:
            media(entry)
    for entry in read_json(root, 'data/environment-media-sources.json')['entries']:
        media(entry)
        for resource in entry['files']:
            asset(resource['path'])
    for entry in read_json(root, 'evidence/demo-manifest.json')['artifacts']:
        web = entry.get('web_asset')
        if web:
            asset(web['path'])
            if web.get('poster'):
                asset(web['poster']['path'])
        for resource in entry.get('web_files', []):
            asset(resource['path'])

    def local_reference(value):
        url = urlsplit(value)
        if url.scheme or url.netloc or not url.path:
            return
        relative = clean_path(url.path)
        if relative.startswith('assets/'):
            asset(relative)
        elif relative not in BASE_FILES:
            raise ValueError('Local page reference is outside the release allowlist')

    for name in ('index.html', 'environment.html'):
        page = References()
        page.feed(source_file(root, name).read_text(encoding='utf-8'))
        for url in page.urls:
            local_reference(url)
    for name in ('site.css', 'environment.css'):
        for _, url in re.findall(r'url\(\s*([\'\"]?)(.*?)\1\s*\)', source_file(root, name).read_text(encoding='utf-8')):
            local_reference(url)
    return frozenset(files)


def verify_release(root):
    expected = release_files(root)
    actual = set()
    expected_dirs = {parent.as_posix() for name in expected for parent in PurePosixPath(name).parents}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError('Symlinks are not permitted in a release')
            relative = path.relative_to(root).as_posix()
            if path.is_dir():
                if relative not in expected_dirs:
                    raise ValueError('Unexpected directory in release')
            elif not stat.S_ISREG(path.stat().st_mode):
                raise ValueError('Release contains a non-regular file')
            else:
                actual.add(relative)
    if actual != expected:
        raise ValueError('Release inventory differs from its explicit allowlist')
    return expected


def run_checks(root):
    for name in ('check_public.py', 'check_site.py', 'validate-site.py'):
        subprocess.run([sys.executable, str(ROOT / 'scripts' / name), '--root', str(root)], check=True)


def build_release(root=ROOT, *, checks=run_checks):
    root = Path(root).absolute()
    output = root / 'dist'
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError('dist must be a real directory, never a symlink or file')
    files = release_files(root)
    checks(root)
    staging = Path(tempfile.mkdtemp(prefix='.release-build-', dir=root))
    try:
        for relative in sorted(files):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file(root, relative), destination)
        verify_release(staging)
        checks(staging)
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output


def main():
    try:
        output = build_release()
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f'Release build failed: {error}', file=sys.stderr)
        return 1
    print(f'PASS: built {len(verify_release(output))} audited files in dist/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

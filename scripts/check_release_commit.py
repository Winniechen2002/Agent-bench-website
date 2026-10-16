"""Read-only gate for the exact Git commit intended for publication.

Unlike a working-tree check, this catches forgotten additions and deletions.
It does not rewrite, commit, stage, fetch, or push anything, nor certify history.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile
import sys
from build_site import ROOT, release_files, run_checks, clean_path

SOURCE_FILES = frozenset({
    '.gitignore', 'README.md', 'package.json', '.github/workflows/pages.yml',
    'scripts/build_site.py', 'scripts/serve_site.py', 'scripts/check_site.py',
    'scripts/validate-site.py', 'scripts/check_public.py', 'scripts/public_data.py',
    'scripts/check_release_commit.py', 'scripts/test_public.py', 'scripts/test_release.py',
    'scripts/refresh-paper-data.py', 'scripts/sync_benchmark.py', 'scripts/sync_media.py',
})


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.PIPE)


def check_commit(ref):
    commit = git('rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()
    records = git('ls-tree', '-rz', '--full-tree', commit).split(b'\0')
    entries = []
    for record in records:
        if not record:
            continue
        metadata, raw_name = record.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        name = raw_name.decode('utf-8')
        if mode not in ('100644', '100755') or kind != 'blob':
            raise ValueError('Commit contains a symlink, submodule, or unsupported tree entry')
        if name not in SOURCE_FILES:
            clean_path(name)
        entries.append((name, oid))
    names = {name for name, _ in entries}
    forbidden = [name for name in names if name not in SOURCE_FILES and
                 not name.startswith(('assets/', 'data/', 'evidence/')) and
                 name not in ('index.html', 'environment.html', 'site.css', 'site.js',
                              'environment.css', 'environment.js', '.nojekyll')]
    if forbidden:
        raise ValueError(f'Commit still contains {len(forbidden)} unreviewed/retired files; first: {sorted(forbidden)[0]}')
    missing = SOURCE_FILES - names
    if missing:
        raise ValueError(f'Commit lacks {len(missing)} required source/check files; first: {sorted(missing)[0]}')
    with tempfile.TemporaryDirectory(prefix='website-commit-check-') as directory:
        snapshot = Path(directory)
        for name, oid in entries:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git('cat-file', 'blob', oid))
        expected = release_files(snapshot) | SOURCE_FILES
        if names != expected:
            raise ValueError('Committed file set differs from the reviewed source and release allowlists')
        run_checks(snapshot)  # Current validators; never execute code from the target commit.
    print(f'PASS: commit {commit[:12]} contains only {len(names)} reviewed source/release files.')
    print('Scope: this commit only. Earlier commits, forks, and cached remote views are not cleared by this check.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', default='HEAD', help='Commit or ref to inspect; default HEAD')
    args = parser.parse_args()
    try:
        check_commit(args.ref)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'BLOCKED: selected commit is not ready for publication: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

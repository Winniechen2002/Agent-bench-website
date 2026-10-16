"""Copy curated native media from Agent-bench without redrawing or recompression.

python3 scripts/sync_media.py ../Agent-bench [--check]
Requires only Python's standard library. Existing native media outside the selection is retained.
Paper media.json is managed separately and is never rewritten by this importer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from public_data import public_media_entry, public_media_catalog, validate_document

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'docs/website_media_catalog.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes root: {name}')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path, default=ROOT.parent / 'Agent-bench')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    catalog = json.loads((source / CATALOG).read_text())
    entries = catalog['entries']
    assert len({m['id'] for m in entries}) == len(entries)
    tasks = json.loads((ROOT / 'data/environment-groups.json').read_text())
    ids = {t['id']: set(t['task_ids']) for t in tasks}
    # Validate the entire import before copying any file.
    for m in entries:
        assert m['task'] in ids and set(m['case_ids']) <= ids[m['task']]
        for f in m['files']:
            assert f['path'].startswith('assets/')
            original = safe_path(source, f['source_path'])
            assert original.stat().st_size == f['bytes'] and sha(original) == f['sha256'], f'Stale selected media: {original}'
    for name, expected in catalog['evidence_sources'].items():
        assert sha(safe_path(source, name)) == expected, f'Stale evidence context: {name}'
    current = json.loads((ROOT / 'data/environment-media.json').read_text())
    selected = {m['id'] for m in entries}
    merged = [m for m in current if m['id'] not in selected]
    merged.extend(public_media_entry({k:v for k,v in m.items() if k != 'files'}) for m in entries)
    provenance = public_media_catalog(dict(catalog, source_catalog=CATALOG, source_catalog_sha256=sha(source / CATALOG)))
    validate_document(merged, 'native media')
    for m in entries:
        for f in m['files']:
            output = safe_path(ROOT, f['path'])
            if args.check:
                assert output.is_file() and sha(output) == f['sha256'], f'Missing or altered media: {output}'
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe_path(source, f['source_path']), output)
    for name, value in [('data/environment-media.json', merged), ('data/environment-media-sources.json', provenance)]:
        path = ROOT / name
        text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.check:
            assert path.read_text() == text, f'Out of sync: {path}'
        else:
            path.write_text(text)
    size = sum(f['bytes'] for m in entries for f in m['files'])
    print(f'PASS: {len(entries)} curated media records; {size:,} bytes; original bytes and evidence context verified.')


if __name__ == '__main__':
    main()

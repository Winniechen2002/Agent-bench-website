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
from media_overrides import load_overrides

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
    # Upstream checks above remain mandatory even for replaced/retired records.
    overlay = load_overrides(ROOT)
    overrides = {entry['id']: entry for entry in overlay['entries']}
    retired = set(overlay['removed_media_ids'])
    current = json.loads((ROOT / 'data/environment-media.json').read_text())
    previous_path = ROOT / 'data/environment-media-sources.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    # Public tombstones preserve the checked nonvideo identity after a current-only
    # preview leaves the runtime collection. Live records take precedence so a
    # later video under the same ID cannot bypass the retirement guard.
    known = {entry['id']: entry for entry in previous.get('retired_media', []) + current + entries}
    assert retired <= set(known), 'Unknown retired media ID'
    assert all(known[mid].get('media_kind') == 'image' for mid in retired), 'Only scene previews may be retired'
    retired_media = [{key: known[mid][key] for key in ('id', 'task', 'media_kind')} for mid in sorted(retired)]
    for entry in overrides.values():
        assert entry['task'] in ids and set(entry.get('case_ids', [])) <= ids[entry['task']], 'Invalid override task association'
        if entry['id'] in known:
            assert entry['task'] == known[entry['id']]['task'], 'Override changes native task association'
        for resource in entry['files']:
            output = safe_path(ROOT, resource['path'])
            assert output.is_file() and output.stat().st_size == resource['bytes'] and sha(output) == resource['sha256'], f'Missing or altered website derivative: {output}'
    final_entries = [overrides.get(entry['id'], public_media_entry(entry)) for entry in entries if entry['id'] not in retired]
    imported = {entry['id'] for entry in final_entries}
    final_entries.extend(entry for mid, entry in overrides.items() if mid not in imported)
    selected = {m['id'] for m in entries} | set(overrides) | retired
    merged = [m for m in current if m['id'] not in selected]
    merged.extend({k: v for k, v in entry.items() if k != 'files'} for entry in final_entries)
    provenance_context = dict(catalog)
    upstream_gaps = provenance_context.pop('gaps', [])
    provenance = public_media_catalog(dict(provenance_context, entries=final_entries, retired_media=retired_media,
        upstream_catalog_gaps=upstream_gaps,
        coverage_note='Upstream catalog gaps describe the original catalog before website overrides. Current website media coverage is described by entries. Reproductions and action replays retain their declared recording types and do not establish policy-executed rollout coverage.',
        website_derivative_ids=sorted(mid for mid, entry in overrides.items() if entry.get('media_kind') == 'video'),
        source_catalog=CATALOG, source_catalog_sha256=sha(source / CATALOG)))
    validate_document(merged, 'native media')
    # Check the entire output plan before writing; two IDs cannot silently own
    # different bytes at the same path (including a website derivative path).
    hashes = {}
    for entry in final_entries:
        for resource in entry['files']:
            assert hashes.setdefault(resource['path'], resource['sha256']) == resource['sha256'], 'Conflicting media output path'
    for entry in entries:
        if entry['id'] in overrides or entry['id'] in retired:
            continue
        for resource in entry['files']:
            output = safe_path(ROOT, resource['path'])
            if args.check:
                assert output.is_file() and sha(output) == resource['sha256'], f'Missing or altered media: {output}'
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(safe_path(source, resource['source_path']), output)
    for name, value in [('data/environment-media.json', merged), ('data/environment-media-sources.json', provenance)]:
        path = ROOT / name
        text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.check:
            assert path.read_text() == text, f'Out of sync: {path}'
        else:
            path.write_text(text)
    size = sum(f['bytes'] for m in final_entries for f in m['files'])
    print(f'PASS: {len(final_entries)} final media records; {size:,} bytes; original bytes and evidence context verified.')


if __name__ == '__main__':
    main()

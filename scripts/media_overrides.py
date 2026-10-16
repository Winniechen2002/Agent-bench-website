"""Website-owned public derivative metadata, applied after upstream verification.

The source-only configuration is deliberately excluded from the release allowlist.
Original artifact hashes belong in source_artifacts; files hashes describe only
bytes actually shipped at their public asset paths.
"""
import json
from pathlib import Path
import re

from build_site import clean_path
from public_data import strict_json, validate_document

EMPTY = dict(schema_version=1, entries=[], group_media={}, removed_media_ids=[])


def load_overrides(root):
    path = Path(root) / 'scripts/media-overrides.json'
    overlay = strict_json(path.read_text()) if path.exists() else dict(EMPTY)
    validate_document(overlay, 'website media overrides')
    assert overlay['schema_version'] == 1, 'Unsupported media overrides schema'
    assert set(overlay) == set(EMPTY), 'Unexpected media overrides field'
    entries = overlay['entries']
    assert len({entry['id'] for entry in entries}) == len(entries), 'Duplicate override ID'
    assert len(set(overlay['removed_media_ids'])) == len(overlay['removed_media_ids']), 'Duplicate retired ID'
    assert not ({entry['id'] for entry in entries} & set(overlay['removed_media_ids'])), 'Cannot override and retire the same ID'
    for entry in entries:
        assert 'source_path' not in entry, 'Overrides must use public artifact IDs'
        assert entry.get('files'), 'Override must declare derivative files'
        paths = set()
        for resource in entry['files']:
            assert 'source_path' not in resource, 'Derivative files must use public artifact IDs'
            path = clean_path(resource['path'])
            assert path.startswith('assets/'), 'Derivative must be under assets/'
            assert path not in paths, 'Duplicate derivative path'
            paths.add(path)
            assert isinstance(resource['bytes'], int) and resource['bytes'] > 0, 'Invalid derivative size'
            assert re.fullmatch('[0-9a-f]{64}', resource['sha256']), 'Invalid derivative hash'
        for field in ('path', 'poster', 'fallback'):
            value = entry.get(field)
            assert not value or value == 'image' or value in paths, f'Undeclared override {field}'
    for family, media_ids in overlay['group_media'].items():
        assert isinstance(family, str) and isinstance(media_ids, list) and media_ids, 'Invalid group media override'
        assert len(media_ids) == len(set(media_ids)), 'Duplicate group media ID'
    return overlay


def apply_group_overrides(media_by_family, overlay):
    retired = set(overlay['removed_media_ids'])
    result = {family: list(dict.fromkeys(mid for mid in mids if mid not in retired))
              for family, mids in media_by_family.items()}
    result.update(overlay['group_media'])
    assert not any(retired & set(mids) for mids in result.values()), 'Retired media remains associated'
    return result

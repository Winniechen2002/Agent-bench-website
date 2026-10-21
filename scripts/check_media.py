"""Validate visible video coverage, sizes and playback metadata.

The portable content/build checks validate declared durations. Run the explicit
`npm run check:media` command for actual container durations (requires ffprobe).
"""
import argparse
import json
import hashlib
import math
from pathlib import Path
import re
import shutil
import subprocess

from build_site import source_file

ROOT = Path(__file__).resolve().parents[1]
HERO_PROMO_ID = 'embodied-playground-film'
HERO_PROMO_LIMIT = 192.25


def read(root, name):
    return json.loads((root / 'data' / name).read_text())


def check_manifest_resources(root):
    """Audit shipped derivatives, independently of original source artifacts.

    Legacy artifact IDs are permitted. Where an artifact ID or media_ids resolves
    to current media, its declared web videos must be those canonical paths.
    """
    root = Path(root).resolve()
    manifest = json.loads(source_file(root, 'evidence/demo-manifest.json').read_text())
    canonical = {}
    for name in ('media.json', 'environment-media.json'):
        for entry in read(root, name):
            if entry.get('media_kind') == 'video':
                canonical.setdefault(entry['id'], set()).add(entry['path'])
    resource_count = 0
    for artifact in manifest['artifacts']:
        resources = list(artifact.get('web_files', []))
        if artifact.get('web_asset'):
            resources.append(artifact['web_asset'])
        videos = set()
        while resources:
            resource = resources.pop()
            relative = resource['path']
            assert relative.startswith('assets/'), 'Manifest web resource must be under assets/'
            path = source_file(root, relative)
            sizes = [resource[field] for field in ('bytes', 'size_bytes') if field in resource]
            assert sizes and all(size == path.stat().st_size for size in sizes), f'Manifest web resource size mismatch: {relative}'
            assert hashlib.sha256(path.read_bytes()).hexdigest() == resource['sha256'], f'Manifest web resource hash mismatch: {relative}'
            resource_count += 1
            if path.suffix.lower() in {'.mp4', '.webm', '.mov', '.m4v'}:
                videos.add(relative)
            if resource.get('poster'):
                resources.append(resource['poster'])
        related_ids = {artifact['id'], *artifact.get('media_ids', [])} & canonical.keys()
        if related_ids:
            expected = set().union(*(canonical[mid] for mid in related_ids))
            assert videos == expected, f'Manifest web video differs from canonical media: {artifact["id"]}'
    return resource_count


def validate_media(root, *, probe=False):
    root = Path(root).resolve()
    asset_bytes = sum(path.stat().st_size for path in (root / 'assets').rglob('*') if path.is_file())
    assert asset_bytes <= 100_000_000, 'Media exceeds 100 MB asset budget'
    all_videos, visible_videos = {}, set()
    over_target, promo_paths = set(), set()
    for collection, associations in (('media.json', 'tasks.json'), ('environment-media.json', 'environment-groups.json')):
        entries = read(root, collection)
        lookup = {item['id']: item for item in entries}
        visible = {mid for card in read(root, associations) for mid in card['media']}
        visible.update(item['id'] for item in entries if item.get('showcase'))
        assert visible <= set(lookup), 'Unresolved visible media association'
        for entry in entries:
            if entry.get('media_usage') == 'hero-promo' or entry['id'] == HERO_PROMO_ID:
                assert collection == 'media.json' and entry['id'] == HERO_PROMO_ID and entry.get('media_usage') == 'hero-promo', 'Only the selected homepage film may use the hero exception'
                assert entry.get('media_kind') == 'video' and entry.get('showcase') is False and entry['id'] not in visible, 'The hero film must remain outside task and showcase media'
                duration = entry.get('duration_seconds')
                assert isinstance(duration, (float, int)) and math.isfinite(duration) and 0 < duration <= HERO_PROMO_LIMIT, f'Invalid hero film duration ({HERO_PROMO_LIMIT}-second limit)'
                assert entry.get('playback_speed') == 1, 'The hero film must preserve original playback timing'
                promo_paths.add(entry['path'])
        for mid in visible:
            entry = lookup[mid]
            assert entry.get('media_kind') == 'video', f'Visible media must be video: {mid}'
            duration = entry.get('duration_seconds')
            assert isinstance(duration, (float, int)) and math.isfinite(duration) and 0 < duration <= 120, f'Invalid video duration (hard limit 120 seconds): {mid}'
            speed = entry.get('playback_speed', 1)
            assert isinstance(speed, (float, int)) and math.isfinite(speed) and speed > 0, f'Invalid playback speed: {mid}'
            labels = [float(value) for value in re.findall(r'(?<![\d.])(\d+(?:\.\d+)?)\s*[×x](?!\d)', ' '.join(entry.get(field, '') for field in ('caption', 'title', 'playback_label')))]
            assert all(abs(value - speed) < 0.001 for value in labels), f'Playback speed label differs from metadata: {mid}'
            assert speed == 1 or labels, f'Accelerated playback needs a speed label: {mid}'
            if duration > 60:
                over_target.add(entry['path'])
            visible_videos.add(entry['path'])
        for entry in entries:
            if entry.get('media_kind') == 'video':
                all_videos.setdefault(entry['path'], []).append(entry)
    # Public provenance names the same website derivative subset in both the
    # source tree and staged release; source-only config never changes policy.
    provenance = read(root, 'environment-media-sources.json')
    derivative_ids = provenance.get('website_derivative_ids', [])
    lookup = {entry['id']: entry for entry in provenance['entries']}
    assert len(set(derivative_ids)) == len(derivative_ids) and set(derivative_ids) <= set(lookup), 'Invalid website derivative subset'
    for mid in derivative_ids:
        entry = lookup[mid]
        assert entry.get('media_kind') == 'video', 'Website derivative size subset must contain videos'
        assert (root / entry['path']).stat().st_size < 5_000_000, f'New video must be below 5 MB: {entry["id"]}'
    if probe:
        ffprobe = shutil.which('ffprobe')
        assert ffprobe, 'ffprobe is required for check:media; install FFmpeg or run portable npm run check'
        for path, entries in all_videos.items():
            result = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'json', str(root / path)], check=True, capture_output=True, text=True)
            actual = float(json.loads(result.stdout)['format']['duration'])
            limit = HERO_PROMO_LIMIT if all(entry.get('media_usage') == 'hero-promo' and entry['id'] == HERO_PROMO_ID for entry in entries) else 120
            assert math.isfinite(actual) and 0 < actual <= limit, f'Actual video duration exceeds {limit} seconds: {path}'
            if actual > 60 and path not in promo_paths:
                over_target.add(path)
            for entry in entries:
                if entry.get('duration_seconds') is not None:
                    assert abs(actual - entry['duration_seconds']) <= 0.25, f'Declared duration differs from video: {entry["id"]}'
    check_manifest_resources(root)
    return dict(asset_bytes=asset_bytes, videos=len(all_videos), hero_promos=len(promo_paths), visible_videos=len(visible_videos), over_target=sorted(over_target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--probe', action='store_true')
    args = parser.parse_args()
    result = validate_media(args.root, probe=args.probe)
    print(f'PASS: {result["visible_videos"]} visible videos; {result["videos"]} unique video files; {result["asset_bytes"] / 1e6:.2f} MB assets; rollouts ≤120 seconds; {result["hero_promos"]} selected hero film(s) ≤{HERO_PROMO_LIMIT} seconds.')
    if result['over_target']:
        print('Above preferred 60-second target: ' + ', '.join(result['over_target']))


if __name__ == '__main__':
    main()

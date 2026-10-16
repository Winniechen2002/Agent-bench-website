"""Check standalone site data and local references. No network or repository operations."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
ROOT = parser.parse_args().root.resolve()

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            assert attrs['id'] not in self.ids, 'Duplicate HTML ID: ' + attrs['id']
            self.ids.add(attrs['id'])
        for field in ('href', 'src', 'poster'):
            if attrs.get(field):
                self.links.append(attrs[field])

page = Page()
page.feed((ROOT / 'index.html').read_text())
for url in page.links:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        continue
    if not parts.path:
        assert not parts.fragment or parts.fragment in page.ids, 'Missing anchor: ' + url
    else:
        assert not parts.path.startswith('/'), 'Non-relative resource: ' + url
        assert (ROOT / unquote(parts.path)).is_file(), 'Missing resource: ' + url

# Validate shipped data only; local archives and dependency caches are not inputs.
json_paths = [ROOT / 'package.json'] if (ROOT / 'package.json').is_file() else []
for directory in ('data', 'evidence'):
    json_paths.extend((ROOT / directory).rglob('*.json'))
for path in json_paths:
    json.loads(path.read_text())
media = json.loads((ROOT / 'data/media.json').read_text())
ids = {item['id'] for item in media}
assert len(ids) == len(media), 'Duplicate media ID'
for item in media:
    for field in ('path', 'poster', 'fallback'):
        if item.get(field):
            assert item[field].startswith('assets/'), f'Runtime path outside assets: {item[field]}'
            assert (ROOT / item[field]).is_file(), f'Missing {field}: {item[field]}'
for task in json.loads((ROOT / 'data/tasks.json').read_text()):
    assert all(mid in ids for mid in task['media']), 'Unresolved media for ' + task['id']
asset_bytes = sum(path.stat().st_size for path in (ROOT / 'assets').rglob('*') if path.is_file())
assert asset_bytes <= 100_000_000, 'Media exceeds 100 MB budget'
print(f'PASS: JSON, unique IDs, anchors, local links, media associations; {len(media)} media entries, {asset_bytes / 1e6:.2f} MB assets.')

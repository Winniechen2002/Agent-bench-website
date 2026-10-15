"""Validate the actual static website and its portable environment snapshot."""
from html.parser import HTMLParser
import json
import hashlib
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path, self.ids, self.links = path, [], []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('href', 'src', 'poster'):
            if attrs.get(key):
                self.links.append(attrs[key])


def read(name):
    return json.loads((ROOT / 'data' / name).read_text())


def local_link(link, base=ROOT):
    url = urlsplit(link)
    if url.scheme or url.netloc:
        return
    path = base / unquote(url.path)
    assert path.is_file(), f'Missing local resource: {link}'
    if url.fragment and path.suffix == '.html':
        assert unquote(url.fragment) in Page(path).ids, f'Broken anchor: {link}'


for name in ('index.html', 'report.html'):
    page = Page(ROOT / name)
    assert len(page.ids) == len(set(page.ids)), f'Duplicate IDs: {name}'
    for link in page.links:
        if link.startswith('#'):
            assert link[1:] in page.ids, f'Broken anchor: {name}{link}'
        else:
            local_link(link, page.path.parent)

cards, meta, inventory, media = (read(n) for n in ('tasks.json', 'benchmark.json', 'environment-catalog.json', 'media.json'))
ids = [t['id'] for t in inventory]
assert len(ids) == len(set(ids)) == meta['task_count'] == 410
assert sum(t['count'] for t in cards) == meta['task_count']
assert sorted(i for t in cards for i in t['task_ids']) == sorted(ids)
assert meta['group_count'] == sum(len(t['groups']) for t in inventory) == 510
assert meta['planned_episodes'] == meta['group_count'] * meta['trials_per_group'] == 2040
assert meta['protocol_version'] == 'environment-four-trial-v2'
assert meta['capability_version'] == '2026-10-09-environment-l0-l3'
assert meta['qualification'] == 'not_established' and meta['release_ready'] is False
assert read('results.json')['results'] == read('results.json')['summary'] == []
assert all(t['status'] == 'qualification-pending' for t in cards)
assert len({m['id'] for m in media}) == len(media)
media_ids = {m['id'] for m in media}
assert all(t['media'] for t in cards), 'Every catalog group needs a media entry'
assert all(m in media_ids for t in cards for m in t['media'])
assert all(next(m for m in media if m['id'] == media_id)['task'] == t['id'] for t in cards for media_id in t['media'])
assert all(m['task'] in {t['id'] for t in cards} for m in media)
for m in media:
    for key in ('path', 'poster', 'fallback'):
        if m.get(key) and m[key] != 'image':
            local_link(m[key])
    if m.get('media_kind') == 'video':
        assert m['claim_status'].startswith('historical-')
        assert 'Not evaluated under environment-four-trial-v2.' in m['caption']
provenance = read('media-sources.json')
for entry in provenance['entries']:
    live = next(m for m in media if m['id'] == entry['id'])
    assert live == {k: v for k, v in entry.items() if k != 'files'}, f"Media metadata drift: {entry['id']}"
    for resource in entry['files']:
        path = ROOT / resource['path']
        assert path.stat().st_size == resource['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == resource['sha256'], f"Altered source media: {path}"
    assert set(entry['case_ids']) <= set(ids)
assert all(len(m['case_ids']) == 10 for m in media if m.get('display') == 'contact-sheet')
assert next(m for m in media if m['id'] == 'bookshelf-native-preview')['claim_status'] == 'environment-preview'

for task in inventory:
    assert task['budgets']['max_steps'] == round(task['budgets']['simulation_seconds'] * task['budgets']['control_hz'])

html = (ROOT / 'index.html').read_text()
js = (ROOT / 'site.js').read_text()
assert 'fallbackData' not in js, 'Do not resurrect stale scores when a fetch fails'
assert 'data/results.json' not in js
assert 'L4' not in html and 'Opus 5.5' not in html
assert all(f'data-filter="{family}"' in html for family in {t['family'] for t in cards})
for path in re.findall(r'loadJSON\("([^\"]+)"\)', js):
    local_link(path)
assert '"output": "index.html"' not in (ROOT / 'scripts/build_framework.py').read_text()
print('PASS: pages, links, media, 410 unique tasks, 510 groups, 2040 planned episodes, budgets, media provenance and 12/12 group preview coverage.')

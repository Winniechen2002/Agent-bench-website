"""Validate the paper website and its separate portable native environment snapshot."""
from html.parser import HTMLParser
import json
from collections import Counter
import hashlib
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
ROOT = parser.parse_args().root.resolve()


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


for name in ('index.html', 'environment.html'):
    page = Page(ROOT / name)
    assert len(page.ids) == len(set(page.ids)), f'Duplicate IDs: {name}'
    for link in page.links:
        if link.startswith('#'):
            assert link[1:] in page.ids, f'Broken anchor: {name}{link}'
        else:
            local_link(link, page.path.parent)

cards, meta, inventory, media = (read(n) for n in ('environment-groups.json', 'benchmark.json', 'environment-catalog.json', 'environment-media.json'))
ids = [t['id'] for t in inventory]
assert len(ids) == len(set(ids)) == meta['task_count'] == 410
assert sum(t['count'] for t in cards) == meta['task_count']
assert sorted(i for t in cards for i in t['task_ids']) == sorted(ids)
assert meta['group_count'] == sum(len(t['groups']) for t in inventory) == 510
assert meta['planned_episodes'] == meta['group_count'] * meta['trials_per_group'] == 2040
assert meta['protocol_version'] == 'environment-four-trial-v2'
assert meta['capability_version'] == '2026-10-09-environment-l0-l3'
assert meta['qualification'] == 'not_established' and meta['release_ready'] is False
assert read('environment-results.json')['results'] == read('environment-results.json')['summary'] == []
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
provenance = read('environment-media-sources.json')
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

html = (ROOT / 'environment.html').read_text()
js = (ROOT / 'environment.js').read_text()
assert 'fallbackData' not in js, 'Do not resurrect stale scores when a fetch fails'
assert 'data/results.json' not in js
assert 'L4' not in html and 'Opus 5.5' not in html
assert all(f'data-filter="{family}"' in html for family in {t['family'] for t in cards})
# Validate both entry points' active JSON dependencies.
for script in ('environment.js', 'site.js'):
    source = (ROOT / script).read_text()
    assert 'fallbackData' not in source, 'Do not resurrect stale scores when a fetch fails'
    for path in re.findall(r"loadJSON\(['\"]([^'\"]+)['\"]\)", source):
        local_link(path)
assert 'data/environment-groups.json' in js and 'data/environment-media.json' in js
assert 'index.html#tasks' in html and 'loaded and ground' in html
assert 'href="site.css"' in html, 'Directory must share the primary theme'
assert 'id="hero-video"' not in html and 'id="results"' not in html and 'id="protocol"' not in html
assert 'data/environment-catalog.json' in js
assert len(cards) == 12
assert all(set(task['groups']) == {'loaded', 'ground'} for task in inventory if task['family'] == 'marble')

# Paper-indexed types and audited results are deliberately not native sync outputs.
paper_cards, paper_media, paper_index, results = (read(name) for name in (
    'tasks.json', 'media.json', 'ep100-index.json', 'results.json'))
assert len(paper_cards) == 16
assert len({card['id'] for card in paper_cards}) == 16
assert sum(card['task_count'] for card in paper_cards) == 100
paper_rows = paper_index['task_results']
assert len(paper_rows) == len({row['task_id'] for row in paper_rows}) == 100
assert len({row['index'] for row in paper_rows}) == 100
paper_task_ids = [task_id for card in paper_cards for task_id in card['task_ids']]
assert sorted(paper_task_ids) == sorted(row['task_id'] for row in paper_rows)
assert set(paper_task_ids) <= set(ids), 'Paper tasks must exist in the full native catalog'
expected_suites = {'Launch': 34, 'Tower': 21, 'Lock': 16, 'Cube': 12, 'Home': 17}
assert Counter(row['suite'] for row in paper_rows) == paper_index['suite_counts'] == expected_suites
assert Counter(row['split'] for row in paper_rows) == paper_index['split_counts'] == {'Easy': 50, 'Hard': 50}
assert sum(bool(row['ep20']) for row in paper_rows) == paper_index['ep20_count'] == 20
for card in paper_cards:
    assert card['task_count'] == len(card['task_ids'])
    matching = [row for row in paper_rows if row['task_id'] in card['task_ids']]
    assert all(row['suite'] == card['suite'] and row['type'] == card['type'] for row in matching)
    assert card['ep20_count'] == sum(bool(row['ep20']) for row in matching)
    assert card['split_counts'] == Counter(row['split'] for row in matching)
    assert card['counts_by_embodiment'] == Counter(row['embodiment'] for row in matching)
    assert card['access_levels'] == ['L0', 'L1', 'L2', 'L3'] and 'observation_profiles' not in card
    native_docs = {group['source'] for group in cards if set(group['task_ids']) & set(card['task_ids'])}
    assert {entry['path'] for entry in card['documentation']} == native_docs
paper_media_ids = {item['id'] for item in paper_media}
assert len(paper_media_ids) == len(paper_media)
assert all(card['media'] for card in paper_cards)
assert all(media_id in paper_media_ids for card in paper_cards for media_id in card['media'])
for item in paper_media:
    for key in ('path', 'poster', 'fallback'):
        if item.get(key) and item[key] != 'image':
            local_link(item[key])
# Keep the collaborator's primary presentation reachable during future content refreshes.
primary = (ROOT / 'index.html').read_text()
primary_js = (ROOT / 'site.js').read_text()
assert 'legacy-results' not in primary and 'legacy-opus.json' not in primary_js
assert 'ex.source.filename' not in primary_js and 'ex.source.sha256' not in primary_js
assert 'SHA-256' not in primary and 'Earlier exploratory evaluations' not in primary
assert 'aria-current' in primary_js and 'full-catalog-entry' in primary
assert 'assets/posters/marble-a099-initial.png' in primary
assert "mediaById('marble-a099-historical')" in primary_js
assert {'marble-a099-historical', 'marble-a057-historical', 'hanoi-floating-h29-scene'} <= paper_media_ids
assert all(next(item for item in paper_media if item['id'] == key)['showcase'] for key in (
    'marble-a099-historical', 'marble-a057-historical', 'hanoi-floating-h29-scene'))
assert 'docs/evaluation_protocol.en.md' in primary and 'data/benchmark.json' in primary
primary_lookup = {item['id']: item for item in paper_media}
for native in media:
    if native['id'] in primary_lookup:
        assert native['path'] == primary_lookup[native['id']]['path'], f"Conflicting canonical media: {native['id']}"
experiment_ids = [experiment['id'] for experiment in results['experiments']]
assert len(experiment_ids) == len(set(experiment_ids))
assert results['default_experiment'] in experiment_ids
experiment = next(item for item in results['experiments'] if item['id'] == results['default_experiment'])
assert experiment['model'] == 'gpt-6-astra' and experiment['access_level'] == 'L3'
assert experiment['source'] == paper_index['source']
assert experiment['protocol']['launcher_mode'] == 'loaded-only'
assert experiment['protocol']['conditions_per_task'] == 4
local_link(experiment['task_results_file'])
assert experiment['task_results_file'] == 'data/ep100-index.json'
for subset, subset_rows in (('EP-100', paper_rows), ('EP-20', [row for row in paper_rows if row['ep20']])):
    summary = experiment['subsets'][subset]
    assert summary['tasks'] == len(subset_rows)
    assert summary['conditions'] == len(subset_rows) * 4
    for suite, suite_summary in summary['suites'].items():
        rows = [row for row in subset_rows if row['suite'] == suite]
        assert suite_summary['tasks'] == len(rows)
        for metric in ('pass_at_1', 'pass_at_2'):
            assert abs(suite_summary[metric] - sum(row[metric] for row in rows) / len(rows)) < 1e-12
assert 'legacy' not in results, 'Unfinished exploratory results belong in local archives, not published data'
print('PASS: paper/native pages and links; 410 unique native tasks, 12 groups, 510 evaluation groups, 2040 planned episodes; budgets, native media provenance and 12/12 preview coverage; 16 paper types, EP-100/EP-20 membership, splits, media and audited result consistency.')

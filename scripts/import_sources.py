"""Refresh the HISTORICAL 200-task atlas snapshot (not the current website catalog) from an Agent-bench checkout.

For the active 410-task site use sync_benchmark.py instead.

Usage: python3 scripts/import_sources.py ../Agent-bench
Requires Pillow. Never modifies the source checkout.
"""
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parent / 'Agent-bench'
ATLAS = SOURCE / 'docs/task_atlas_200'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


en = read(ATLAS / 'task_index.en.json')
zh = {t['id']: t for t in read(ATLAS / 'task_index.zh-CN.json')}
status = read(SOURCE / 'docs/task_status_index.json')
statuses = {t['id']: t for t in status['rows']}
catalog, media = [], []
for t in en:
    target = ROOT / 'assets/tasks' / (t['id'] + '.webp')
    target.parent.mkdir(parents=True, exist_ok=True)
    original = ATLAS / t['image']
    with Image.open(original) as im:
        im = im.convert('RGB')
        im.thumbnail((900, 720))
        im.save(target, 'WEBP', quality=82, method=6)
        size = list(im.size)
    s = statuses[t['id']]
    catalog.append({
        'id': t['id'], 'group': t['group'], 'image': str(target.relative_to(ROOT)),
        'width': size[0], 'height': size[1], 'completed': s['completed'],
        'en': {'title': t['title'], 'subtitle': t['subtitle'], 'lines': t['lines'], 'status': s['note_en']},
        'zh': {'title': zh[t['id']]['title'], 'subtitle': zh[t['id']]['subtitle'], 'lines': zh[t['id']]['lines'], 'status': s['note_zh']},
    })
    media.append({'id': t['id'], 'source': str(original.relative_to(SOURCE)),
                  'source_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
                  'output': str(target.relative_to(ROOT)),
                  'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                  'transform': 'Aspect-preserving resize and WebP encoding; no generative edits.'})

assert len(catalog) == 200
assert len({t['id'] for t in catalog}) == 200
counts = dict(Counter(t['group'] for t in catalog))
completed = sum(t['completed'] for t in catalog)
assert counts == {'cube': 20, 'birds': 100, 'panda': 40, 'hand': 40}
assert completed == 82
write(ROOT / 'data/catalog.json', catalog)
write(ROOT / 'data/evidence.json', {
    'snapshot_date': '2026-10-09', 'inventory_reviewed_at': status['reviewed_at'],
    'inventory_source_commit': status['source_commit'], 'core_tasks': len(catalog),
    'groups': counts, 'historical_completed': completed,
    'historical_completed_by_group': dict(Counter(t['group'] for t in catalog if t['completed'])),
    'scope': 'Historical engineering/reference execution at recorded configurations, not a model success rate or a four-trial-v1 score.',
    'image_scope': 'Native simulation scene illustrations. Visual backgrounds are presentation context, not rollout evidence.',
    'extensions': {'kongming_reference_successes': ['assemble', 'disassemble'],
                   'single_panda_cube_public_cases': 30, 'public_case_acceptance_scope': 'reset only'},
})
sources = ['README.md', 'rules.md', 'Vision_rules.md', 'report.en.md',
           'docs/task_atlas_200/task_index.en.json', 'docs/task_atlas_200/task_index.zh-CN.json',
           'docs/task_status_index.json', 'docs/task_status.en.md',
           'docs/benchmark-platform.md', 'docs/benchmark-platform-evidence.md',
           'docs/rubiks-benchmark-platform.md', 'docs/rubiks_cube_milestone_v0.1.md',
           'docs/rubiks_platform_native_acceptance.json',
           'env/franka_marble/ENVIRONMENT_CATALOG.md', 'env/franka_marble/TEST_PROTOCOL.en.md']
records = []
for p in sources:
    raw = (SOURCE / p).read_bytes()
    tracked = subprocess.run(['git', '-C', str(SOURCE), 'show', 'HEAD:' + p], capture_output=True)
    records.append({'path': p, 'sha256': hashlib.sha256(raw).hexdigest(),
                    'matches_head': tracked.returncode == 0 and tracked.stdout == raw})
write(ROOT / 'data/source-manifest.json', {
    'captured_on': '2026-10-09',
    'repository': 'https://github.com/Winniechen2002/Agent-bench',
    'checkout_head': subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip(),
    'note': 'Working-tree snapshot includes local atlas/status edits. HEAD alone does not identify those bytes. Historical evidence retains its own source versions.',
    'sources': records, 'media': media,
})
print(f'Imported {len(catalog)} tasks; {completed} historical passes; groups {counts}.')

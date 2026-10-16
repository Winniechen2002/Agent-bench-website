"""Sync public environment metadata, without simulator imports or paper model results.

Native outputs are namespaced so syncing never overwrites the paper task types
or audited EP-100 results.

python3 scripts/sync_benchmark.py ../Agent-bench [--check]
The checked-in evaluation export is the source of task IDs, budgets and counts.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
from public_data import validate_document
from media_overrides import load_overrides, apply_group_overrides

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    'marble': ('Launch · Dual Franka Panda', 'marble', 'Physics & recovery', '100 authored scenes with finite ammunition, protected targets and scene-specific physical objectives. Loaded and ground modes are separate evaluation groups.', ['physics', 'planning', 'recovery']),
    'hanoi_panda': ('Hanoi · Franka Panda', 'hanoi', 'Strategic planning', '40 authored start/goal configurations. Legal moves, seating checks and one second of stable completion.', ['planning', 'rules', 'contact']),
    'hanoi_sharpa': ('Hanoi · Franka FR3 + Sharpa', 'hanoi', 'Dexterous planning', 'The 40-case Hanoi suite with an arm-mounted Sharpa hand.', ['planning', 'dexterity', 'contact']),
    'hanoi_floating': ('Hanoi · Floating Sharpa', 'hanoi', 'Dexterous planning', 'The 40-case Hanoi suite with a floating Sharpa hand.', ['planning', 'dexterity', 'state_tracking']),
    'pocket_cube': ('2×2 Pocket Cube', 'cube', 'Bimanual state tracking', '10 authored cases per embodiment, 20 entries total. Exact target state and committed quarter-turn count are scored.', ['state_tracking', 'bimanual', 'contact']),
    'rubiks_panda': ("Rubik's Cube · Franka Panda", 'cube', 'Spatial reasoning', '30 fixed public cases using the declared hybrid_fixture_v1 auxiliary mechanism, with legal release and return rules.', ['state_tracking', 'dexterity', 'spatial']),
    'rubiks_sharpa': ("Rubik's Cube · Floating Sharpa", 'cube', 'Spatial reasoning', '30 fixed public cases using hybrid_fixture_v1. Four lighting conditions preserve the authored scramble and physical layout.', ['state_tracking', 'dexterity', 'spatial']),
    'kongming_lock': ('Kongming Lock', 'kongming', 'Assembly & disassembly', '30 assembly/disassembly cases per embodiment, 60 entries total. Case-specific goals, release and continuous physical audits determine success.', ['bimanual', 'contact', 'recovery']),
    'bookshelf': ('Bookshelf Organization', 'bookshelf', 'Constrained placement', '20 dual-Panda variants with native layout sampling. Object destinations, support, wall constraints and stable placement are task-specific.', ['perception', 'planning', 'placement']),
    'maniskill_long_horizon': ('Home · Long', 'maniskill', 'Sequential manipulation', '10 tasks with fixed authored layouts, native robot controllers and a 300-second simulation budget. L1–L10 are task codes, not permission levels.', ['planning', 'memory', 'control']),
    'maniskill_geometry': ('Home · Precise', 'maniskill', 'Spatial reasoning', '10 geometry tasks with fixed layouts, four lighting factors and a 120-second simulation budget.', ['geometry', 'placement', 'control']),
    'maniskill_dynamics': ('Home · Dynamic', 'maniskill', 'Physical reasoning', '10 dynamics tasks. Formal trials use physics_variant=0; additional physics variants are engineering checks. Task deadlines remain separate from the episode budget.', ['physics', 'timing', 'control']),
}
ROBOTS = {'dual-panda': 'Dual Franka Panda', 'panda': 'Franka Panda', 'fr3-sharpa': 'Franka FR3 + Sharpa', 'floating-sharpa': 'Floating Sharpa', 'aloha': 'Dual ALOHA', 'dual-sharpa': 'Dual Floating Sharpa', 'dual-floating-sharpa': 'Dual Floating Sharpa', 'fetch': 'Fetch', **{f'everyday_robot_0{i}': f'Everyday Robot 0{i}' for i in (1, 3, 9)}}
MEDIA = {
    'hanoi_panda': ['hanoi-franka-preview', 'hanoi-4090-demo'],
    'hanoi_sharpa': ['hanoi-sharpa-preview'],
    'pocket_cube': ['pocket-cube-dual-aloha-preview', 'pocket-cube-dual-sharpa-preview'],
    'rubiks_panda': ['rubiks-franka-three-step', 'rubiks-franka-reference-cycle'],
    'rubiks_sharpa': ['rubiks-floating-sharpa-preview'],
    'kongming_lock': ['kongming-dual-franka-reference', 'kongming-floating-sharpa-a06-reference', 'kongming-floating-sharpa-d06-reference', 'kongming-dual-franka-disassemble-reference'],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assignment(path, name):
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f'Missing {name} in {path}')


def snapshot(source):
    protocol_path = 'docs/evaluation/tasks.json'
    protocol = json.loads((source / protocol_path).read_text())
    # Reject an outdated source export rather than publishing a mixed snapshot.
    for name, expected in protocol['sources'].items():
        if digest(source / name) != expected:
            raise ValueError(f'Stale evaluation export: {name}; run scripts/export_evaluation_protocol.py in Agent-bench first.')
    counts = Counter(t['task_id'].split('/')[0] for t in protocol['tasks'])
    catalog_source = 'source/agentbench_platform/agentbench_platform/environment_catalog.py'
    assert counts == assignment(source / catalog_source, 'EXPECTED')
    assert set(counts) == set(FAMILIES), 'Update website descriptions for new families'
    assert protocol['task_count'] == len(protocol['tasks']) == len({t['task_id'] for t in protocol['tasks']})
    assert protocol['group_count'] == sum(len(t['groups']) for t in protocol['tasks'])
    assert protocol['planned_episodes'] == sum(len(g['trials']) for t in protocol['tasks'] for g in t['groups'])
    assert all(len(g['trials']) == 4 for t in protocol['tasks'] for g in t['groups'])
    media_catalog_path = 'docs/website_media_catalog.json'
    media_catalog = json.loads((source / media_catalog_path).read_text())
    media_by_family = {family: list(items) for family, items in MEDIA.items()}
    for entry in media_catalog['entries']:
        assert entry['task'] in FAMILIES
        media_by_family.setdefault(entry['task'], []).append(entry['id'])
    overlay = load_overrides(ROOT)
    assert set(overlay['group_media']) <= set(FAMILIES), 'Unknown group media family'
    current_media = json.loads((ROOT / 'data/environment-media.json').read_text())
    known_media = {entry['id']: entry for entry in current_media + media_catalog['entries'] + overlay['entries']}
    for family, media_ids in overlay['group_media'].items():
        assert all(mid in known_media and known_media[mid]['task'] == family for mid in media_ids), 'Invalid group media association'
    media_by_family = apply_group_overrides(media_by_family, overlay)
    cards = []
    for family, (title, category, label, summary, skills) in FAMILIES.items():
        rows = [t for t in protocol['tasks'] if t['task_id'].split('/')[0] == family]
        cards.append(dict(id=family, title=title, family=category, family_label=label,
            count=len(rows), counts_by_embodiment=dict(Counter(ROBOTS[t['task_id'].split('/')[1]] for t in rows)), embodiments=[ROBOTS[r] for r in sorted({t['task_id'].split('/')[1] for t in rows})],
            status='qualification-pending', summary=summary, skills=skills,
            source=f'docs/evaluation/{family}.en.md', media=media_by_family.get(family, []),
            task_ids=[t['task_id'] for t in rows]))
    profile_source = 'source/agentbench_platform/agentbench_platform/profiles.py'
    tracked = set(protocol['sources']) | {protocol_path, catalog_source, profile_source, media_catalog_path,
        'README.en.md', 'docs/evaluation_protocol.en.md', 'env/runtime/release-scope-decision.json',
        'env/runtime/license-decisions.json', 'LICENSING.md'}
    for card in cards:
        assert (source / card['source']).is_file()
        tracked.add(card['source'])
    metadata = dict(schema_version='website-environments-v1', repository='https://github.com/Winniechen2002/Embodied-Playgroud',
        source_scope='Local working tree, including uncommitted source changes.',
        protocol_version=protocol['version'], capability_version=assignment(source / profile_source, 'CAPABILITY_VERSION'),
        base_seed=protocol['base_seed'], task_count=protocol['task_count'], counts=dict(counts),
        group_count=protocol['group_count'], planned_episodes=protocol['planned_episodes'], trials_per_group=4,
        qualification=json.loads((source / 'env/runtime/release-scope-decision.json').read_text())['full_environment_qualification'],
        release_ready=json.loads((source / 'env/runtime/license-decisions.json').read_text())['source_release_ready'],
        sources={name: digest(source / name) for name in sorted(tracked)})
    # Public inventory intentionally excludes hidden states, trial layouts and scorer internals.
    inventory = [dict(id=t['task_id'], family=t['task_id'].split('/')[0],
        embodiment=t['task_id'].split('/')[1], configuration_sha256=t['configuration_sha256'],
        budgets=t['budgets'], groups=[g['variant'] for g in t['groups']]) for t in protocol['tasks']]
    return {'environment-groups.json': cards, 'benchmark.json': metadata, 'environment-catalog.json': inventory,
        'environment-results.json': dict(schema_version='2.0', protocol=protocol['version'], results=[], summary=[],
            source_note='The current environment source scope publishes no model results. Historical website scores are archived separately and do not establish performance under this protocol.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path, default=ROOT.parent / 'Agent-bench')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = snapshot(args.source.resolve())
    for name, value in outputs.items():
        validate_document(value, name)
    for name, value in outputs.items():
        path = ROOT / 'data' / name
        content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f'Out of sync: {path}; run npm run sync')
        else:
            path.write_text(content)
    print('PASS: website snapshot matches the Agent-bench working tree (410 tasks, 510 groups, 2040 planned episodes).')


if __name__ == '__main__':
    main()

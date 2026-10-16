#!/usr/bin/env python3
"""Refresh public website data from the paper snapshot without repository operations.

Usage: python3 scripts/refresh-paper-data.py PAPER_DIRECTORY [--check]
Local archives are neither required nor modified.
Only the three generated JSON files are written. --check compares without writing.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
from public_data import validate_document


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paper', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    site = Path(__file__).resolve().parents[1]
    paper = args.paper
    source_path = paper / 'data/codex_experiments.json'
    data = json.loads(source_path.read_text())
    index_path = paper / 'appendices/ep100_index.tex'
    metadata = {
        'filename': 'data/codex_experiments.json',
        'revision': data['subset_revision'],
        'sha256': sha(source_path),
        'environment_revision': 'a58a288',
        'selection': 'agentbench-curated-v2; index version 1.4; paper-loaded-only-v1',
        'report_audit_created_at': data['provenance']['report_audit_created_at'],
        'publication_verified_at': data['provenance']['publication_verified_at'],
        'supporting_sources': [
            {'filename': name, 'sha256': sha(paper / name)}
            for name in ['appendices/ep100_index.tex', 'sections/ep100.tex',
                         'sections/evaluation_protocol.tex', 'sections/experiments.tex']
        ],
        'upstream_audit_sources': [
            {'filename': Path(name).name, 'sha256': value}
            for name, value in data['provenance']['sources_sha256'].items()
        ],
    }
    pattern = re.compile(r'^(\w+-\d+) & (\w+) & (.*?) & (Easy|Hard) & (.*?) & \\nolinkurl\{([^}]+)\}', re.M)
    paper_rows = {}
    for index, task_type, title, split, ep20, task_id in pattern.findall(index_path.read_text()):
        paper_rows[index] = dict(task_id=task_id, type=task_type, title=title.replace('~', ' '),
                                 split=split, ep20='checkmark' in ep20)
    assert len(paper_rows) == 100

    embodiments = {
        'dual-panda': 'Dual Franka Panda', 'panda': 'Franka Panda',
        'fr3-sharpa': 'FR3 + Sharpa hand', 'floating-sharpa': 'Floating Sharpa hand',
        'dual-floating-sharpa': 'Dual floating Sharpa hands',
        'aloha': 'Dual ALOHA grippers', 'dual-sharpa': 'Dual floating Sharpa hands',
        'fetch': 'Fetch mobile manipulator',
    }
    native_documentation = {
        'marble': 'Launch / Angry Birds contract',
        'hanoi_panda': 'Franka Hanoi contract',
        'hanoi_sharpa': 'FR3–Sharpa Hanoi contract',
        'hanoi_floating': 'Floating Sharpa Hanoi contract',
        'pocket_cube': 'Pocket cube contract',
        'rubiks_panda': 'Franka Rubik’s cube contract',
        'rubiks_sharpa': 'Floating Sharpa Rubik’s cube contract',
        'kongming_lock': 'Kongming lock contract',
        'bookshelf': 'Bookshelf contract',
        'maniskill_long_horizon': 'Home long-horizon contract',
        'maniskill_geometry': 'Home precision contract',
        'maniskill_dynamics': 'Home dynamics contract',
    }
    rows = []
    for original in data['task_results']:
        row = dict(original)
        member = paper_rows[row['index']]
        for field in ['task_id', 'split', 'ep20']:
            assert row[field] == member[field], (row['index'], field)
        row.update(type=member['type'], title=member['title'],
                   embodiment=embodiments[row['task_id'].split('/')[1]])
        rows.append(row)
    suite_counts = dict(collections.Counter(row['suite'] for row in rows))
    assert suite_counts == {'Launch': 34, 'Tower': 21, 'Lock': 16, 'Cube': 12, 'Home': 17}
    split_counts = dict(collections.Counter(row['split'] for row in rows))
    assert split_counts == {'Hard': 50, 'Easy': 50}
    assert sum(row['ep20'] for row in rows) == 20
    assert collections.Counter(row['split'] for row in rows if row['ep20']) == {'Easy': 10, 'Hard': 10}
    assert len({row['task_id'] for row in rows}) == 100

    for subset, metrics in data['subsets'].items():
        selected = [row for row in rows if subset == 'EP-100' or
                    (subset == 'EP-20' and row['ep20']) or
                    (subset == 'EP-Easy' and row['split'] == 'Easy') or
                    (subset == 'EP-Hard' and row['split'] == 'Hard')]
        assert len(selected) == metrics['tasks']
        assert metrics['conditions'] == len(selected) * 4
        for k in [1, 2]:
            pooled = sum(row[f'pass_at_{k}'] for row in selected) / len(selected)
            assert abs(pooled - metrics[f'pooled_pass_at_{k}']) < 1e-12
            assert sum(round(row[f'pass_at_{k}'] * 4) for row in selected) == metrics['first_successes' if k == 1 else 'within_two_successes']
            suite_means = []
            for suite, values in metrics['suites'].items():
                suite_rows = [row for row in selected if row['suite'] == suite]
                assert len(suite_rows) == values['tasks']
                mean = sum(row[f'pass_at_{k}'] for row in suite_rows) / len(suite_rows)
                assert abs(mean - values[f'pass_at_{k}']) < 1e-12
                suite_means.append(mean)
            assert abs(sum(suite_means) / 5 - metrics[f'suite_balanced_pass_at_{k}']) < 1e-12
        assert metrics['valid_attempts'] == metrics['conditions'] * 2 - metrics['first_successes']

    cold_start = dict(data['cold_start_summary'])
    cold_start['unique_socket_bind_sources'] = {
        Path(name).name: count for name, count in cold_start['unique_socket_bind_sources'].items()
    }
    experiment_id = 'codex-gpt-6-astra-l3-paper'
    experiment = {
        'id': experiment_id,
        'title': 'Final audited Codex evaluation',
        'model': data['model'], 'reasoning': data['reasoning'], 'access_level': 'L3',
        'source': metadata,
        'protocol': {
            'access_level': 'L3', 'observation_profile': 'privileged',
            'token_budget': 30000000, 'token_budget_includes_cached_input': True,
            'image_budget': 100, 'conditions_per_task': 4, 'base_seed': 0,
            'launcher_mode': 'loaded-only',
            'scoring': data['protocol'],
            'aggregation': 'Conditions averaged within tasks, tasks within suites, and the five suites equally.',
            'attempt_selection': 'First two valid attempts chronologically per condition, stopping at first success.',
            'exclusions': '69 confirmed infrastructure incidents excluded; 41 superseded extras unscored, including two native successes.',
            'agent_tools': ['Python standard library', 'NumPy', 'Pillow', 'Public environment SDK'],
            'auxiliary_tool_grants': [], 'pretrained_action_controllers': False,
            'reference_solutions_provided': False,
        },
        'subsets': data['subsets'],
        'audit_counts': data['audit_counts'],
        'disclosure_summary': data['disclosure_summary'],
        'cold_start_summary': cold_start,
        'failure_diagnostics': data['failure_diagnostics'],
        'failure_labels_note': 'Counts are native diagnostic incidences among failed attempts; multiple labels can apply to one failure. Labels alone do not establish agent, controller, or simulator causation.',
        'task_condition_success_histograms': data['task_condition_success_histograms'],
        'time_at_success_minutes': data['time_at_success_minutes'],
        'time_at_success_note': data['time_at_success_note'] + ' Measured over 91 successful attempts; prior unsuccessful attempts are excluded.',
        'task_results_file': 'data/ep100-index.json',
        'limitations': [
            'One model and agent configuration at L3 privileged access; broader model comparisons and controlled access, controller, and feedback ablations are needed.',
            'Incomplete rule or threshold disclosure affects 574 of 645 scored failures (88.99%). Native verdicts remain in the scores, with no scoring changes; these failures cannot be attributed solely to agent reasoning or control.',
            'Separate agent sessions and public, scratch, and runtime directories are evidenced for all 736 scored attempts. Cleared host or service caches and complete simulator-state independence are not certified.',
            'EP-20 overlaps EP-Easy and EP-Hard and is partly informed by pilot success evidence. It is a compact diagnostic selection, not an unbiased estimate of full-set performance.',
            'Complete provider token usage is unavailable, so no token efficiency metric is reported.',
            'Demonstration videos and scene previews illustrate tasks and reference behavior; they are not the scored Codex attempts and do not establish benchmark success.',
        ],
    }
    results = {'schema_version': 2, 'default_experiment': experiment_id,
               'experiments': [experiment]}
    index = {'schema_version': 2, 'source': metadata, 'suite_counts': suite_counts,
             'split_counts': split_counts, 'ep20_count': 20, 'task_results': rows}

    definitions = [
        ('Launch', 'Aim', 7, ['aiming', 'energy_budgeting', 'azimuth_control'],
         'Direct shots at single or paired targets, including azimuth aiming.', ['launch-a007-preview'],
         'Clear required targets within the shot budget while respecting launcher interlocks, physical limits, and any target rules.'),
        ('Launch', 'Causal', 13, ['causal_reasoning', 'trajectory_planning', 'physical_prediction'],
         'Indirect hits through rolling bodies, dominoes, and collapsing structures.', ['launch-roof-cascade-reference'],
         'Clear required targets through the declared damage or causal path within the shot budget and task rules.'),
        ('Launch', 'Glass', 5, ['material_reasoning', 'fracture_thresholds', 'energy_budgeting'],
         'Breakable glass panes with fracture thresholds.', ['launch-glass-preview'],
         'Clear targets and satisfy the required glass fracture predicates without violating the launcher contract.'),
        ('Launch', 'Rules', 9, ['constraint_tracking', 'ordered_actions', 'recovery'],
         'Ordered or protected targets and recovery after a miss.', ['launch-recovery-reference'],
         'Clear targets in the required order, preserve protected targets, and satisfy the required post-hit observation period.'),
        ('Tower', 'Plan', 5, ['hierarchical_planning', 'symbolic_state_tracking', 'contact_control'],
         'Planning depth from 1 to 31 moves on a standard Hanoi board.', ['hanoi-4090-demo'],
         'Reach the exact ring arrangement through legal moves, valid seating, and one second of stability.'),
        ('Tower', 'Physics', 8, ['physical_reasoning', 'contact_control', 'adaptation'],
         'Physical Hanoi board variations under the same legal-move rule.', ['hanoi-franka-preview'],
         'Reach the specified arrangement under the configured geometry, mass, or friction variation with legal moves and stable seating.'),
        ('Tower', 'Dex', 8, ['dexterous_grasping', 'finger_coordination', 'planning'],
         'Representative Hanoi boards with an FR3–Sharpa or floating Sharpa hand.', ['hanoi-sharpa-preview', 'hanoi-sharpa-two-ring-reference', 'hanoi-floating-h29-scene'],
         'Complete the board goal through legal ring transfers with the declared hand embodiment and required stability.'),
        ('Lock', 'Assemble', 6, ['geometric_reasoning', 'bimanual_coordination', 'insertion'],
         'Insert the key, key and bar, or full Kongming lock with two Panda arms.', ['kongming-dual-franka-reference'],
         'Reach the case-specific assembled arrangement, release the pieces, and maintain two seconds of stability under native contact checks.'),
        ('Lock', 'Disassemble', 6, ['geometric_reasoning', 'bimanual_coordination', 'extraction'],
         'Remove the key, key and bar, or all six pieces with two Panda arms.', ['kongming-dual-franka-disassemble-reference'],
         'Reach the case-specific disassembled arrangement, release the pieces, and maintain one second of stability under native contact checks.'),
        ('Lock', 'Dex', 4, ['dexterous_grasping', 'bimanual_coordination', 'geometric_reasoning'],
         'Kongming assembly and disassembly with two floating Sharpa hands.', ['kongming-floating-sharpa-a06-reference', 'kongming-floating-sharpa-d06-reference'],
         'Satisfy the native assembly or disassembly goal, release, stability, and contact predicates using two floating hands.'),
        ('Cube', 'Rubik', 8, ['symbolic_planning', 'fixture_control', 'state_tracking'],
         'Solve scrambles of 5, 10, or 15 tokens through the auxiliary fixture.', ['rubiks-franka-three-step', 'rubiks-franka-reference-cycle', 'rubiks-floating-sharpa-preview', 'rubiks-floating-sharpa-u3'],
         'Solve the physical cube with legal fixture use, return and release it, and satisfy a fresh 0.5-second stable window.'),
        ('Cube', 'Pocket', 4, ['bimanual_coordination', 'regrasping', 'layer_control'],
         'Prescribed layer turns with ALOHA grippers or two floating Sharpa hands.', ['pocket-cube-dual-aloha-preview', 'pocket-cube-dual-sharpa-preview'],
         'Reach the target state with the prescribed committed quarter turns, aligned detents, no active layer, and one second of stability.'),
        ('Home', 'Tidy', 5, ['scene_understanding', 'multi_object_planning', 'placement'],
         'Organize a bookshelf and correct misplaced objects.', ['bookshelf-overview'],
         'Satisfy all task placement and protection rules continuously for 0.5 seconds.'),
        ('Home', 'Long', 4, ['long_horizon_planning', 'mobile_manipulation', 'milestone_tracking'],
         'Multi-step household sequences with a mobile Fetch robot.', ['home-long-preview'],
         'Complete ordered milestones and final predicates, preserve protected objects, and sustain one second of successful dwell.'),
        ('Home', 'Precise', 4, ['insertion', 'geometry_reasoning', 'contact_control'],
         'Insertion, hooking, and narrow-gap placement with a Panda arm.', ['home-precise-preview'],
         'Complete ordered milestones and final geometric predicates within contact limits and one second of successful dwell.'),
        ('Home', 'Dynamic', 4, ['motion_prediction', 'timing', 'dynamic_control'],
         'Intercept, push, and close objects in motion with a Panda arm.', ['home-dynamic-preview'],
         'Complete motion and final predicates before event deadlines, preserve protected objects, and sustain one second of successful dwell.'),
    ]
    tasks = []
    for suite, task_type, expected_count, skills, summary, media, criteria in definitions:
        members = [row for row in rows if row['suite'] == suite and row['type'] == task_type]
        assert len(members) == expected_count
        native_groups = list(dict.fromkeys(row['task_id'].split('/')[0] for row in members))
        counts_by_embodiment = dict(collections.Counter(row['embodiment'] for row in members))
        assert sum(counts_by_embodiment.values()) == len(members)
        demo_scope = 'Representative task media and reference behavior; not the scored Codex trials or evidence of a success rate.'
        if not media:
            demo_scope = 'No matching type-specific demonstration is included. Counts and scores come from the paper index and audited evaluation.'
        if (suite, task_type) == ('Tower', 'Physics'):
            demo_scope = 'Representative Franka Hanoi reference replay; not a demonstration of all physical board variants or a scored Codex trial.'
        if (suite, task_type) == ('Launch', 'Aim'):
            demo_scope = 'Native A007 single-target controller reproduction, included in the EP-100 Aim selection. This recording succeeds; it is not a scored trial.'
        if (suite, task_type) == ('Launch', 'Glass'):
            demo_scope = 'A045 glass gatehouse saved-action replay, outside the EP-100 Glass selection. This replay succeeds; it is not a scored trial.'
        if (suite, task_type) == ('Cube', 'Rubik'):
            demo_scope += ' Short turn sequences illustrate manipulation; they do not establish completion of the benchmark scrambles.'
        tasks.append({
            'id': f'{suite.lower()}-{task_type.lower()}', 'title': f'{suite} · {task_type}',
            'family': suite, 'suite': suite, 'type': task_type, 'task_count': len(members),
            'embodiments': list(dict.fromkeys(row['embodiment'] for row in members)),
            'counts_by_embodiment': counts_by_embodiment,
            'skills': skills, 'summary': summary, 'media': media, 'success_criteria': criteria,
            'source': 'Paper sections/ep100.tex; appendices/ep100_index.tex; sections/evaluation_protocol.tex',
            'documentation': [
                {'label': native_documentation[group], 'path': f'docs/evaluation/{group}.en.md'}
                for group in native_groups
            ],
            'source_revision': data['subset_revision'], 'status': 'paper-indexed',
            'claim_status': 'representative-task-type', 'demo_scope': demo_scope,
            'access_levels': ['L0', 'L1', 'L2', 'L3'],
            'split_counts': dict(collections.Counter(row['split'] for row in members)),
            'ep20_count': sum(row['ep20'] for row in members),
            'task_ids': [row['task_id'] for row in members],
            'indices': [row['index'] for row in members],
            'score_source': 'data/ep100-index.json',
            'score_scope': 'Four registered conditions per task; final audited Codex gpt-6-astra high L3 experiment.',
        })
    assert len(tasks) == 16 and sum(task['task_count'] for task in tasks) == 100
    assert all(task['ep20_count'] > 0 for task in tasks)
    assert sum(item['failed_attempts'] for item in data['failure_diagnostics']) == 645
    assert data['audit_counts']['retained'] == 736 + 69 + 41
    outputs = {'results.json': results, 'ep100-index.json': index, 'tasks.json': tasks}
    for filename, value in outputs.items():
        validate_document(value, filename)
    for filename, value in outputs.items():
        rendered = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        assert not any(prefix in rendered for prefix in ['/Users/', '/home/', '/run/', '/private/'])
        destination = site / 'data' / filename
        if args.check:
            assert destination.read_text() == rendered, f'Stale generated data: {filename}'
        else:
            destination.write_text(rendered)
    print('Validated 100 unique tasks; suites 34/21/16/12/17; 16 task types; Easy/Hard 50/50; EP-20 20 (10/10).')
    print('All four subsets: precise pooled and suite-balanced Pass@1/2 independently match task rows; audit counts and source provenance verified.')
    print('Mode:', 'check (no writes)' if args.check else 'generated three JSON files')


if __name__ == '__main__':
    main()

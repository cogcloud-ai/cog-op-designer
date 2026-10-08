"""Deterministic proposal/child-build handoff; never execute a proposed Op."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(WORKSPACE / 'cog-workbench/src'))
sys.path.insert(0, str(WORKSPACE / 'cog-smith/templates/op/src'))
import cog_core
import cog_package
import op_runner
import op_spec
from workbench_suite import Suite, clean, digest, package_digest, require

SCHEMA = 'openteams/op-design-handoff [0.1]'


def prepare(request, envelope):
    payload = clean(envelope)
    require(envelope.get('cog') == cog_core.SELF_ID, 'Expected this designer identity.')
    require(not cog_core.validate_input(request) and not cog_core.validate_output(payload, request), 'Proposal failed packaged design checks.')
    require(payload['classification'] == 'proposed', 'Only a proposed design has a build handoff.')
    sha = digest({'request': request, 'proposal': payload})
    missing = []
    for brief in payload['cog_briefs']:
        identity = 'missing-' + digest({'proposal_sha256': sha, 'brief': brief})
        missing.append({'missing_cog_id': identity, 'brief_id': brief['id'],
                        'build_origin': {'proposal_sha256': sha, 'missing_cog_id': identity},
                        'prohibits': brief['prohibits'], 'name': brief['name'],
                        'builder_request': {'brief': brief['brief'], 'kind': brief.get('cog_kind', 'context'),
                                            'build_origin': {'proposal_sha256': sha, 'missing_cog_id': identity}},
                        'request': {'operation': 'design', 'brief': brief['brief'],
                                    'contract': None, 'identity': None, 'materials': [], 'feedback': [],
                                    'kind': brief.get('cog_kind', 'context')}})
    result = {'schema': SCHEMA, 'proposal_id': 'proposal-' + sha,
              'proposal_sha256': sha, 'request': request, 'envelope': envelope,
              'missing_cogs': missing,
              'artifact_ids': {a['id']: 'artifact-' + digest({'proposal_sha256': sha, 'artifact': a}) for a in payload['artifacts']}}
    result['sha256'] = digest(result)
    return copy.deepcopy(result)


def accepted_child(child, missing, suite):
    pending, decision = child['pending'], child['decision']
    require(pending.get('decides') == 'artifact' and (pending.get('artifact') or {}).get('kind') == 'cog-candidate', 'Child needs its candidate artifact Gate.')
    require((pending['artifact'].get('detail') or {}).get('build_origin') == missing['build_origin'], 'Child acceptance belongs to another missing Cog or proposal.')
    applied = op_runner.apply_decision(pending, decision)
    require(applied['verdict'] == 'accept', 'Rejected child candidates cannot enter a final Op.')
    package = child['materialization']; verification = child['verification']; assessment = child['assessment']
    root = suite.root(package['path']); manifest = suite.manifest(root)
    snapshot = package['plan_request']
    require(snapshot['contract'].get('kind', 'context') == missing['request']['kind'] and manifest.get('kind', 'context') == missing['request']['kind'], 'Child kind differs from its build brief.')
    require(set(missing['prohibits']) <= set(snapshot['contract'].get('prohibits', [])) and set(snapshot['contract'].get('prohibits', [])) <= set(manifest.get('prohibits', [])), 'Child must retain the brief and accepted contract prohibitions.')
    files = sorted(snapshot['files'], key=lambda row: row['path'])
    for row in files:
        path = suite.file(root, row['path'])
        require(path.is_file() and not path.is_symlink() and path.read_text() == row['content'], 'Accepted child source changed or does not match its snapshot.')
    source = digest({'contract': snapshot['contract'], 'files': files})
    expected = {'contract': digest(snapshot['contract']), 'source': source,
                'package': package_digest(root), 'evidence': digest(verification), 'assessment': digest(assessment)}
    require(pending['artifact']['digests'] == expected, 'Child contract/source/package/evidence/assessment differs from its acceptance.')
    require(package['source_sha256'] == source and package['package_sha256'] == expected['package'] and verification['package_sha256'] == expected['package'], 'Child materialization or verification receipt mismatch.')
    require(verification['review_request']['contract'] == snapshot['contract'] and sorted(verification['review_request']['files'], key=lambda row: row['path']) == files, 'Child review uses another source snapshot.')
    require(pending['payload'] == assessment and pending['payload_sha256'] == digest(assessment), 'Child pending review differs from the accepted assessment.')
    require(pending['artifact'].get('id') == manifest['id'], 'Accepted child Cog identity mismatch.')
    return root, manifest, child['task']


def schema_file(suite, root, manifest, key):
    path = suite.file(root, manifest['context'][key])
    require(path.is_file() and not path.is_symlink(), 'Declared schema must be a local package file.')
    return json.loads(path.read_text())


def compatible_schema(source, target):
    # A deliberately conservative proof: equality or a broad type-only target.
    return source == target or target is True or target == {} or (
        isinstance(source, dict) and isinstance(target, dict) and set(target) == {'type'}
        and source.get('type') == target['type'])


def aggregate_schema(ids, artifacts):
    if len(ids) == 1:
        return artifacts[ids[0]]['schema']
    return {'type': 'object', 'properties': {key: artifacts[key]['schema'] for key in ids},
            'required': ids, 'additionalProperties': False}


def finalize(handoff, children, reused, op_identity, op_dir, suite=None):
    suite = suite or Suite(workspace=WORKSPACE)
    expected = prepare(handoff['request'], handoff['envelope'])
    require(handoff == expected, 'Handoff changed; prepare and review the proposal again.')
    require(set(op_identity) == {'id', 'version', 'name'}, 'Provide explicit final Op id, version and name.')
    destination = suite.root(op_dir)
    proposal = handoff['envelope']['payload']
    missing = {row['brief_id']: row for row in handoff['missing_cogs']}
    require(set(children) == {row['missing_cog_id'] for row in missing.values()}, 'Supply exactly one accepted child for each missing Cog.')
    existing_ids = {s['choice']['cog_id'] for s in proposal['steps'] if s['choice']['kind'] == 'existing'}
    require(set(reused) == existing_ids, 'Supply exactly the reused Cog package selections.')
    cards = {row['id']: row for row in handoff['request']['catalog']}
    selected = {}
    for brief_id, row in missing.items():
        selected[brief_id] = accepted_child(children[row['missing_cog_id']], row, suite)
    for cid in existing_ids:
        root = suite.root(reused[cid]['path']); manifest = suite.manifest(root)
        require(manifest['id'] == cid and str(manifest['version']) == cards[cid]['version'] and package_digest(root) == cards[cid]['fingerprint'], 'Reused Cog disappeared or changed since proposal review.')
        selected[cid] = root, manifest, reused[cid]['task']
    artifacts = {row['id']: row for row in proposal['artifacts']}
    flows = {key: {'expression': 'inputs.' + key, 'producer': None} for key in proposal['inputs']}
    steps = []
    for proposed in proposal['steps']:
        choice = proposed['choice']
        if choice['kind'] == 'human':
            require(len(proposed['inputs']) == len(proposed['outputs']) == 1, 'Human review supports one artifact; split this review proposal.')
            before, after = proposed['inputs'][0], proposed['outputs'][0]
            flow = flows[before]
            require(flow['producer'] is not None, 'A human review needs a producing Cog step.')
            producer = next(step for step in steps if step['id'] == flow['producer'])
            require(producer['gate']['policy'] != 'human', 'Multiple human reviews need distinct producing Cog steps.')
            require(compatible_schema(artifacts[before]['schema'], artifacts[after]['schema']), 'Human artifact acceptance preserves bytes; input/output artifact schemas must match.')
            producer['gate'] = {'policy': 'human', 'decides': 'artifact',
                                'artifact': {'kind': 'op-artifact', 'id': handoff['artifact_ids'][before],
                                             'summary': proposed['purpose'],
                                             'digests': {'content': {'$sha256': {'$from': flow['expression']}}}}}
            flows[after] = dict(flow)
            continue
        require(choice['kind'] in ('existing', 'new'), 'Unbound code choices need a real Cog brief or reuse selection.')
        key = choice['cog_id'] if choice['kind'] == 'existing' else choice['brief_id']
        root, manifest, task = selected[key]
        require(not manifest.get('reaches') and not manifest.get('effects'), 'This handoff profile supports pure Cogs only; effectful Ops need explicit authority design.')
        require(compatible_schema(aggregate_schema(proposed['inputs'], artifacts), schema_file(suite, root, manifest, 'input_schema')), 'Schema-incompatible Cog input for step ' + proposed['id'])
        require(compatible_schema(schema_file(suite, root, manifest, 'output_schema'), aggregate_schema(proposed['outputs'], artifacts)), 'Schema-incompatible Cog output for step ' + proposed['id'])
        dependencies = sorted({flows[key]['producer'] for key in proposed['inputs'] if flows[key]['producer']})
        inputs = ({'$from': flows[proposed['inputs'][0]]['expression']} if len(proposed['inputs']) == 1 else
                  {key: {'$from': flows[key]['expression']} for key in proposed['inputs']})
        step = {'id': proposed['id'], 'name': proposed['purpose'],
                'cog': {'id': manifest['id'], 'version': str(manifest['version']), 'source': os.path.relpath(root, destination), 'task': task},
                'input': inputs, 'expected_outcome': proposed['purpose'],
                'gate': {'policy': op_spec.GATE_POLICY, 'guards': []}, 'on_fail': 'stop'}
        if dependencies:
            step['depends_on'] = dependencies
        steps.append(step)
        for key in proposed['outputs']:
            flows[key] = {'expression': 'steps.' + proposed['id'] + '.payload' + ('.' + key if len(proposed['outputs']) > 1 else ''), 'producer': proposed['id']}
    spec = {'schema': op_spec.SCHEMA_STRING, **op_identity, 'description': proposal['goal'],
            'inputs': [{'name': key, 'description': artifacts[key]['description'], 'required': True, 'schema': artifacts[key]['schema']} for key in proposal['inputs']],
            'steps': steps, 'outputs': {key: {'$from': flows[key]['expression']} for key in proposal['outputs']}}
    validated = op_spec.OpSpec(spec)
    problems = op_spec.declaration_problems(validated, destination)
    require(not problems, 'Final Op declarations failed: ' + '; '.join(problems))
    return {'schema': 'openteams/op-design-finalization [0.1]', 'proposal_sha256': handoff['proposal_sha256'],
            'op_spec': spec, 'op_spec_sha256': digest(spec), 'child_acceptances': {key: digest(value['decision']) for key, value in children.items()},
            'review_points': proposal['review_points'], 'criteria': proposal['criteria'],
            'status': 'validated-spec-not-executed-or-published'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'finalize'])
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    try:
        document = json.loads(Path(args.request).read_text())
        result = prepare(**document) if args.operation == 'prepare' else finalize(**document)
        envelope = cog_core._envelope('design-handoff', True, payload=result, binding={'source': 'deterministic-design-handoff'})
        code = 0
    except (ValueError, KeyError, TypeError, OSError, op_spec.OpSpecError, cog_package.PackageError) as exc:
        envelope = cog_core._fail('design-handoff', 'invalid-handoff', str(exc)); code = 1
    print(json.dumps(envelope))
    return code


if __name__ == '__main__':
    sys.exit(main())

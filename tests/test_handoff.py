"""Synthetic accepted child artifacts, mixed reuse, and final native Op validation."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('design_handoff', ROOT / 'scripts/design_handoff.py')
handoff = importlib.util.module_from_spec(spec); spec.loader.exec_module(handoff)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.design-handoff-', dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name).resolve()
        self.suite = handoff.Suite(self.workspace, self.workspace / 'state', journal=lambda x: None)
        self.schema = {'type': 'object', 'properties': {'text': {'type': 'string'}}, 'required': ['text'], 'additionalProperties': False}
        self.new = self.package('cog-child')
        self.reuse = self.package('cog-reused')
        self.card = {'id': 'example/cog-reused', 'version': '0.1.0', 'summary': 'Pure passthrough fixture', 'accepts': ['task_request'], 'produces': ['text'], 'capabilities': [], 'fingerprint': handoff.package_digest(self.reuse)}
        self.request = {'goal': 'Pass text through two pure Cogs, then review it.', 'success_criteria': ['Keep the text.'], 'constraints': [], 'catalog': [self.card], 'feedback': []}
        def choice(kind, key):
            return {'kind': kind, 'cog_id': key if kind == 'existing' else None, 'catalog_fingerprint': self.card['fingerprint'] if kind == 'existing' else None, 'brief_id': key if kind == 'new' else None, 'rationale': 'Explicit fixture selection.'}
        def step(sid, before, after, selected):
            return {'id': sid, 'purpose': 'Keep text for ' + sid, 'capability': 'text', 'inputs': [before], 'outputs': [after], 'criteria': ['keep'], 'choice': selected}
        self.proposal = {'abstained': False, 'classification': 'proposed', 'reason': None, 'goal': self.request['goal'], 'assumptions': [], 'questions': [], 'criteria': [{'id': 'keep', 'description': 'Keep the text.'}], 'artifacts': [{'id': key, 'description': key, 'schema': self.schema} for key in ['input', 'middle', 'output', 'accepted']], 'inputs': ['input'], 'outputs': ['accepted'], 'steps': [step('child', 'input', 'middle', choice('new', 'child')), step('reuse', 'middle', 'output', choice('existing', self.card['id'])), step('review', 'output', 'accepted', choice('human', None))], 'cog_briefs': [{'id': 'child', 'step_ids': ['child'], 'name': 'cog-child', 'brief': 'Keep text unchanged in a pure code Cog.', 'prohibits': [], 'cog_kind': 'code'}], 'review_points': ['Review the child contract and candidate.', 'Review the result.']}
        self.envelope = handoff.cog_core._envelope('ask', True, payload=self.proposal, binding={'source': 'synthetic-test-not-model-evidence'})
        self.prepared = handoff.prepare(self.request, self.envelope)
        self.missing = self.prepared['missing_cogs'][0]
        self.child = self.acceptance()

    def package(self, name):
        root = self.workspace / name
        shutil.copytree(ROOT.parent / 'cog-word-tally', root, ignore=shutil.ignore_patterns('.git', '.pixi', '__pycache__', 'runs'))
        manifest = yaml.safe_load((root / 'cog.yaml').read_text()); manifest['id'] = 'example/' + name
        (root / 'cog.yaml').write_text(yaml.safe_dump(manifest, sort_keys=False))
        for key in ['input-schema.json', 'output-schema.json']:
            (root / 'context' / key).write_text(json.dumps(self.schema))
        # This is an author-owned module, not an alteration to Smith machinery.
        (root / 'src/task_logic.py').write_text('def check_input(bundle): return []\ndef check_output(payload, bundle): return []\ndef run(bundle, grant, journal): return bundle, []\n')
        return root

    def acceptance(self):
        contract = {'kind': 'code', 'input_schema': self.schema, 'output_schema': json.loads((self.new / 'context/output-schema.json').read_text()), 'prohibits': [], 'acceptance_criteria': [{'id': 'keep', 'description': 'Keep the text.'}]}
        files = [{'path': name, 'content': (self.new / name).read_text()} for name in ['src/task_logic.py', 'context/input-schema.json', 'context/output-schema.json']]
        snapshot = {'operation': 'plan', 'contract': contract, 'files': files, 'evidence': []}
        source = handoff.digest({'contract': contract, 'files': sorted(files, key=lambda r: r['path'])})
        package = {'path': str(self.new), 'plan_request': snapshot, 'source_sha256': source, 'package_sha256': handoff.package_digest(self.new)}
        verification = {'package_sha256': package['package_sha256'], 'review_request': {**snapshot, 'operation': 'review'}, 'tests': {'exit_code': 0}, 'source': 'synthetic-test'}
        assessment = {'classification': 'pass', 'reason': 'Synthetic fixture; not a live assessment.', 'findings': []}
        artifact = {'kind': 'cog-candidate', 'id': 'example/cog-child', 'detail': {'build_origin': copy.deepcopy(self.missing['build_origin'])}, 'digests': {'contract': handoff.digest(contract), 'source': source, 'package': package['package_sha256'], 'evidence': handoff.digest(verification), 'assessment': handoff.digest(assessment)}}
        run = self.workspace / 'child-run'; run.mkdir(exist_ok=True)
        pending, _, _ = handoff.op_runner.write_pending(run, 'child-build', 'review', assessment, artifact)
        decision = {'schema': handoff.op_runner.DECISION_SCHEMA, 'run_id': 'child-build', 'step': 'review', 'payload_sha256': pending['payload_sha256'], 'artifact_sha256': pending['artifact_sha256'], 'verdict': 'accept', 'decided_by': 'synthetic-reviewer', 'decided_at': '2026-10-08T00:00:00Z'}
        return {'pending': pending, 'decision': decision, 'materialization': package, 'verification': verification, 'assessment': assessment, 'task': 'run'}

    def finalize(self):
        return handoff.finalize(self.prepared, {self.missing['missing_cog_id']: self.child}, {self.card['id']: {'path': str(self.reuse), 'task': 'run'}}, {'id': 'example/op-text', 'version': '0.1.0', 'name': 'Text fixture'}, self.workspace / 'op-text', self.suite)

    def test_identities_are_stable_and_change_when_proposal_changes(self):
        self.assertEqual(self.prepared, handoff.prepare(self.request, copy.deepcopy(self.envelope)))
        self.envelope['payload']['assumptions'].append('A new assumption')
        changed = handoff.prepare(self.request, self.envelope)
        self.assertNotEqual(changed['proposal_id'], self.prepared['proposal_id'])
        self.assertNotEqual(changed['missing_cogs'][0]['missing_cog_id'], self.missing['missing_cog_id'])

    def test_mixed_reuse_and_accepted_child_produce_valid_native_spec(self):
        result = self.finalize(); spec = handoff.op_spec.OpSpec(result['op_spec'])
        self.assertEqual(len(spec.steps), 2)
        self.assertEqual(spec.steps[1]['depends_on'], ['child'])
        self.assertEqual(spec.steps[1]['gate']['policy'], 'human')
        self.assertEqual(spec.outputs['accepted'], {'$from': 'steps.reuse.payload'})
        self.assertEqual(handoff.op_spec.declaration_problems(spec, self.workspace / 'op-text'), [])

    def test_rejected_child_and_another_proposals_child_are_refused(self):
        self.child['decision'].update(verdict='reject', reason='Not accepted')
        with self.assertRaisesRegex(ValueError, 'Rejected'):
            self.finalize()
        self.child = self.acceptance()
        self.child['pending']['artifact']['detail']['build_origin']['proposal_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'another'):
            self.finalize()

    def test_schema_incompatible_accepted_output_is_refused(self):
        (self.new / 'context/output-schema.json').write_text(json.dumps({'type': 'object', 'properties': {'text': {'type': 'integer'}}}))
        self.child = self.acceptance()
        with self.assertRaisesRegex(ValueError, 'Schema-incompatible Cog output'):
            self.finalize()

    def test_changed_source_and_stale_reused_package_are_refused(self):
        (self.new / 'src/task_logic.py').write_text('# changed after acceptance\n')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.finalize()
        self.child = self.acceptance()
        (self.reuse / 'src/task_logic.py').write_text('# changed after proposal\n')
        with self.assertRaisesRegex(ValueError, 'Reused Cog'):
            self.finalize()

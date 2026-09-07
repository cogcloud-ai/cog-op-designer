"""Checks for reviewable Op designs; no plan execution or catalog invention."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator


def problem(detail):
    return {'check': 'op-design', 'detail': detail, 'severity': 'error'}


def check_input(bundle):
    cards = bundle.get('catalog')
    if isinstance(cards, list):
        ids = [x.get('id') for x in cards if isinstance(x, dict)]
        if len(ids) != len(set(str(x) for x in ids)):
            return [problem('Catalog Cog IDs must be unique.')]
    return []


def render_input(bundle):
    return 'DESIGN INPUT DATA:\n' + json.dumps(bundle, ensure_ascii=False)


def check_output(payload, bundle):
    schema = json.loads((Path(__file__).resolve().parents[1] / 'context/output-schema.json').read_text())
    if not Draft202012Validator(schema).is_valid(payload):
        return [problem('Cannot inspect a malformed design payload.')]
    errors = []
    def check(ok, detail):
        if not ok:
            errors.append(problem(detail))
    check(payload['goal'] == bundle.get('goal'), 'Design must preserve the requested goal.')
    classification = payload['classification']
    check(payload['abstained'] == (classification == 'abstained'), 'Abstention flag contradicts classification.')
    if classification != 'proposed':
        check(not payload['steps'] and not payload['cog_briefs'] and not payload['artifacts'] and not payload['inputs'] and not payload['outputs'], 'Non-proposals cannot carry an executable-looking design.')
        check(bool(payload['questions']) if classification == 'needs_input' else bool(payload['reason']), 'Questions or an abstention reason are required.')
        return errors
    check(not payload['questions'] and payload['reason'] is None, 'A proposal must resolve questions or record assumptions.')
    check(bool(payload['steps']) and bool(payload['outputs']) and bool(payload['review_points']), 'A proposal requires steps, outputs and review points.')
    for collection in ('steps', 'criteria', 'artifacts', 'cog_briefs'):
        ids = [row['id'] for row in payload[collection]]
        check(len(ids) == len(set(ids)), collection + ' IDs must be unique.')
    criteria = {x['id'] for x in payload['criteria']}
    descriptions = {x['description'] for x in payload['criteria']}
    check(set(bundle.get('success_criteria', [])) <= descriptions, 'Every supplied success criterion must be preserved.')
    artifacts = {x['id']: x for x in payload['artifacts']}
    for artifact in artifacts.values():
        try:
            def local(node):
                if isinstance(node, dict):
                    for key, value in node.items():
                        if key in ('$ref', '$dynamicRef') and (not isinstance(value, str) or not value.startswith('#')):
                            raise ValueError()
                        local(value)
                elif isinstance(node, list):
                    for value in node:
                        local(value)
            local(artifact['schema'])
            Draft202012Validator.check_schema(artifact['schema'])
        except Exception:
            errors.append(problem('Artifact schemas must be valid and self-contained.'))
    available = set(payload['inputs'])
    used, covered = set(), set()
    check(available <= artifacts.keys(), 'Unknown Op input artifact.')
    cards = {x['id']: x for x in bundle.get('catalog', [])}
    briefs = {x['id']: x for x in payload['cog_briefs']}
    new_steps = {}
    for step in payload['steps']:
        check(set(step['inputs']) <= available, 'Step inputs must come from Op inputs or earlier steps; cycles are invalid.')
        check(not set(step['outputs']) & available, 'An artifact must have exactly one producer.')
        check(set(step['outputs']) <= artifacts.keys(), 'Unknown step output artifact.')
        check(set(step['criteria']) <= criteria, 'Unknown acceptance criterion.')
        check(len(step['outputs']) == len(set(step['outputs'])), 'Duplicate step outputs.')
        covered.update(step['criteria']); used.update(step['inputs']); available.update(step['outputs'])
        choice = step['choice']
        if choice['kind'] == 'existing':
            card = cards.get(choice['cog_id'])
            check(card is not None, 'Existing Cog must be present in the supplied catalog.')
            if card:
                check(choice['catalog_fingerprint'] == card['fingerprint'], 'Catalog fingerprint mismatch.')
                check(step['capability'] in card['capabilities'] + card['produces'], 'Catalog does not declare this capability or output.')
            check(choice['brief_id'] is None, 'Existing choices do not create new-Cog briefs.')
        elif choice['kind'] == 'new':
            check(choice['cog_id'] is None and choice['catalog_fingerprint'] is None, 'New Cogs cannot claim existing identities.')
            check(choice['brief_id'] in briefs, 'New Cog choice requires a brief.')
            new_steps.setdefault(choice['brief_id'], set()).add(step['id'])
        else:
            check(all(choice[k] is None for k in ('cog_id', 'catalog_fingerprint', 'brief_id')), 'Human steps have no Cog binding or build brief.')
    check(covered == criteria, 'Every acceptance criterion requires step coverage.')
    check(set(payload['outputs']) <= available, 'Op outputs have no producer or supplied input.')
    check(set(artifacts) == available, 'Unused or unproduced artifact declarations.')
    check(available <= used | set(payload['outputs']), 'Every input and step output must contribute to another step or final output.')
    for key, brief in briefs.items():
        check(set(brief['step_ids']) == new_steps.get(key, set()) and key in new_steps, 'Brief-to-step mapping must exactly cover its new-Cog steps.')
    return errors

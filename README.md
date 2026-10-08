# Cog Op Designer

A bounded **Context Cog** for starting from “What are you trying to accomplish?”
It proposes an Op and the capabilities it needs. It never runs or manages the Op.

Supply a goal, success criteria, constraints, optional catalog and feedback.
Receive a reviewable proposal with artifact schemas, ordered steps, candidate
Cog reuse, human review points and missing-Cog briefs. Questions and abstention
are explicit alternatives. The catalog is supplied data; the Cog does not search
registries or invent installed packages.

## Use

```sh
pixi install
pixi run test
pixi run resolve
pixi run ask -- --bundle examples/sample-bundle.json
```

The default model reference in `cog.yaml` is a legacy sibling-checkout
convenience and is not distributed with this Cog. A capable model and an
explicit binding are needed for useful designs. Workbench's `/studio` screen
can instead compose this Cog with an admitted Harness-only or Model+Harness Cog
through the declared `composition` interface. It executes the packaged input
and output checks around the external turn.

## Handoff to Cog building

Workbench validates a clean proposed envelope and current catalog fingerprints,
then prepares one cog-author **design** request per missing-Cog brief. The briefs
are not accepted work contracts. Review the author-designed contract, author
source, plan evaluations, package with Smith, run checks/cases, and ask the
independent evaluator Cog to review the evidence. Approval belongs to the caller.

The example is a hand-written meeting-action proposal, not live-model evidence.
The deterministic suite covers fabricated reuse, stale catalog identity, invalid
artifact flow/cycles, duplicate producers, brief mappings, criterion coverage,
unsafe schemas and malformed outputs. These checks do not prove the Op is useful
or complete. Workbench's binding qualification is a separate concern.

`pixi run eval` runs declared fixtures against the installed model. Tests of a
subscription composition must identify the combined model and harness; they
cannot be reported as bare-model evaluation results.

See the Workbench [tool-suite guide](https://github.com/cogcloud-ai/cog-workbench/blob/main/docs/tool-suite.md) for the complete workflow.

New build briefs may declare `cog_kind: code` for explicit-rule work (legacy
omission means context). Use `choice.kind: new` with a brief for either kind,
or `existing` with a catalog identity. The legacy unbound `code` choice remains
readable but Workbench refuses its build handoff until it has a real brief or
catalog choice. Pure code authoring is supported; external effects are outside
this first code-building extension.

## License

Copyright 2026 OpenTeams. Licensed under the [Apache License 2.0](LICENSE).
Third-party dependencies and external model services retain their own licenses
and terms. Previously published BSD-3-Clause versions remain available under
that license.

## Public preview

See the [suite guide](https://github.com/cogcloud-ai/cog-op-builder/blob/main/docs/repositories.md)
for repository roles, supported setup, and current limitations.

## Accepted child builds → executable Op

The declared `design-handoff` lifecycle task prepares durable identities without
invoking a model or running an Op:

```sh
pixi run design-handoff -- prepare --request examples/handoff-input.json
```

Its input is `{request, envelope}`: the original design request and a clean,
validated proposed result. The output envelope's payload is the handoff. A
proposal ID hashes the original request and proposal; each missing-Cog ID hashes
that proposal and its brief; each artifact ID hashes that proposal and its
artifact declaration. Re-preparing the same inputs gives the same IDs. Changing
the goal, catalog, brief, graph or artifact schema gives a different identity.

Each `missing_cogs` entry contains an author design `request`, a `builder_request`
stub, and `build_origin`. Supply a Smith identity to the stub, build the child
through the coordinating builder, and retain its contract and candidate Gates.
The builder must include `build_origin` in the candidate artifact's detail. A
brief is not an accepted contract, and an author's source is not an accepted Cog.

To finalize, call `pixi run design-handoff -- finalize --request finalization.json`
with `handoff`, `children`, `reused`, `op_identity` and `op_dir`. `children` maps
missing-Cog IDs to saved `{materialization, verification, assessment, pending,
decision, task}` documents from each accepted child build. `reused` maps catalog
Cog IDs to `{path, task}` selections. `op_identity` has `id`, `version`, `name`.
`op_dir` is the intended package directory within this public workspace; source
paths are computed relative to it.

Finalization verifies the child candidate's actual artifact decision using
Smith's shared semantics, exact source files and current package fingerprint,
contract/source/package/evidence/assessment hashes and proposal origin. It
rechecks reused catalog identity/fingerprints, then validates the final native Op
manifest and every declared usage task with public Smith. Save `payload.op_spec`
as JSON or YAML and pass it to `cogsmith op new --from-spec … --dir …`. The result
also retains criteria, review points and accepted-child decision fingerprints.
No package is created, installed, invoked or published by finalization.

This first executable handoff profile supports pure Cogs and explicit artifact
flows. One artifact maps to the whole Cog input/output; multiple artifacts map to
object properties named by their artifact IDs. Schema compatibility requires
structural equality, or a broad type-only receiving schema (or `true`/`{}`). It
refuses other relationships rather than guessing JSON Schema subsumption.
A single-artifact human review becomes an artifact acceptance Gate on the
producing Cog step and preserves its bytes; the reviewed artifact schema must
accept those bytes. Multiple independent human reviews need separate producing
steps. Unbound legacy code choices, effectful Cogs, rejected or stale child
candidates, cross-proposal children and incompatible schemas are refused. A
custom authority workflow or data conversion needs an explicit revised proposal.
Hash receipts correlate saved artifacts; they do not authenticate a reviewer.

Finalization validates supplied pending/decision documents against the current
behavior files and source snapshot. It does not read a terminal child Track or
authenticate acceptance: someone who can edit all local receipts can change a
rejection to acceptance. Locks, tests and other evidence-only files are outside
the behavior digest unless included in the source snapshot. Use retained accepted
Track documents as the source of these receipts; do not edit decisions to change
a rejected child's status. The public handoff example requests a pure-code child
compatible with the native Builder's supported slice.

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

The default model is a workspace-relative convenience. A capable model and an
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

See sibling `cog-workbench/docs/tool-suite.md` for the complete workflow.

## License

Copyright 2026 OpenTeams. Licensed under the [Apache License 2.0](LICENSE).
Third-party dependencies and external model services retain their own licenses
and terms. Previously published BSD-3-Clause versions remain available under
that license.

---
type: cog [0.1]
name: cog-op-designer
description: Designs reviewable Ops and Cog-building briefs from a goal.
version: "0.1.0"
license: BSD-3-Clause
publisher: OpenTeams
manifest: cog.yaml
manifest_schema: openteams/cog-manifest [0.1]
---

# Cog Op Designer

Given a goal, success criteria, constraints and an explicit catalog, proposes
an Op with connected artifact flows, candidate Cog reuse, human review points,
and briefs for missing Cogs. It never executes or manages the proposed Op.

The consumer reviews the proposal. Missing-Cog briefs feed cog-author design;
its resulting work contracts require a separate acceptance decision. Catalog
matches are suggestions, not admitted satisfiers. The dynamic selector/binder
qualifies implementations separately.

Packaged checks validate graph order, references, catalog identity and declared
fit, criterion coverage, brief mappings, and schema safety. They cannot prove
semantic completeness or model quality. Invalid outputs retain their problems.
Unsupported work abstains; consequential missing information asks questions.

Use `pixi run ask -- --bundle examples/sample-bundle.json` after binding a model,
or invoke through workbench's external composition bridge. `pixi run test` is
model-free; `pixi run eval` exercises the declared fixtures against a live model.

# Contributor instructions

Read COG.md and README.md. The Cog designs reviewable Ops; it never executes or
manages them. Edit task_logic.py and author-owned context, schemas and tests.
Other src modules are hash-verified Smith machinery; fix those upstream only.
The composition bridge is copied from cog-workbench/bridges/context_bridge.py.
Run pixi run test and Smith checking with --tests after behavior changes.
Never qualify catalog suggestions as admitted bindings or claim model quality
from deterministic fixtures. Preserve exact goals, criteria and catalog identity.

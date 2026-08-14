# Instructions for Coding Agents

Read these files before changing the project:

1. `docs/DESIGN_CHARTER.md`
2. `docs/ARCHITECTURE.md`
3. the active section of `docs/ROADMAP.md`

## Non-negotiables

- Keep the engine headless. No `input()` or terminal rendering outside `cli.py` or another UI adapter.
- Do not hardcode named world content in engine modules.
- Use stable string IDs and preserve save compatibility.
- Use deterministic seeded randomness for game outcomes.
- Add tests for successful behaviour and invalid commands.
- Make one milestone-sized change per branch/PR.
- Do not add multiplayer, romance/dynasty systems, runtime AI prose or a graphical framework unless the roadmap explicitly reaches them.
- Do not replace clear domain models with a generic ECS or plug-in framework prematurely.
- Do not silently change locked design decisions. Record proposed changes separately for Tyler to approve.

## Definition of a good feature

A feature is good when it:

- creates a meaningful player decision;
- connects to at least two existing systems;
- exposes understandable causes and consequences;
- works through `GameEngine` without depending on the CLI;
- is represented in serialisable state where persistence matters;
- is data-driven where authors should be able to extend it;
- has deterministic tests.

## Implementation workflow

1. State the exact capability and exclusions.
2. Inspect current state and tests.
3. Add or adjust definitions/state models.
4. Implement the smallest coherent system rule.
5. expose it through `GameEngine`.
6. Add a minimal CLI demonstration only when useful.
7. Add unit and scenario tests.
8. Validate save/content compatibility.
9. Update the relevant documentation.
10. Report what remains explicitly out of scope.

## Content effect changes

When adding an event effect operation:

- document its JSON shape;
- add it to content validation;
- implement it in one engine/system location;
- test valid and malformed use;
- consider whether it needs rollback or capacity validation;
- avoid arbitrary code execution from content.

## Save changes

Never alter the shape of `GameState` without either:

- keeping defaults compatible with existing saves; or
- incrementing the save schema and adding a migration.

## Code style

- Python 3.11+
- standard library by default;
- type hints on public functions;
- dataclasses for clear state/definition records;
- raise domain-readable `ValueError` or a future domain exception for invalid commands;
- no hidden network calls;
- keep functions small enough for rules to be tested independently.

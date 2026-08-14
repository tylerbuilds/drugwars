# The Neverwildens

**Working title.** A text-first fantasy economy RPG about becoming wealthy, collecting and raising creatures, owning property, exploring a changing world, and making choices whose effects persist.

This branch is a clean starter architecture built alongside the repository's original Drug Wars implementation. It keeps the fast economic clarity of Drug Wars while separating game rules from presentation and world content.

## What is already runnable

The starter includes thin, testable versions of:

- regional markets with deterministic daily price movement;
- weighted inventory and carrying limits;
- debt interest, travel and a persistent calendar;
- property purchase, resale and weekly income;
- owned pet creatures with bond, traits, value and records;
- simulated creature racing, betting payouts and creature fights;
- solo, strict-round player combat;
- permanent, socket-inspired active and support magic modules;
- Reigns-like event choices with flags and delayed-state support;
- faction reputation, knowledge and trade-prosperity state;
- JSON saves with an explicit schema version;
- a data-driven starter world and interactive terminal shell.

The current content is deliberately small. It proves the architecture; it is not meant to be the finished game.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
neverwildens
```

Or:

```bash
python -m neverwildens
```

Useful shell commands:

```text
status
market
buy moonmoss 2
routes
travel brambleward
event
choose follow
properties
creatures
train companion-1 speed
race companion-1
petfight companion-1
combat road_cutpurse
attack
magic ember
save save.json
quit
```

Run checks:

```bash
pytest
ruff check .
```

## Project shape

```text
content/starter_world.json      Starter content pack
src/neverwildens/models.py      Definitions and serialisable state
src/neverwildens/content.py     Content loading and validation
src/neverwildens/systems.py     Economy, property and creature systems
src/neverwildens/combat.py      Solo strict-round combat
src/neverwildens/engine.py      Headless command API
src/neverwildens/cli.py         Replaceable terminal presentation
tests/                          Behavioural tests
docs/                           Locked design and build guidance
AGENTS.md                       Rules for future coding agents/prompts
```

## Read before extending

1. [`docs/DESIGN_CHARTER.md`](docs/DESIGN_CHARTER.md) — the game we have actually chosen.
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system boundaries and save/content rules.
3. [`docs/ROADMAP.md`](docs/ROADMAP.md) — incremental milestones and acceptance criteria.
4. [`docs/CONTENT_GUIDE.md`](docs/CONTENT_GUIDE.md) — how worldbuilding plugs into the engine.
5. [`docs/PROMPT_PLAYBOOK.md`](docs/PROMPT_PLAYBOOK.md) — how to continue development safely across many prompts.

## Non-negotiable product rule

Every substantial activity should feed at least two other systems. Mining is not an isolated minigame: it supplies trade, property development, equipment and magic discoveries. Racing affects creature value, betting, reputation and rival relationships. Choices alter markets, faction power, access and property values.

## Legacy and licensing

The original `drugwars/` package remains as reference material. The new `src/neverwildens/` code is written as a separate architecture rather than a line-by-line conversion.

This repository currently carries the GNU GPL v3 licence. A deliberate licensing decision is required before treating the project as closed-source commercial software or moving it into a differently licensed repository.

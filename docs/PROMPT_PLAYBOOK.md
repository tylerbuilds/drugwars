# Multi-Prompt Development Playbook

## Why this exists

The game is too large for a reliable one-shot build. Future prompts should produce small, reviewable changes that preserve the architecture and leave the repository runnable.

## Prompt format

Use this structure for each development request:

```text
Read AGENTS.md, docs/DESIGN_CHARTER.md, docs/ARCHITECTURE.md and the relevant roadmap milestone.

Work only on: [one clearly named capability].

Required behaviour:
- [observable requirement]
- [observable requirement]

Out of scope:
- [tempting adjacent feature]
- [tempting adjacent feature]

Acceptance tests:
- [scenario]
- [scenario]

Update the relevant docs, run tests and open a draft PR.
```

## Recommended next prompts

### Prompt 1: debt and chapter loop

```text
Implement Milestone 1's debt, repayment and opening-chapter deadline only. Add bank/debt commands, scheduled interest, a day-30 reckoning and deterministic tests. Do not add new locations, NPC simulation or UI frameworks.
```

### Prompt 2: market history and rumours

```text
Add market price history, approximate historical bands and data-driven scheduled shortages. Expose them through the engine and CLI. Do not implement auctions or full supply-chain simulation.
```

### Prompt 3: event conditions and delayed consequences

```text
Replace simple event eligibility with a validated declarative condition system and delayed event scheduling. Migrate the starter events and add tests. Do not add prose-generation APIs.
```

### Prompt 4: first auction

```text
Implement a deterministic property auction with three NPC bidder strategies, valuation uncertainty and a CLI demonstration. Use the existing property definitions. Do not add creature auctions yet.
```

### Prompt 5: first real racing season

```text
Expand creature racing into a four-event seasonal league with entry selection, form, course conditions, betting and championship standings. Keep races simulated rather than manually steered. Do not implement breeding in the same change.
```

## Review questions after each prompt

- Is the feature fun or merely technically present?
- Does it feed at least two existing systems?
- Can the player understand why the result happened?
- Does the feature create a meaningful economic or emotional decision?
- Did the change hardcode world lore into the engine?
- Is save compatibility protected?
- Did the prompt accidentally begin another milestone?

## Worldbuilding sessions

Worldbuilding prompts should output content packs or structured worksheets, not engine changes, unless a genuinely new rule is required.

A useful content prompt:

```text
Using docs/CONTENT_GUIDE.md, design the starter region's eight persistent NPCs. Each needs an economic role, property or creature interest, faction relationship, personal goal, two event hooks and one way their circumstances can change without the player.
```

## Balancing sessions

Balancing should use seeded simulation and explicit targets. Do not balance solely by intuition after adding many interacting systems.

Example targets:

- a competent player can service opening debt without one lucky price spike;
- property is attractive but not an automatic best purchase;
- racing is positive expected value only with skill/information;
- rare magic modules are economically significant without trivialising property progression;
- inventory capacity creates trade-offs without forcing constant menu work.

# Architecture

## Principle: headless engine first

The engine must work without a terminal, browser or mobile interface. Presentation layers call commands on `GameEngine`; they do not mutate `GameState` directly.

This supports three intended clients:

1. terminal prototype;
2. browser interface with text, panels and creature/location art;
3. mobile-friendly vertical choice interface.

## Layers

### Content definitions

`content/starter_world.json` contains authored facts:

- locations and routes;
- commodities and regional multipliers;
- property definitions;
- creature species;
- magic modules;
- enemies;
- factions;
- choice events.

Definitions are immutable during play. Stable string IDs are public contracts. Renaming an ID requires a save migration.

### Runtime state

`GameState` contains facts unique to a save:

- day, location and action points;
- cash, debt, inventory and equipment;
- owned property and creatures;
- skills, perks and traits;
- world meters, flags, faction reputation and completed events.

Never put prose-only world lore into save state unless it represents a discovery or player-authored text.

### Systems

Systems implement rules over definitions and state:

- `MarketSystem`
- `InventorySystem`
- `PropertySystem`
- `CreatureSystem`
- combat functions
- future auction, gathering, NPC, faction and route systems

Systems should be deterministic when supplied the same content, state and seed. This makes saves reproducible and tests reliable.

### Command engine

`GameEngine` is the application boundary. It validates commands, coordinates systems, applies costs and writes log entries.

Future clients should call methods such as:

```python
engine.buy("moonmoss", 3)
engine.travel("brambleward")
engine.choose_event("follow")
engine.buy_property("riverside_rooms")
engine.race_creature("companion-1")
```

Do not teach a web route how property values are calculated. It should ask the engine.

## Determinism

Randomness is derived from SHA-256 of:

- save seed;
- system name;
- day or season;
- relevant stable IDs;
- attempt counter where repeated attempts are permitted.

Do not use Python's process-randomised `hash()` for game outcomes.

## Save rules

- Every save includes `schema_version`.
- A breaking state change requires a migration function.
- Content IDs referenced by saves cannot silently disappear.
- Saves serialise to plain JSON.
- Automated tests must load at least one previous-schema fixture once migrations exist.

## Content rules

- Engine code must not contain named locations, factions, commodities or creatures.
- Content effects use a small validated operation vocabulary.
- New effect operations require implementation, validation and tests.
- Content validation should fail early with a useful error.
- Narrative conditions will expand from flags into a declared condition language rather than arbitrary Python embedded in content.

## System integration rule

Every new activity must declare:

1. its input resources;
2. its output resources;
3. which player skill it exercises;
4. which world or economic state can alter it;
5. at least two systems it feeds.

Example:

```text
Mining
Inputs: action, tool condition, access right, stamina
Outputs: ore, surveys, relics, injuries
Skill: mining
Altered by: season, property upgrades, faction law
Feeds: market, construction, equipment, knowledge
```

## Future entity model

Add these in order, only when their milestone begins:

- `NPCState`: wealth, role, location, relationships, strategy and assets;
- `AuctionState`: lots, bidders, valuations and schedules;
- `SettlementState`: prosperity, security, access and faction control;
- `TransportState`: capacity, condition, routes and ownership;
- `BusinessState`: workers, inputs, outputs and policies;
- `PedigreeState`: parents, inherited traits and lineage claims;
- `QuestState` or `EventChainState`: explicit stage, not scattered flags;
- `EquipmentState`: sockets, links, condition and equipped modules;
- `GatheringSiteState`: depletion, hazards and discoveries.

## Avoid premature abstractions

Do not build a generic universal entity-component system. Use clear domain objects until repeated behaviour proves a shared abstraction is needed.

Do not replace JSON with a database until content size, querying or authoring pain justifies it. SQLite is the likely first persistence upgrade for large worlds; it is not required for the starter.

## Testing levels

1. **Unit:** price, weight, property valuation, race scoring and combat rounds.
2. **System:** commands alter state correctly and reject invalid actions.
3. **Scenario:** a fixed seed can complete a representative economic loop.
4. **Content:** all references and effect operations validate.
5. **Save:** round-trip and migration behaviour.

A feature is not complete merely because the CLI can demonstrate it.

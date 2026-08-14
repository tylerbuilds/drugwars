# Content and Worldbuilding Guide

## Build systems before encyclopaedias

Worldbuilding should answer gameplay needs. Do not begin with twenty kingdoms and several thousand years of chronology. Begin with the places, goods, institutions and conflicts required by the current milestone.

For each region, create content in this order:

1. economic function;
2. property market;
3. creature ecology;
4. factions and laws;
5. routes and gathering sites;
6. recurring NPCs;
7. visible history;
8. hidden cosmology;
9. event chains and prose variation.

## Region worksheet

A complete playable region needs:

- one economic hub;
- two or three smaller settlements;
- at least one wilderness or ruin area;
- six to twelve meaningful commodities;
- understandable local production and demand;
- residential, commercial, resource and personal property opportunities;
- one racing circuit or competition culture;
- at least three creature species with local relevance;
- two or three factions with conflicting incentives;
- twelve to twenty persistent named NPCs at mature scope;
- one inaccessible or partially understood old route;
- a central economic disruption that player choices can affect.

## Commodity worksheet

Every commodity should have more than a resale price.

```text
ID:
Name:
Where produced:
Where consumed:
Normal price band:
Weight/bulk:
Seasonal behaviour:
Legal status by region:
Direct use:
Property/production use:
Creature use:
Magic or knowledge use:
Events that alter supply/demand:
```

At least half of the important commodities should be usable outside trade.

## Property worksheet

```text
ID:
Name:
Location:
Category:
Base value:
Income/cost schedule:
Current condition:
Storage/capacity:
Required inputs:
Outputs:
Upgrade branches:
Worker or tenant decisions:
Events generated:
Effects on settlement:
Effects on creature systems:
Hidden feature or historical clue:
```

Property upgrades should create choices rather than a single linear ladder whenever depth is added.

## Creature worksheet

```text
Species ID:
Common name:
Ecology:
Legal/ownership status:
Base value:
Age stages:
Racing role:
Fighting role:
Working role:
Core statistics:
Natural traits:
Possible transformations:
Breeding rules:
Care preferences:
Relationship to old systems:
How NPC cultures treat it:
```

A creature must be more than a bundle of racing statistics. Give it behaviour that matters in choices, property, travel or gathering.

## Event worksheet

A strong event contains:

- a concrete situation;
- two to four competing priorities;
- at least one state-dependent option where appropriate;
- an immediate outcome;
- one remembered consequence;
- a plausible path to a later event, market change or relationship reaction.

Avoid:

- obvious good/evil buttons;
- fake choices whose outcomes are identical;
- punishment that could not reasonably be anticipated;
- lore lectures detached from action;
- random comedy that undercuts an important emotional scene.

## Prose scale

Use three prose lengths:

- **transaction:** one clear sentence;
- **ordinary event:** 40–120 words plus concise choices;
- **major discovery:** 150–350 words, used sparingly.

Most play should remain fast. Atmosphere belongs where it changes meaning, not on every shop purchase.

## Hidden cosmology discipline

Material Deities elements should arrive as evidence:

- impossible joins in star-iron;
- socket layouts repeated across weapons and ruins;
- creatures reacting to dormant routes;
- factions suppressing surveys;
- economic shocks after an old connection opens;
- religious rituals that are also functional maintenance procedures.

Do not place a final explanatory document in the first region. Let several interpretations survive.

## IDs and authoring

- IDs use lowercase `snake_case`.
- IDs never contain display prose.
- Names may change; IDs should not.
- All cross-references use IDs.
- Content packs must pass `load_world()` validation before review.
- New authored content should include at least one automated scenario or validation test when it adds a new rule.

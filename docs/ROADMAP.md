# Incremental Roadmap

This project is intentionally too large for one prompt or one pull request. Each milestone below should be developed on its own branch, with tests and a playable demonstration.

## Milestone 0 — Foundation starter

**Status:** scaffolded in this branch.

Contains thin versions of market, inventory, time, debt, property, creatures, racing, creature fighting, choice events, saving, solo combat and linked magic.

Acceptance criteria:

- `pytest` passes;
- a new game can buy, travel, choose an event, acquire property, race a creature, fight and save;
- engine has no terminal input calls;
- content validates before play.

## Milestone 1 — Complete the economic loop

Build:

- buy/sell spreads and transaction costs;
- price history and player-facing valuation bands;
- scheduled market events and shortages;
- bank, debt repayment and refinancing;
- transport capacity and condition;
- chapter-one debt deadline and outcome;
- scenario test covering a profitable regional trade loop.

Do not add more regions yet.

## Milestone 2 — Choice engine, NPCs and factions

Build:

- declarative event conditions;
- event-chain stages rather than flag sprawl;
- 8–12 persistent NPCs in the starter region;
- relationship values and memory tags;
- NPC economic strategies;
- faction laws and access gates;
- delayed event scheduling;
- 25 polished events with at least five delayed consequences.

## Milestone 3 — Property, auctions and businesses

Build:

- auctions with competing bidders and valuations;
- property listings and scheduled sales;
- condition, repairs and upgrade branches;
- tenant and worker policies;
- warehouses and local storage;
- one residential, one commercial and one resource-property loop;
- property effects on settlement prosperity and prices.

## Milestone 4 — Creature ownership simulation

Build:

- acquisition, sale and sanctuary capacity;
- age stages, care, mood and bond;
- training plans and diminishing returns;
- seasonal racing leagues and betting;
- tactical management policies for creature fights;
- pedigree data and breeding;
- inherited and developed traits;
- creature transformations tied to treatment and environment;
- market valuation and auction integration.

## Milestone 5 — Player combat and modular magic

Build:

- equipment definitions and real socket layouts;
- linked active/support combinations;
- module growth and mastery;
- status effects, items and flee rules;
- multiple enemies while the player remains the sole player-controlled combatant;
- defeat recovery and risk;
- combat encounters integrated with routes and exploration;
- at least one rare-module economic dilemma.

## Milestone 6 — Mining, fishing and commissions

Build:

- branching gathering encounters;
- tools, condition, access rights and site quality;
- common and rare result tables;
- fishing seasons, bait and water conditions;
- mine hazards, surveys and depth;
- commissioned crafting through specialist NPCs;
- resource-property integration;
- gathering effects on local supply and prices.

## Milestone 7 — Living settlements and old routes

Build:

- settlement prosperity, security and trade access;
- visible changes to shops, rents, NPCs and event decks;
- route reopening and closure;
- regional expansion framework;
- one material-deity discovery that changes actual economics;
- migration and faction-control consequences.

## Milestone 8 — Browser and mobile-friendly UI

Only begin after the headless scenario tests prove the game loop.

Build:

- API or in-process application service around `GameEngine`;
- browser layout with text, market, inventory, creature and property panels;
- vertical swipe/tap choice presentation suitable for mobile;
- optional pixel-art or illustrated creature/location cards;
- accessible keyboard navigation;
- save selection and import/export.

## Milestone 9 — Content production tools

Build only when manual JSON authoring becomes the bottleneck:

- schema-backed editor;
- content preview;
- event graph viewer;
- economy sanity checks;
- missing-reference detection;
- balancing simulation over thousands of seeded runs;
- localisation-ready prose storage.

## Definition of done for every milestone

- design charter still holds;
- data model changes are documented;
- save compatibility is preserved or migrated;
- invalid commands fail without corrupting state;
- at least one deterministic automated scenario demonstrates the feature;
- README or relevant documentation is updated;
- no unrelated pillar is added "while we are here".

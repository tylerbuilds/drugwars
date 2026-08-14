from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .combat import CombatSession, resolve_round, start_combat
from .content import WorldContent
from .models import GameState, InventoryState, OwnedPropertyState, PlayerState, WorldState
from .systems import (
    CreatureSystem,
    InventorySystem,
    MarketSystem,
    PropertySystem,
    deterministic_rng,
)


class GameEngine:
    """Headless command layer. User interfaces call this; they do not mutate state directly."""

    SAVE_SCHEMA_VERSION = 1

    def __init__(self, content: WorldContent, state: GameState):
        self.content = content
        self.state = state
        self.active_combat: CombatSession | None = None

    @classmethod
    def new_game(cls, content: WorldContent, seed: int = 1) -> GameEngine:
        settings = content.settings
        player = PlayerState(
            cash=int(settings.get("starting_cash", 2_000)),
            debt=int(settings.get("starting_debt", 5_500)),
            inventory=InventoryState(
                capacity_kg=float(settings.get("starting_capacity_kg", 25.0))
            ),
            skills={
                "trading": 1,
                "property": 1,
                "creature_handling": 1,
                "combat": 1,
                "knowledge": 1,
            },
            equipped_modules=list(settings.get("starting_modules", ["ember", "mend"])),
            module_links=deepcopy(settings.get("starting_module_links", [])),
        )
        for property_definition in content.properties.values():
            if property_definition.starting_owned:
                player.properties[property_definition.id] = OwnedPropertyState(
                    property_id=property_definition.id,
                    purchase_price=0,
                    condition=65,
                )

        starter_species = settings.get("starting_creature_species_id", "ashcat")
        starter = CreatureSystem.create(
            content,
            creature_id="companion-1",
            species_id=starter_species,
            name=settings.get("starting_creature_name", "Nim"),
        )
        player.creatures[starter.id] = starter

        state = GameState(
            schema_version=cls.SAVE_SCHEMA_VERSION,
            seed=seed,
            day=1,
            action_points=int(settings.get("actions_per_day", 3)),
            current_location_id=settings["starting_location_id"],
            player=player,
            world=WorldState(
                faction_reputation={faction_id: 0 for faction_id in content.factions}
            ),
            log=["You inherit a damaged home, a debt, and one unusual creature."],
        )
        InventorySystem.add(state, "glowfruit", 3)
        return cls(content, state)

    def market_quotes(self) -> dict[str, int]:
        return MarketSystem.all_quotes(self.content, self.state)

    def inventory_weight(self) -> float:
        return InventorySystem.weight(self.content, self.state)

    def buy(self, commodity_id: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if commodity_id not in self.content.commodities:
            raise ValueError("Unknown commodity")
        price = MarketSystem.quote(self.content, self.state, commodity_id)
        total = price * quantity
        if self.state.player.cash < total:
            raise ValueError("Not enough cash")
        if not InventorySystem.can_add(self.content, self.state, commodity_id, quantity):
            raise ValueError("Not enough carrying capacity")
        self.state.player.cash -= total
        InventorySystem.add(self.state, commodity_id, quantity)
        self._gain_skill("trading", 1)
        self._log(f"Bought {quantity} {commodity_id} for {total} crowns.")
        return total

    def sell(self, commodity_id: str, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        price = MarketSystem.quote(self.content, self.state, commodity_id)
        InventorySystem.remove(self.state, commodity_id, quantity)
        total = price * quantity
        self.state.player.cash += total
        self._gain_skill("trading", 1)
        self._log(f"Sold {quantity} {commodity_id} for {total} crowns.")
        return total

    def travel(self, destination_id: str) -> int:
        if self.active_combat is not None and not self.active_combat.finished:
            raise ValueError("Cannot travel during combat")
        route = self.content.route_between(self.state.current_location_id, destination_id)
        if route is None:
            raise ValueError("No direct route to that destination")
        origin = self.state.current_location_id
        self._advance_days(route.days)
        self.state.current_location_id = destination_id
        self.state.action_points = int(self.content.settings.get("actions_per_day", 3))
        self._log(f"Travelled from {origin} to {destination_id} in {route.days} day(s).")
        self.draw_event("travel")
        return route.days

    def available_destinations(self) -> list[str]:
        return sorted(
            route.destination
            for route in self.content.routes
            if route.origin == self.state.current_location_id
        )

    def property_listings(self) -> dict[str, int]:
        return {
            property_id: PropertySystem.current_value(self.content, self.state, property_id)
            for property_id, definition in self.content.properties.items()
            if definition.location_id == self.state.current_location_id
            and property_id not in self.state.player.properties
        }

    def buy_property(self, property_id: str) -> int:
        price = PropertySystem.buy(self.content, self.state, property_id)
        self._gain_skill("property", 2)
        self._log(f"Bought property {property_id} for {price} crowns.")
        return price

    def sell_property(self, property_id: str) -> int:
        proceeds = PropertySystem.sell(self.content, self.state, property_id)
        self._gain_skill("property", 1)
        self._log(f"Sold property {property_id} for {proceeds} crowns.")
        return proceeds

    def train_creature(self, creature_id: str, stat: str) -> int:
        self._spend_action()
        new_value = CreatureSystem.train(self.state, creature_id, stat)
        self._gain_skill("creature_handling", 1)
        self._log(f"Trained {creature_id}: {stat} is now {new_value}.")
        return new_value

    def race_creature(self, creature_id: str):
        self._spend_action()
        fee = int(self.content.settings.get("race_entry_fee", 30))
        result = CreatureSystem.race(self.content, self.state, creature_id, fee)
        self._gain_skill("creature_handling", 1)
        self._log(
            f"{creature_id} placed {result.placing}; racing payout {result.payout} crowns."
        )
        return result

    def fight_creature(self, creature_id: str):
        self._spend_action()
        fee = int(self.content.settings.get("creature_fight_entry_fee", 25))
        result = CreatureSystem.fight(self.content, self.state, creature_id, fee)
        self._gain_skill("creature_handling", 1)
        self._log(
            f"{creature_id} {'won' if result.won else 'lost'} its bout; payout {result.payout}."
        )
        return result

    def creature_collection_score(self) -> int:
        return CreatureSystem.collection_score(self.content, self.state)

    def begin_combat(self, enemy_id: str) -> CombatSession:
        if enemy_id not in self.content.enemies:
            raise ValueError("Unknown enemy")
        if self.active_combat is not None and not self.active_combat.finished:
            raise ValueError("A combat is already active")
        self._spend_action()
        self.active_combat = start_combat(self.content, enemy_id)
        self._log(f"Combat started against {enemy_id}.")
        return self.active_combat

    def combat_action(self, action: str, module_id: str | None = None) -> list[str]:
        if self.active_combat is None:
            raise ValueError("No active combat")
        messages = resolve_round(
            self.content,
            self.state,
            self.active_combat,
            action,
            module_id,
        )
        if self.active_combat.finished and self.active_combat.won:
            self._gain_skill("combat", 2)
        for message in messages:
            self._log(message)
        return messages

    def draw_event(self, trigger: str) -> str | None:
        if self.state.active_event_id is not None:
            return self.state.active_event_id
        eligible = []
        for event in self.content.events.values():
            if event.trigger != trigger:
                continue
            if event.once and event.id in self.state.world.completed_events:
                continue
            if event.location_ids and self.state.current_location_id not in event.location_ids:
                continue
            if not set(event.requires_flags).issubset(self.state.world.flags):
                continue
            if set(event.forbids_flags) & self.state.world.flags:
                continue
            eligible.append(event)
        if not eligible:
            return None
        rng = deterministic_rng(
            self.state.seed,
            "event",
            self.state.day,
            trigger,
            self.state.current_location_id,
        )
        event = rng.choice(eligible)
        self.state.active_event_id = event.id
        self._log(f"Event: {event.title}")
        return event.id

    def current_event(self):
        if self.state.active_event_id is None:
            return None
        return self.content.events[self.state.active_event_id]

    def choose_event(self, choice_id: str) -> str:
        event = self.current_event()
        if event is None:
            raise ValueError("No active event")
        choice = next((choice for choice in event.choices if choice.id == choice_id), None)
        if choice is None:
            raise ValueError("Unknown event choice")
        for effect in choice.effects:
            self._apply_effect(effect)
        if event.once:
            self.state.world.completed_events.add(event.id)
        self.state.active_event_id = None
        self._log(choice.outcome)
        return choice.outcome

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.state.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, content: WorldContent, path: str | Path) -> GameEngine:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        state = GameState.from_dict(data)
        if state.schema_version != cls.SAVE_SCHEMA_VERSION:
            raise ValueError("Unsupported save schema; add a migration before loading")
        return cls(content, state)

    def summary(self) -> dict[str, Any]:
        location = self.content.locations[self.state.current_location_id]
        property_value = sum(
            PropertySystem.current_value(self.content, self.state, property_id)
            for property_id in self.state.player.properties
        )
        inventory_value = sum(
            MarketSystem.quote(self.content, self.state, item_id) * quantity
            for item_id, quantity in self.state.player.inventory.quantities.items()
        )
        wealth = self.state.player.cash + property_value + inventory_value - self.state.player.debt
        return {
            "day": self.state.day,
            "location": location.name,
            "actions": self.state.action_points,
            "cash": self.state.player.cash,
            "debt": self.state.player.debt,
            "wealth": wealth,
            "inventory_weight": self.inventory_weight(),
            "inventory_capacity": self.state.player.inventory.capacity_kg,
            "trade_prosperity": self.state.world.trade_prosperity,
            "knowledge": self.state.world.knowledge,
            "creature_collection": self.creature_collection_score(),
            "factions": dict(self.state.world.faction_reputation),
        }

    def _advance_days(self, days: int) -> None:
        daily_interest = float(self.content.settings.get("daily_debt_interest", 0.01))
        for _ in range(days):
            self.state.day += 1
            self.state.player.debt = int(round(self.state.player.debt * (1 + daily_interest)))
            for creature in self.state.player.creatures.values():
                creature.age_days += 1
            if self.state.day % 7 == 0:
                income = PropertySystem.collect_weekly_income(self.content, self.state)
                if income:
                    self._log(f"Properties generated {income} crowns this week.")

    def _spend_action(self) -> None:
        if self.state.action_points <= 0:
            raise ValueError("No action points remain; travel or end the day")
        self.state.action_points -= 1

    def _gain_skill(self, skill: str, amount: int) -> None:
        self.state.player.skills[skill] = self.state.player.skills.get(skill, 0) + amount

    def _apply_effect(self, effect: dict[str, Any]) -> None:
        operation = effect["op"]
        value = effect.get("value", 0)
        target = effect.get("target")
        if operation == "cash":
            self.state.player.cash += int(value)
        elif operation == "debt":
            self.state.player.debt = max(0, self.state.player.debt + int(value))
        elif operation == "knowledge":
            self.state.world.knowledge += int(value)
            self._gain_skill("knowledge", int(value))
        elif operation == "trade_prosperity":
            self.state.world.trade_prosperity = min(
                100, max(0, self.state.world.trade_prosperity + int(value))
            )
        elif operation == "faction":
            if target is None:
                raise ValueError("Faction effects require target")
            self.state.world.faction_reputation[target] = (
                self.state.world.faction_reputation.get(target, 0) + int(value)
            )
        elif operation == "flag":
            if target is None:
                raise ValueError("Flag effects require target")
            self.state.world.flags.add(target)
        elif operation == "item":
            if target is None:
                raise ValueError("Item effects require target")
            if int(value) >= 0:
                if not InventorySystem.can_add(self.content, self.state, target, int(value)):
                    raise ValueError("Event reward exceeds carrying capacity")
                InventorySystem.add(self.state, target, int(value))
            else:
                InventorySystem.remove(self.state, target, abs(int(value)))
        elif operation == "trait":
            if target is None:
                raise ValueError("Trait effects require target")
            if target not in self.state.player.traits:
                self.state.player.traits.append(target)
        elif operation == "market_modifier":
            if target is None:
                raise ValueError("Market modifier effects require target")
            self.state.world.market_modifiers[target] = float(value)
        else:
            raise ValueError(f"Unsupported effect operation: {operation}")

    def _log(self, message: str) -> None:
        self.state.log.append(message)
        self.state.log[:] = self.state.log[-100:]

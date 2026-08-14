from __future__ import annotations

import hashlib
import random

from .content import WorldContent
from .models import (
    CreatureFightResult,
    CreatureState,
    GameState,
    OwnedPropertyState,
    RaceResult,
)


def deterministic_rng(seed: int, *parts: object) -> random.Random:
    raw = ":".join(str(part) for part in (seed, *parts)).encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


class InventorySystem:
    @staticmethod
    def weight(content: WorldContent, state: GameState) -> float:
        total = 0.0
        for item_id, quantity in state.player.inventory.quantities.items():
            commodity = content.commodities.get(item_id)
            if commodity is not None:
                total += commodity.weight_kg * quantity
        return round(total, 3)

    @classmethod
    def can_add(
        cls, content: WorldContent, state: GameState, item_id: str, quantity: int
    ) -> bool:
        if quantity < 0 or item_id not in content.commodities:
            return False
        added_weight = content.commodities[item_id].weight_kg * quantity
        return cls.weight(content, state) + added_weight <= state.player.inventory.capacity_kg

    @staticmethod
    def add(state: GameState, item_id: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        state.player.inventory.quantities[item_id] = (
            state.player.inventory.quantities.get(item_id, 0) + quantity
        )

    @staticmethod
    def remove(state: GameState, item_id: str, quantity: int) -> None:
        owned = state.player.inventory.quantities.get(item_id, 0)
        if quantity < 0 or owned < quantity:
            raise ValueError("Not enough inventory")
        remaining = owned - quantity
        if remaining:
            state.player.inventory.quantities[item_id] = remaining
        else:
            state.player.inventory.quantities.pop(item_id, None)


class MarketSystem:
    @staticmethod
    def quote(content: WorldContent, state: GameState, commodity_id: str) -> int:
        commodity = content.commodities[commodity_id]
        location = content.locations[state.current_location_id]
        local_multiplier = location.market_multipliers.get(commodity_id, 1.0)
        world_modifier = state.world.market_modifiers.get(commodity_id, 1.0)
        prosperity_modifier = 1.0 + ((50 - state.world.trade_prosperity) / 500)
        rng = deterministic_rng(
            state.seed, "market", state.day, state.current_location_id, commodity_id
        )
        daily_variation = rng.uniform(0.84, 1.16)
        value = (
            commodity.base_price
            * local_multiplier
            * world_modifier
            * prosperity_modifier
            * daily_variation
        )
        return max(1, int(round(value)))

    @classmethod
    def all_quotes(cls, content: WorldContent, state: GameState) -> dict[str, int]:
        return {
            commodity_id: cls.quote(content, state, commodity_id)
            for commodity_id in content.commodities
        }


class PropertySystem:
    @staticmethod
    def current_value(content: WorldContent, state: GameState, property_id: str) -> int:
        definition = content.properties[property_id]
        location = content.locations[definition.location_id]
        prosperity_factor = 0.7 + (state.world.trade_prosperity / 100)
        rng = deterministic_rng(state.seed, "property", state.day // 7, property_id)
        market_cycle = rng.uniform(0.94, 1.08)
        return max(
            1,
            int(
                round(
                    definition.purchase_price
                    * location.property_multiplier
                    * prosperity_factor
                    * market_cycle
                )
            ),
        )

    @classmethod
    def buy(cls, content: WorldContent, state: GameState, property_id: str) -> int:
        if property_id in state.player.properties:
            raise ValueError("Property already owned")
        definition = content.properties[property_id]
        if definition.location_id != state.current_location_id:
            raise ValueError("Property is not in the current location")
        price = cls.current_value(content, state, property_id)
        if state.player.cash < price:
            raise ValueError("Not enough cash")
        state.player.cash -= price
        state.player.properties[property_id] = OwnedPropertyState(
            property_id=property_id,
            purchase_price=price,
        )
        return price

    @classmethod
    def sell(cls, content: WorldContent, state: GameState, property_id: str) -> int:
        if property_id not in state.player.properties:
            raise ValueError("Property not owned")
        definition = content.properties[property_id]
        if definition.starting_owned:
            raise ValueError("The starting home cannot be sold in the starter build")
        gross = cls.current_value(content, state, property_id)
        proceeds = int(round(gross * 0.94))
        state.player.cash += proceeds
        del state.player.properties[property_id]
        return proceeds

    @staticmethod
    def collect_weekly_income(content: WorldContent, state: GameState) -> int:
        income = sum(
            content.properties[property_id].weekly_income
            for property_id in state.player.properties
        )
        state.player.cash += income
        return income


class CreatureSystem:
    @staticmethod
    def create(
        content: WorldContent,
        *,
        creature_id: str,
        species_id: str,
        name: str,
    ) -> CreatureState:
        species = content.creature_species[species_id]
        return CreatureState(
            id=creature_id,
            species_id=species_id,
            name=name,
            age_days=120,
            bond=20,
            market_value=species.base_value,
            stats=dict(species.stats),
            traits=list(species.traits[:1]),
        )

    @staticmethod
    def collection_score(content: WorldContent, state: GameState) -> int:
        distinct_species = {creature.species_id for creature in state.player.creatures.values()}
        achievements = sum(
            creature.race_wins + creature.fight_wins
            for creature in state.player.creatures.values()
        )
        raw_value = sum(creature.market_value for creature in state.player.creatures.values())
        return len(distinct_species) * 25 + achievements * 10 + raw_value // 100

    @staticmethod
    def train(state: GameState, creature_id: str, stat: str) -> int:
        creature = state.player.creatures[creature_id]
        if stat not in creature.stats:
            raise ValueError(f"Unknown creature stat: {stat}")
        creature.stats[stat] += 1
        creature.bond = min(100, creature.bond + 1)
        creature.market_value += 5
        return creature.stats[stat]

    @staticmethod
    def race(
        content: WorldContent, state: GameState, creature_id: str, entry_fee: int
    ) -> RaceResult:
        if state.player.cash < entry_fee:
            raise ValueError("Not enough cash for the entry fee")
        creature = state.player.creatures[creature_id]
        state.player.cash -= entry_fee
        rng = deterministic_rng(state.seed, "race", state.day, creature_id, creature.race_starts)

        def score(stats: dict[str, int], noise: float) -> float:
            return (
                stats.get("speed", 0) * 0.50
                + stats.get("stamina", 0) * 0.30
                + stats.get("focus", 0) * 0.20
                + noise
            )

        entrants: list[tuple[str, float]] = [
            (creature.name, score(creature.stats, rng.uniform(-8, 8)))
        ]
        rival_species = list(content.creature_species.values())[:3]
        for index, species in enumerate(rival_species, start=1):
            entrants.append(
                (
                    f"{species.name} #{index}",
                    score(species.stats, rng.uniform(-8, 8)),
                )
            )
        entrants.sort(key=lambda row: row[1], reverse=True)
        placing = next(
            index
            for index, row in enumerate(entrants, start=1)
            if row[0] == creature.name
        )
        payout_table = {1: entry_fee * 5, 2: entry_fee * 2, 3: entry_fee}
        payout = payout_table.get(placing, 0)
        state.player.cash += payout
        creature.race_starts += 1
        if placing == 1:
            creature.race_wins += 1
            creature.market_value += 50
        return RaceResult(entrants=tuple(entrants), placing=placing, payout=payout)

    @staticmethod
    def fight(
        content: WorldContent, state: GameState, creature_id: str, entry_fee: int
    ) -> CreatureFightResult:
        if state.player.cash < entry_fee:
            raise ValueError("Not enough cash for the entry fee")
        creature = state.player.creatures[creature_id]
        state.player.cash -= entry_fee
        rng = deterministic_rng(
            state.seed, "creature-fight", state.day, creature_id, creature.fight_starts
        )
        player_score = (
            creature.stats.get("strength", 0) * 0.5
            + creature.stats.get("stamina", 0) * 0.3
            + creature.stats.get("focus", 0) * 0.2
            + rng.uniform(-7, 7)
        )
        species = rng.choice(list(content.creature_species.values()))
        opponent_score = (
            species.stats.get("strength", 0) * 0.5
            + species.stats.get("stamina", 0) * 0.3
            + species.stats.get("focus", 0) * 0.2
            + rng.uniform(-7, 7)
        )
        won = player_score >= opponent_score
        payout = entry_fee * 3 if won else 0
        state.player.cash += payout
        creature.fight_starts += 1
        if won:
            creature.fight_wins += 1
            creature.market_value += 35
        return CreatureFightResult(
            player_score=player_score,
            opponent_score=opponent_score,
            won=won,
            payout=payout,
        )

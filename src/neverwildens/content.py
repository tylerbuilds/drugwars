from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import (
    CommodityDefinition,
    CreatureSpeciesDefinition,
    EnemyDefinition,
    EventChoiceDefinition,
    EventDefinition,
    LocationDefinition,
    MagicModuleDefinition,
    PropertyDefinition,
    RouteDefinition,
)


class ContentError(ValueError):
    """Raised when a world pack is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class WorldContent:
    meta: dict[str, Any]
    settings: dict[str, Any]
    commodities: dict[str, CommodityDefinition]
    locations: dict[str, LocationDefinition]
    routes: tuple[RouteDefinition, ...]
    properties: dict[str, PropertyDefinition]
    creature_species: dict[str, CreatureSpeciesDefinition]
    magic_modules: dict[str, MagicModuleDefinition]
    enemies: dict[str, EnemyDefinition]
    events: dict[str, EventDefinition]
    factions: dict[str, dict[str, Any]]

    def route_between(self, origin: str, destination: str) -> RouteDefinition | None:
        return next(
            (
                route
                for route in self.routes
                if route.origin == origin and route.destination == destination
            ),
            None,
        )


def _index_unique(records: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ContentError(f"Every {label} requires a non-empty string id")
        if record_id in indexed:
            raise ContentError(f"Duplicate {label} id: {record_id}")
        indexed[record_id] = record
    return indexed


def load_world(path: str | Path) -> WorldContent:
    source = Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"))

    commodity_rows = _index_unique(raw.get("commodities", []), "commodity")
    location_rows = _index_unique(raw.get("locations", []), "location")
    property_rows = _index_unique(raw.get("properties", []), "property")
    species_rows = _index_unique(raw.get("creature_species", []), "creature species")
    module_rows = _index_unique(raw.get("magic_modules", []), "magic module")
    enemy_rows = _index_unique(raw.get("enemies", []), "enemy")
    event_rows = _index_unique(raw.get("events", []), "event")
    faction_rows = _index_unique(raw.get("factions", []), "faction")

    commodities = {
        key: CommodityDefinition(
            id=key,
            name=value["name"],
            base_price=int(value["base_price"]),
            weight_kg=float(value["weight_kg"]),
            description=value.get("description", ""),
            tags=tuple(value.get("tags", [])),
        )
        for key, value in commodity_rows.items()
    }
    locations = {
        key: LocationDefinition(
            id=key,
            name=value["name"],
            description=value.get("description", ""),
            market_multipliers={
                item_id: float(multiplier)
                for item_id, multiplier in value.get("market_multipliers", {}).items()
            },
            property_multiplier=float(value.get("property_multiplier", 1.0)),
        )
        for key, value in location_rows.items()
    }
    routes = tuple(
        RouteDefinition(
            origin=row["origin"],
            destination=row["destination"],
            days=int(row.get("days", 1)),
            risk=float(row.get("risk", 0.0)),
        )
        for row in raw.get("routes", [])
    )
    properties = {
        key: PropertyDefinition(
            id=key,
            name=value["name"],
            location_id=value["location_id"],
            purchase_price=int(value["purchase_price"]),
            weekly_income=int(value.get("weekly_income", 0)),
            description=value.get("description", ""),
            starting_owned=bool(value.get("starting_owned", False)),
            category=value.get("category", "residential"),
        )
        for key, value in property_rows.items()
    }
    species = {
        key: CreatureSpeciesDefinition(
            id=key,
            name=value["name"],
            description=value.get("description", ""),
            base_value=int(value["base_value"]),
            stats={name: int(score) for name, score in value["stats"].items()},
            traits=tuple(value.get("traits", [])),
        )
        for key, value in species_rows.items()
    }
    modules = {
        key: MagicModuleDefinition(
            id=key,
            name=value["name"],
            kind=value["kind"],
            effect=value["effect"],
            power=int(value.get("power", 0)),
            description=value.get("description", ""),
            value=int(value.get("value", 0)),
            permanent=bool(value.get("permanent", True)),
        )
        for key, value in module_rows.items()
    }
    enemies = {
        key: EnemyDefinition(
            id=key,
            name=value["name"],
            max_hp=int(value["max_hp"]),
            attack=int(value["attack"]),
            reward_cash=int(value.get("reward_cash", 0)),
            description=value.get("description", ""),
        )
        for key, value in enemy_rows.items()
    }
    events = {
        key: EventDefinition(
            id=key,
            trigger=value["trigger"],
            title=value["title"],
            text=value["text"],
            choices=tuple(
                EventChoiceDefinition(
                    id=choice["id"],
                    text=choice["text"],
                    effects=tuple(choice.get("effects", [])),
                    outcome=choice.get("outcome", ""),
                )
                for choice in value["choices"]
            ),
            location_ids=tuple(value.get("location_ids", [])),
            once=bool(value.get("once", True)),
            requires_flags=tuple(value.get("requires_flags", [])),
            forbids_flags=tuple(value.get("forbids_flags", [])),
        )
        for key, value in event_rows.items()
    }

    content = WorldContent(
        meta=dict(raw.get("meta", {})),
        settings=dict(raw.get("settings", {})),
        commodities=commodities,
        locations=locations,
        routes=routes,
        properties=properties,
        creature_species=species,
        magic_modules=modules,
        enemies=enemies,
        events=events,
        factions=faction_rows,
    )
    validate_world(content)
    return content


def validate_world(content: WorldContent) -> None:
    if not content.locations:
        raise ContentError("A world pack needs at least one location")
    if not content.commodities:
        raise ContentError("A world pack needs at least one commodity")

    starting_location = content.settings.get("starting_location_id")
    if starting_location not in content.locations:
        raise ContentError("settings.starting_location_id must reference a location")

    for route in content.routes:
        if route.origin not in content.locations or route.destination not in content.locations:
            raise ContentError(f"Route references unknown location: {route}")
        if route.days < 1:
            raise ContentError("Routes must take at least one day")

    for location in content.locations.values():
        unknown = set(location.market_multipliers) - set(content.commodities)
        if unknown:
            raise ContentError(
                f"Location {location.id} has multipliers for unknown commodities: {unknown}"
            )

    for property_definition in content.properties.values():
        if property_definition.location_id not in content.locations:
            raise ContentError(
                f"Property {property_definition.id} references unknown location"
            )

    allowed_effects = {
        "cash",
        "debt",
        "knowledge",
        "trade_prosperity",
        "faction",
        "flag",
        "item",
        "trait",
        "market_modifier",
    }
    for event in content.events.values():
        choice_ids = [choice.id for choice in event.choices]
        if len(choice_ids) != len(set(choice_ids)):
            raise ContentError(f"Event {event.id} contains duplicate choice ids")
        for choice in event.choices:
            for effect in choice.effects:
                if effect.get("op") not in allowed_effects:
                    raise ContentError(
                        f"Event {event.id} uses unsupported effect op: {effect.get('op')}"
                    )

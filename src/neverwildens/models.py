from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CommodityDefinition:
    id: str
    name: str
    base_price: int
    weight_kg: float
    description: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocationDefinition:
    id: str
    name: str
    description: str
    market_multipliers: dict[str, float]
    property_multiplier: float = 1.0


@dataclass(frozen=True)
class RouteDefinition:
    origin: str
    destination: str
    days: int
    risk: float = 0.0


@dataclass(frozen=True)
class PropertyDefinition:
    id: str
    name: str
    location_id: str
    purchase_price: int
    weekly_income: int
    description: str = ""
    starting_owned: bool = False
    category: str = "residential"


@dataclass(frozen=True)
class CreatureSpeciesDefinition:
    id: str
    name: str
    description: str
    base_value: int
    stats: dict[str, int]
    traits: tuple[str, ...] = ()


@dataclass(frozen=True)
class MagicModuleDefinition:
    id: str
    name: str
    kind: str
    effect: str
    power: int
    description: str
    value: int
    permanent: bool = True


@dataclass(frozen=True)
class EnemyDefinition:
    id: str
    name: str
    max_hp: int
    attack: int
    reward_cash: int
    description: str = ""


@dataclass(frozen=True)
class EventChoiceDefinition:
    id: str
    text: str
    effects: tuple[dict[str, Any], ...]
    outcome: str


@dataclass(frozen=True)
class EventDefinition:
    id: str
    trigger: str
    title: str
    text: str
    choices: tuple[EventChoiceDefinition, ...]
    location_ids: tuple[str, ...] = ()
    once: bool = True
    requires_flags: tuple[str, ...] = ()
    forbids_flags: tuple[str, ...] = ()


@dataclass
class InventoryState:
    capacity_kg: float = 25.0
    quantities: dict[str, int] = field(default_factory=dict)


@dataclass
class OwnedPropertyState:
    property_id: str
    purchase_price: int
    condition: int = 100
    upgrade_level: int = 0


@dataclass
class CreatureState:
    id: str
    species_id: str
    name: str
    age_days: int
    bond: int
    market_value: int
    stats: dict[str, int]
    traits: list[str] = field(default_factory=list)
    race_starts: int = 0
    race_wins: int = 0
    fight_starts: int = 0
    fight_wins: int = 0


@dataclass
class PlayerState:
    cash: int
    debt: int
    hp: int = 100
    max_hp: int = 100
    mp: int = 30
    max_mp: int = 30
    base_attack: int = 12
    inventory: InventoryState = field(default_factory=InventoryState)
    skills: dict[str, int] = field(default_factory=dict)
    perks: list[str] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    properties: dict[str, OwnedPropertyState] = field(default_factory=dict)
    creatures: dict[str, CreatureState] = field(default_factory=dict)
    equipped_modules: list[str] = field(default_factory=list)
    module_links: list[list[str]] = field(default_factory=list)


@dataclass
class WorldState:
    trade_prosperity: int = 50
    knowledge: int = 0
    faction_reputation: dict[str, int] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)
    completed_events: set[str] = field(default_factory=set)
    market_modifiers: dict[str, float] = field(default_factory=dict)


@dataclass
class GameState:
    schema_version: int
    seed: int
    day: int
    action_points: int
    current_location_id: str
    player: PlayerState
    world: WorldState
    active_event_id: str | None = None
    log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["world"]["flags"] = sorted(self.world.flags)
        data["world"]["completed_events"] = sorted(self.world.completed_events)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameState:
        inventory = InventoryState(**data["player"].pop("inventory"))
        properties = {
            key: OwnedPropertyState(**value)
            for key, value in data["player"].pop("properties").items()
        }
        creatures = {
            key: CreatureState(**value)
            for key, value in data["player"].pop("creatures").items()
        }
        player = PlayerState(
            **data["player"],
            inventory=inventory,
            properties=properties,
            creatures=creatures,
        )
        world_data = data["world"]
        world = WorldState(
            trade_prosperity=world_data["trade_prosperity"],
            knowledge=world_data["knowledge"],
            faction_reputation=dict(world_data["faction_reputation"]),
            flags=set(world_data["flags"]),
            completed_events=set(world_data["completed_events"]),
            market_modifiers=dict(world_data.get("market_modifiers", {})),
        )
        return cls(
            schema_version=data["schema_version"],
            seed=data["seed"],
            day=data["day"],
            action_points=data["action_points"],
            current_location_id=data["current_location_id"],
            player=player,
            world=world,
            active_event_id=data.get("active_event_id"),
            log=list(data.get("log", [])),
        )


@dataclass(frozen=True)
class RaceResult:
    entrants: tuple[tuple[str, float], ...]
    placing: int
    payout: int


@dataclass(frozen=True)
class CreatureFightResult:
    player_score: float
    opponent_score: float
    won: bool
    payout: int

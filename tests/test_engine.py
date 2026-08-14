from __future__ import annotations

from pathlib import Path

import pytest

from neverwildens.content import load_world
from neverwildens.engine import GameEngine


CONTENT_PATH = Path(__file__).parents[1] / "content" / "starter_world.json"


@pytest.fixture
def content():
    return load_world(CONTENT_PATH)


@pytest.fixture
def engine(content):
    return GameEngine.new_game(content, seed=17)


def test_new_game_exposes_locked_progress_measures(engine):
    summary = engine.summary()
    assert summary["day"] == 1
    assert summary["location"] == "Bellweather"
    assert summary["trade_prosperity"] == 50
    assert summary["knowledge"] == 0
    assert summary["creature_collection"] > 0
    assert set(summary["factions"]) == {"brass_ledger", "roadwardens", "wild_choir"}


def test_buy_sell_and_weight_limit(engine):
    starting_cash = engine.state.player.cash
    price = engine.market_quotes()["moonmoss"]
    total = engine.buy("moonmoss", 2)
    assert total == price * 2
    assert engine.state.player.cash == starting_cash - total
    assert engine.state.player.inventory.quantities["moonmoss"] == 2

    proceeds = engine.sell("moonmoss", 1)
    assert proceeds == price
    assert engine.state.player.inventory.quantities["moonmoss"] == 1

    engine.state.player.cash = 100_000
    with pytest.raises(ValueError, match="carrying capacity"):
        engine.buy("star_iron", 4)


def test_travel_advances_days_and_compounds_debt(engine):
    starting_debt = engine.state.player.debt
    days = engine.travel("cinderdeep")
    assert days == 2
    assert engine.state.day == 3
    assert engine.state.current_location_id == "cinderdeep"
    assert engine.state.player.debt > starting_debt
    assert engine.state.action_points == 3


def test_property_purchase_and_weekly_income(engine):
    purchase_price = engine.buy_property("riverside_rooms")
    cash_after_purchase = engine.state.player.cash
    assert purchase_price > 0
    assert "riverside_rooms" in engine.state.player.properties

    engine._advance_days(6)
    assert engine.state.day == 7
    assert engine.state.player.cash == cash_after_purchase + 70


def test_event_effects_persist(engine):
    engine.state.active_event_id = "broken_courier"
    starting_cash = engine.state.player.cash
    outcome = engine.choose_event("help")
    assert "route mark" in outcome
    assert engine.state.player.cash == starting_cash - 20
    assert engine.state.world.knowledge == 2
    assert engine.state.world.faction_reputation["roadwardens"] == 2
    assert "helped_broken_courier" in engine.state.world.flags
    assert "broken_courier" in engine.state.world.completed_events


def test_save_round_trip(content, engine, tmp_path):
    engine.buy("blackroot", 2)
    engine.state.active_event_id = "tenant_roof"
    engine.choose_event("contribute")
    save_path = tmp_path / "save.json"
    engine.save(save_path)

    loaded = GameEngine.load(content, save_path)
    assert loaded.state.to_dict() == engine.state.to_dict()
    assert loaded.summary() == engine.summary()


def test_race_is_deterministic_for_same_seed(content):
    first = GameEngine.new_game(content, seed=99)
    second = GameEngine.new_game(content, seed=99)
    result_a = first.race_creature("companion-1")
    result_b = second.race_creature("companion-1")
    assert result_a == result_b


def test_creature_fight_updates_record(engine):
    creature = engine.state.player.creatures["companion-1"]
    result = engine.fight_creature("companion-1")
    assert creature.fight_starts == 1
    assert creature.fight_wins == int(result.won)


def test_player_combat_is_solo_strict_rounds(engine):
    session = engine.begin_combat("road_cutpurse")
    starting_hp = engine.state.player.hp
    messages = engine.combat_action("magic", "ember")
    assert messages
    assert session.round_number == 2 or session.finished
    assert engine.state.player.hp <= starting_hp

    for _ in range(10):
        if session.finished:
            break
        engine.combat_action("attack")
    assert session.finished
    assert session.won

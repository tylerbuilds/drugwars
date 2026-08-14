from __future__ import annotations

import argparse
import cmd
from pathlib import Path

from .content import load_world
from .engine import GameEngine


def default_content_path() -> Path:
    candidates = [
        Path.cwd() / "content" / "starter_world.json",
        Path(__file__).resolve().parents[2] / "content" / "starter_world.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not find content/starter_world.json")


class NeverwildensShell(cmd.Cmd):
    intro = "The Neverwildens starter. Type help or ? to list commands."
    prompt = "never> "

    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine

    def do_status(self, _: str) -> None:
        """Show the five progress measures and immediate player state."""
        for key, value in self.engine.summary().items():
            print(f"{key.replace('_', ' ').title()}: {value}")

    def do_market(self, _: str) -> None:
        """Show current commodity prices."""
        for item_id, price in self.engine.market_quotes().items():
            name = self.engine.content.commodities[item_id].name
            owned = self.engine.state.player.inventory.quantities.get(item_id, 0)
            print(f"{item_id:14} {name:18} {price:>6} crowns  owned {owned}")

    def do_buy(self, arg: str) -> None:
        """buy ITEM_ID QUANTITY"""
        self._run_amount_command(self.engine.buy, arg)

    def do_sell(self, arg: str) -> None:
        """sell ITEM_ID QUANTITY"""
        self._run_amount_command(self.engine.sell, arg)

    def do_routes(self, _: str) -> None:
        """List direct destinations."""
        print("Direct routes:", ", ".join(self.engine.available_destinations()))

    def do_travel(self, destination: str) -> None:
        """travel LOCATION_ID"""
        try:
            days = self.engine.travel(destination.strip())
            print(f"Travel took {days} day(s).")
            self._print_event()
        except ValueError as error:
            print(error)

    def do_event(self, _: str) -> None:
        """Show the current event, or draw an exploration event."""
        if self.engine.current_event() is None:
            self.engine.draw_event("explore")
        self._print_event()

    def do_choose(self, choice_id: str) -> None:
        """choose CHOICE_ID"""
        try:
            print(self.engine.choose_event(choice_id.strip()))
        except ValueError as error:
            print(error)

    def do_properties(self, _: str) -> None:
        """Show owned property and current local listings."""
        print("Owned:")
        for property_id in self.engine.state.player.properties:
            print(f"  {property_id}")
        print("Local listings:")
        for property_id, value in self.engine.property_listings().items():
            print(f"  {property_id}: {value} crowns")

    def do_buyproperty(self, property_id: str) -> None:
        """buyproperty PROPERTY_ID"""
        try:
            price = self.engine.buy_property(property_id.strip())
            print(f"Purchased for {price} crowns.")
        except ValueError as error:
            print(error)

    def do_sellproperty(self, property_id: str) -> None:
        """sellproperty PROPERTY_ID"""
        try:
            proceeds = self.engine.sell_property(property_id.strip())
            print(f"Sold for {proceeds} crowns.")
        except ValueError as error:
            print(error)

    def do_creatures(self, _: str) -> None:
        """Show creatures, stats, records, bond and value."""
        for creature in self.engine.state.player.creatures.values():
            print(
                f"{creature.id}: {creature.name} ({creature.species_id}) "
                f"value={creature.market_value} bond={creature.bond} stats={creature.stats} "
                f"races={creature.race_wins}/{creature.race_starts} "
                f"fights={creature.fight_wins}/{creature.fight_starts}"
            )

    def do_train(self, arg: str) -> None:
        """train CREATURE_ID STAT"""
        parts = arg.split()
        if len(parts) != 2:
            print("Usage: train CREATURE_ID STAT")
            return
        try:
            score = self.engine.train_creature(parts[0], parts[1])
            print(f"New {parts[1]} score: {score}")
        except (KeyError, ValueError) as error:
            print(error)

    def do_race(self, creature_id: str) -> None:
        """race CREATURE_ID"""
        try:
            result = self.engine.race_creature(creature_id.strip())
            print(f"Placed {result.placing}; payout {result.payout} crowns")
            for index, (name, score) in enumerate(result.entrants, start=1):
                print(f"  {index}. {name}: {score:.1f}")
        except (KeyError, ValueError) as error:
            print(error)

    def do_petfight(self, creature_id: str) -> None:
        """petfight CREATURE_ID"""
        try:
            result = self.engine.fight_creature(creature_id.strip())
            print(
                f"{'Won' if result.won else 'Lost'}: "
                f"{result.player_score:.1f} vs {result.opponent_score:.1f}; "
                f"payout {result.payout}"
            )
        except (KeyError, ValueError) as error:
            print(error)

    def do_combat(self, enemy_id: str) -> None:
        """combat ENEMY_ID"""
        try:
            session = self.engine.begin_combat(enemy_id.strip())
            print(f"Combat begins. Enemy HP: {session.enemy_hp}")
        except ValueError as error:
            print(error)

    def do_attack(self, _: str) -> None:
        """Attack during active player combat."""
        self._combat_action("attack")

    def do_defend(self, _: str) -> None:
        """Defend during active player combat."""
        self._combat_action("defend")

    def do_magic(self, module_id: str) -> None:
        """magic MODULE_ID"""
        self._combat_action("magic", module_id.strip())

    def do_save(self, path: str) -> None:
        """save PATH"""
        destination = path.strip() or "save.json"
        self.engine.save(destination)
        print(f"Saved to {destination}")

    def do_quit(self, _: str) -> bool:
        """Quit the game."""
        return True

    do_exit = do_quit
    do_EOF = do_quit

    def _run_amount_command(self, function, arg: str) -> None:
        parts = arg.split()
        if len(parts) != 2:
            print("Expected ITEM_ID QUANTITY")
            return
        try:
            total = function(parts[0], int(parts[1]))
            print(f"Transaction total: {total} crowns")
        except (ValueError, KeyError) as error:
            print(error)

    def _print_event(self) -> None:
        event = self.engine.current_event()
        if event is None:
            print("No event is active.")
            return
        print(f"\n{event.title}\n{event.text}")
        for choice in event.choices:
            print(f"  {choice.id}: {choice.text}")

    def _combat_action(self, action: str, module_id: str | None = None) -> None:
        try:
            for line in self.engine.combat_action(action, module_id):
                print(line)
            session = self.engine.active_combat
            if session is not None and not session.finished:
                print(
                    f"Your HP {self.engine.state.player.hp}; enemy HP {session.enemy_hp}; "
                    f"round {session.round_number}"
                )
        except ValueError as error:
            print(error)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run The Neverwildens starter shell")
    parser.add_argument("--content", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--load", type=Path, default=None)
    args = parser.parse_args()

    content = load_world(args.content or default_content_path())
    engine = (
        GameEngine.load(content, args.load)
        if args.load is not None
        else GameEngine.new_game(content, seed=args.seed)
    )
    NeverwildensShell(engine).cmdloop()

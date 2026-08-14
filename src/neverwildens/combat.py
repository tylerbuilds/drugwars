from __future__ import annotations

from dataclasses import dataclass, field

from .content import WorldContent
from .models import GameState
from .systems import deterministic_rng


@dataclass
class CombatSession:
    enemy_id: str
    enemy_hp: int
    round_number: int = 1
    defending: bool = False
    finished: bool = False
    won: bool = False
    log: list[str] = field(default_factory=list)


def start_combat(content: WorldContent, enemy_id: str) -> CombatSession:
    enemy = content.enemies[enemy_id]
    return CombatSession(enemy_id=enemy_id, enemy_hp=enemy.max_hp)


def resolve_round(
    content: WorldContent,
    state: GameState,
    session: CombatSession,
    action: str,
    module_id: str | None = None,
) -> list[str]:
    if session.finished:
        raise ValueError("Combat has already ended")

    enemy = content.enemies[session.enemy_id]
    messages: list[str] = []
    session.defending = False
    rng = deterministic_rng(
        state.seed,
        "combat",
        state.day,
        session.enemy_id,
        session.round_number,
        state.player.hp,
    )

    if action == "attack":
        damage = max(1, state.player.base_attack + rng.randint(-2, 3))
        session.enemy_hp -= damage
        messages.append(f"You strike {enemy.name} for {damage} damage.")
    elif action == "defend":
        session.defending = True
        messages.append("You brace for the counterattack.")
    elif action == "magic":
        if module_id is None or module_id not in state.player.equipped_modules:
            raise ValueError("That magic module is not equipped")
        module = content.magic_modules[module_id]
        if module.kind != "active":
            raise ValueError("Support modules cannot be cast directly")
        mp_cost = max(1, module.power // 2)
        if state.player.mp < mp_cost:
            raise ValueError("Not enough MP")
        state.player.mp -= mp_cost
        if module.effect == "damage":
            damage = module.power + rng.randint(0, 4)
            session.enemy_hp -= damage
            messages.append(f"{module.name} deals {damage} damage to {enemy.name}.")
            linked_supports = {
                linked
                for pair in state.player.module_links
                if module_id in pair
                for linked in pair
                if linked != module_id
            }
            if "siphon" in linked_supports:
                healing = max(1, damage // 3)
                state.player.hp = min(state.player.max_hp, state.player.hp + healing)
                messages.append(f"Siphon restores {healing} HP.")
        elif module.effect == "heal":
            healing = module.power + rng.randint(0, 4)
            state.player.hp = min(state.player.max_hp, state.player.hp + healing)
            messages.append(f"{module.name} restores {healing} HP.")
        elif module.effect == "ward":
            session.defending = True
            messages.append(f"{module.name} forms a protective ward.")
        else:
            raise ValueError(f"Unsupported active magic effect: {module.effect}")
    else:
        raise ValueError("Action must be attack, defend, or magic")

    if session.enemy_hp <= 0:
        session.enemy_hp = 0
        session.finished = True
        session.won = True
        state.player.cash += enemy.reward_cash
        messages.append(f"{enemy.name} falls. You recover {enemy.reward_cash} crowns.")
        session.log.extend(messages)
        return messages

    incoming = max(1, enemy.attack + rng.randint(-2, 2))
    if session.defending:
        incoming = max(1, incoming // 2)
    state.player.hp = max(0, state.player.hp - incoming)
    messages.append(f"{enemy.name} hits you for {incoming} damage.")
    if state.player.hp <= 0:
        session.finished = True
        session.won = False
        messages.append("You collapse. Defeat recovery is not yet implemented.")

    session.round_number += 1
    session.log.extend(messages)
    return messages

import random
import json
from sqlalchemy.orm import Session
from models.database import Duel, Player, DuelZenamon, ZenamonCache, Turn


def resolve_turn(duel: Duel, db: Session):
    turn = db.query(Turn).filter(Turn.duel_id == duel.id, Turn.turn_number == duel.current_turn).first()
    if not turn or turn.processed:
        return

    p1_action = json.loads(turn.p1_action) if turn.p1_action else {"type": "PASS"}
    p2_action = json.loads(turn.p2_action) if turn.p2_action else {"type": "PASS"}

    log = []

    p1_active = db.query(DuelZenamon).filter(
        DuelZenamon.duel_id == duel.id,
        DuelZenamon.player_id == duel.player1_id,
        DuelZenamon.is_active == True
    ).first()
    p2_active = db.query(DuelZenamon).filter(
        DuelZenamon.duel_id == duel.id,
        DuelZenamon.player_id == duel.player2_id,
        DuelZenamon.is_active == True
    ).first()

    actions = [
        {"player": 1, "player_id": duel.player1_id, "action": p1_action, "zenamon": p1_active},
        {"player": 2, "player_id": duel.player2_id, "action": p2_action, "zenamon": p2_active}
    ]

    # 1. Switch: ha priorita' e, dopo un KO, puo' essere l'unica azione del turno.
    for act in actions:
        if act["action"]["type"] == "SWITCH":
            new_pos = act["action"]["zenamon_index"]
            old_z = act["zenamon"]
            new_z = db.query(DuelZenamon).filter(
                DuelZenamon.duel_id == duel.id,
                DuelZenamon.player_id == act["player_id"],
                DuelZenamon.position == new_pos
            ).first()

            if old_z and new_z and not new_z.is_fainted and not new_z.is_active:
                old_z.is_active = False
                new_z.is_active = True
                z_cache = db.get(ZenamonCache, new_z.zenamon_id)
                player = db.get(Player, old_z.player_id)
                log.append(f"{player.nickname} ritira il suo Zenamon e manda in campo {z_cache.name}!")
                act["zenamon"] = new_z

    db.flush()

    # Sottofase 2: scontro tra i mostriciattoli in campo
    p1_active = actions[0]["zenamon"]
    p2_active = actions[1]["zenamon"]

    atk_actions = []
    for a in actions:
        if a["action"]["type"] == "ATTACK":
            atk_actions.append(a)
        elif a["action"]["type"] == "SWITCH" and a["action"].get("move_name"):
            atk_actions.append(a)

    def get_speed(dz):
        z_cache = db.get(ZenamonCache, dz.zenamon_id)
        return json.loads(z_cache.base_stats).get("speed", 0)

    atk_actions.sort(key=lambda x: get_speed(x["zenamon"]), reverse=True)

    if len(atk_actions) == 2:
        if get_speed(atk_actions[0]["zenamon"]) == get_speed(atk_actions[1]["zenamon"]):
            random.shuffle(atk_actions)

    for atk in atk_actions:
        attacker_dz = atk["zenamon"]
        defender_dz = p2_active if atk["player"] == 1 else p1_active

        if not attacker_dz or not defender_dz or attacker_dz.is_fainted or defender_dz.is_fainted:
            continue

        z_cache_atk = db.get(ZenamonCache, attacker_dz.zenamon_id)
        moves = json.loads(z_cache_atk.moves)
        move_name = atk["action"]["move_name"]
        move = next((m for m in moves if m["name"] == move_name), None)

        if not move:
            continue

        log.append(f"{z_cache_atk.name} usa {move['name']}!")

        atk_stat_name = "attack" if move["damage_class"] == "physical" else "special-attack"
        def_stat_name = "defense" if move["damage_class"] == "physical" else "special-defense"

        attacker_stats = json.loads(z_cache_atk.base_stats)
        z_cache_def = db.get(ZenamonCache, defender_dz.zenamon_id)
        defender_stats = json.loads(z_cache_def.base_stats)

        a_stat = attacker_stats.get(atk_stat_name, 50)
        d_stat = defender_stats.get(def_stat_name, 50)
        multiplier = 1.0

        damage = int((((((2 * 50 / 5) + 2) * move["power"] * a_stat / d_stat) / 50) + 2) * multiplier * random.uniform(0.85, 1.0))

        defender_dz.current_hp -= damage
        if defender_dz.current_hp <= 0:
            defender_dz.current_hp = 0
            defender_dz.is_fainted = True
            log.append(f"{z_cache_def.name} e' esausto!")
        else:
            log.append(f"{z_cache_def.name} subisce {damage} danni.")

    db.flush()

    def check_defeat(player_id):
        fainted_count = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == duel.id,
            DuelZenamon.player_id == player_id,
            DuelZenamon.is_fainted == True
        ).count()
        return fainted_count == 3

    if check_defeat(duel.player1_id):
        duel.status = "FINISHED"
        duel.winner_id = duel.player2_id
        log.append("Il duello e' terminato! Vincitore: " + db.get(Player, duel.player2_id).nickname)
    elif check_defeat(duel.player2_id):
        duel.status = "FINISHED"
        duel.winner_id = duel.player1_id
        log.append("Il duello e' terminato! Vincitore: " + db.get(Player, duel.player1_id).nickname)
    else:
        duel.current_turn += 1
        new_turn = Turn(duel_id=duel.id, turn_number=duel.current_turn)
        db.add(new_turn)

    turn.resolution_log = "\n".join(log)
    turn.processed = True
    db.commit()

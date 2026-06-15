import random
import json
from sqlalchemy.orm import Session
from .models.database import Duel, Player, DuelZenamon, ZenamonCache, Turn

def resolve_turn(duel: Duel, db: Session):
    turn = db.query(Turn).filter(Turn.duel_id == duel.id, Turn.turn_number == duel.current_turn).first()
    if not turn or turn.processed:
        return

    p1_action = json.loads(turn.p1_action)
    p2_action = json.loads(turn.p2_action)
    
    log = []
    
    # Recupero Zenamon attivi
    p1_active = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == duel.player1_id, DuelZenamon.is_active == True).first()
    p2_active = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == duel.player2_id, DuelZenamon.is_active == True).first()
    
    # Logica semplificata:
    # 1. Gestione Switch (priorità massima)
    # 2. Gestione Attacchi (in base alla velocità)
    
    actions = [
        {"player": 1, "action": p1_action, "zenamon": p1_active},
        {"player": 2, "action": p2_action, "zenamon": p2_active}
    ]
    
    # 1. Switch
    for act in actions:
        if act["action"]["type"] == "SWITCH":
            new_pos = act["action"]["zenamon_index"]
            old_z = act["zenamon"]
            new_z = db.query(DuelZenamon).filter(
                DuelZenamon.duel_id == duel.id, 
                DuelZenamon.player_id == duel.player1_id if act["player"] == 1 else duel.player2_id,
                DuelZenamon.position == new_pos
            ).first()
            
            if new_z and not new_z.is_fainted:
                old_z.is_active = False
                new_z.is_active = True
                z_cache = db.query(ZenamonCache).get(new_z.zenamon_id)
                player = db.query(Player).get(old_z.player_id)
                log.append(f"{player.nickname} ritira il suo Zenamon e manda in campo {z_cache.name}!")
                # Aggiorniamo il riferimento per l'attacco se necessario
                act["zenamon"] = new_z
    
    # Aggiorniamo riferimenti dopo switch
    p1_active = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == duel.player1_id, DuelZenamon.is_active == True).first()
    p2_active = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == duel.player2_id, DuelZenamon.is_active == True).first()

    # 2. Attacchi
    atk_actions = [a for a in actions if a["action"]["type"] == "ATTACK"]
    
    # Ordiniamo per velocità
    def get_speed(dz):
        z_cache = db.query(ZenamonCache).get(dz.zenamon_id)
        return json.loads(z_cache.base_stats).get("speed", 0)

    atk_actions.sort(key=lambda x: get_speed(x["zenamon"]), reverse=True)
    
    # Se velocità uguale, mischiamo
    if len(atk_actions) == 2:
        if get_speed(atk_actions[0]["zenamon"]) == get_speed(atk_actions[1]["zenamon"]):
            random.shuffle(atk_actions)

    for atk in atk_actions:
        attacker_dz = atk["zenamon"]
        defender_dz = p2_active if atk["player"] == 1 else p1_active
        
        if attacker_dz.is_fainted: continue # Se è andato KO prima di attaccare
        
        # Recupero dati mossa
        z_cache_atk = db.query(ZenamonCache).get(attacker_dz.zenamon_id)
        moves = json.loads(z_cache_atk.moves)
        move_name = atk["action"]["move_name"]
        move = next((m for m in moves if m["name"] == move_name), None)
        
        if not move: continue
        
        log.append(f"{z_cache_atk.name} usa {move['name']}!")
        
        # Calcolo Danno (Semplificato)
        # Danno = ((( ( (2 * 50 / 5) + 2 ) * Potenza * A / D ) / 50) + 2) * Moltiplicatore
        # A e D usiamo le stats base per ora
        atk_stat_name = "attack" if move["damage_class"] == "physical" else "special-attack"
        def_stat_name = "defense" if move["damage_class"] == "physical" else "special-defense"
        
        attacker_stats = json.loads(z_cache_atk.base_stats)
        z_cache_def = db.query(ZenamonCache).get(defender_dz.zenamon_id)
        defender_stats = json.loads(z_cache_def.base_stats)
        
        A = attacker_stats.get(atk_stat_name, 50)
        D = defender_stats.get(def_stat_name, 50)
        
        # Moltiplicatore Tipi (Semplificato: 1.0 per ora, da espandere)
        multiplier = 1.0
        
        damage = int((((( (2 * 50 / 5) + 2 ) * move["power"] * A / D ) / 50) + 2) * multiplier * (random.uniform(0.85, 1.0)))
        
        defender_dz.current_hp -= damage
        if defender_dz.current_hp <= 0:
            defender_dz.current_hp = 0
            defender_dz.is_fainted = True
            log.append(f"{z_cache_def.name} è esausto!")
        else:
            log.append(f"{z_cache_def.name} subisce {damage} danni.")
            
    # Verifica Fine Duello
    def check_defeat(player_id):
        fainted_count = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == player_id, DuelZenamon.is_fainted == True).count()
        return fainted_count == 3

    if check_defeat(duel.player1_id):
        duel.status = "FINISHED"
        duel.winner_id = duel.player2_id
        log.append("Il duello è terminato! Vincitore: " + db.query(Player).get(duel.player2_id).nickname)
    elif check_defeat(duel.player2_id):
        duel.status = "FINISHED"
        duel.winner_id = duel.player1_id
        log.append("Il duello è terminato! Vincitore: " + db.query(Player).get(duel.player1_id).nickname)
    else:
        # Turno successivo
        duel.current_turn += 1
        new_turn = Turn(duel_id=duel.id, turn_number=duel.current_turn)
        db.add(new_turn)

    turn.resolution_log = "\n".join(log)
    turn.processed = True
    db.commit()

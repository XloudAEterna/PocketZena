import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.models.database import Base, ZenamonCache, Duel, Player, DuelZenamon, Turn
from src.backend.battle_engine import resolve_turn

# Setup DB in memoria
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Setup Dati Base
    p1 = Player(id=1, nickname="P1", session_token="t1")
    p2 = Player(id=2, nickname="P2", session_token="t2")
    session.add_all([p1, p2])
    
    # Zenamon
    moves = json.dumps([
        {"name": "tackle", "power": 40, "type": "normal", "damage_class": "physical"}
    ])
    z1 = ZenamonCache(id=1, name="bulbasaur", types=json.dumps(["grass"]), 
                      base_stats=json.dumps({"hp": 45, "speed": 45, "attack": 49, "defense": 49}), 
                      moves=moves)
    z2 = ZenamonCache(id=4, name="charmander", types=json.dumps(["fire"]), 
                      base_stats=json.dumps({"hp": 39, "speed": 65, "attack": 52, "defense": 43}), 
                      moves=moves)
    session.add_all([z1, z2])
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_resolve_turn_attack(db):
    # Setup Duello
    duel = Duel(id="TEST", player1_id=1, player2_id=2, status="BATTLE", current_turn=1)
    db.add(duel)
    
    # Squadre
    dz1 = DuelZenamon(duel_id="TEST", player_id=1, zenamon_id=1, current_hp=45, position=1, is_active=True)
    dz2 = DuelZenamon(duel_id="TEST", player_id=2, zenamon_id=4, current_hp=39, position=1, is_active=True)
    db.add_all([dz1, dz2])
    
    # Turno
    turn = Turn(duel_id="TEST", turn_number=1, 
                p1_action=json.dumps({"type": "ATTACK", "move_name": "tackle"}),
                p2_action=json.dumps({"type": "ATTACK", "move_name": "tackle"}))
    db.add(turn)
    db.commit()
    
    # Esecuzione
    resolve_turn(duel, db)
    
    # Verifiche
    assert turn.processed is True
    assert turn.resolution_log != ""
    assert "bulbasaur usa tackle" in turn.resolution_log.lower()
    assert "charmander usa tackle" in turn.resolution_log.lower()
    
    # Almeno uno dei due deve aver perso HP
    assert dz1.current_hp < 45 or dz2.current_hp < 39
    assert duel.current_turn == 2

def test_resolve_turn_switch(db):
    # Setup Duello
    duel = Duel(id="SWITCH", player1_id=1, player2_id=2, status="BATTLE", current_turn=1)
    db.add(duel)
    
    # Squadra P1 (due Zenamon)
    dz1_a = DuelZenamon(duel_id="SWITCH", player_id=1, zenamon_id=1, current_hp=45, position=1, is_active=True)
    dz1_b = DuelZenamon(duel_id="SWITCH", player_id=1, zenamon_id=4, current_hp=39, position=2, is_active=False)
    
    # Squadra P2
    dz2 = DuelZenamon(duel_id="SWITCH", player_id=2, zenamon_id=4, current_hp=39, position=1, is_active=True)
    db.add_all([dz1_a, dz1_b, dz2])
    
    # Turno: P1 cambia Zenamon
    turn = Turn(duel_id="SWITCH", turn_number=1, 
                p1_action=json.dumps({"type": "SWITCH", "zenamon_index": 2}),
                p2_action=json.dumps({"type": "ATTACK", "move_name": "tackle"}))
    db.add(turn)
    db.commit()
    
    # Esecuzione
    resolve_turn(duel, db)
    
    # Verifiche
    assert dz1_a.is_active is False
    assert dz1_b.is_active is True
    assert "P1 ritira il suo Zenamon" in turn.resolution_log
    assert "manda in campo charmander" in turn.resolution_log

def test_resolve_turn_switch_and_attack(db):
    # Setup Duello
    duel = Duel(id="SWITCH_ATK", player1_id=1, player2_id=2, status="BATTLE", current_turn=1)
    db.add(duel)
    
    # Squadra P1
    dz1_a = DuelZenamon(duel_id="SWITCH_ATK", player_id=1, zenamon_id=1, current_hp=45, position=1, is_active=True)
    dz1_b = DuelZenamon(duel_id="SWITCH_ATK", player_id=1, zenamon_id=4, current_hp=39, position=2, is_active=False)
    
    # Squadra P2
    dz2 = DuelZenamon(duel_id="SWITCH_ATK", player_id=2, zenamon_id=4, current_hp=39, position=1, is_active=True)
    db.add_all([dz1_a, dz1_b, dz2])
    
    # Turno
    turn = Turn(duel_id="SWITCH_ATK", turn_number=1, 
                p1_action=json.dumps({"type": "SWITCH", "zenamon_index": 2, "move_name": "tackle"}),
                p2_action=json.dumps({"type": "ATTACK", "move_name": "tackle"}))
    db.add(turn)
    db.commit()
    
    # Esecuzione
    resolve_turn(duel, db)
    
    # Verifiche
    assert dz1_a.is_active is False
    assert dz1_b.is_active is True
    assert "P1 ritira il suo Zenamon" in turn.resolution_log
    assert "manda in campo charmander" in turn.resolution_log
    assert "charmander usa tackle" in turn.resolution_log.lower()
    # Verifica che il danno sia andato al nuovo mostriciattolo e non a quello ritirato
    assert dz1_a.current_hp == 45
    assert dz1_b.current_hp < 39

def test_resolve_turn_victory(db):
    # Setup Duello
    duel = Duel(id="VICTORY", player1_id=1, player2_id=2, status="BATTLE", current_turn=1)
    db.add(duel)
    
    # Squadre: P2 ha solo 1 HP
    dz1 = DuelZenamon(duel_id="VICTORY", player_id=1, zenamon_id=4, current_hp=39, position=1, is_active=True)
    dz2 = DuelZenamon(duel_id="VICTORY", player_id=2, zenamon_id=1, current_hp=1, position=1, is_active=True)
    # Altri mostriciattoli di P2 sono già esausti
    dz2_b = DuelZenamon(duel_id="VICTORY", player_id=2, zenamon_id=1, current_hp=0, position=2, is_active=False, is_fainted=True)
    dz2_c = DuelZenamon(duel_id="VICTORY", player_id=2, zenamon_id=1, current_hp=0, position=3, is_active=False, is_fainted=True)
    
    db.add_all([dz1, dz2, dz2_b, dz2_c])
    
    # Turno: P1 attacca (Charmander Speed 65) vs P2 (Bulbasaur Speed 45) -> P1 attacca per primo
    turn = Turn(duel_id="VICTORY", turn_number=1, 
                p1_action=json.dumps({"type": "ATTACK", "move_name": "tackle"}),
                p2_action=json.dumps({"type": "ATTACK", "move_name": "tackle"}))
    db.add(turn)
    db.commit()
    
    # Esecuzione
    resolve_turn(duel, db)
    
    # Verifiche
    assert dz2.is_fainted is True
    assert duel.status == "FINISHED"
    assert duel.winner_id == 1
    assert "vincitore: p1" in turn.resolution_log.lower()

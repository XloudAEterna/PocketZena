import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app, get_db
from backend.models.database import Base, ZenamonCache, DuelZenamon
import json

# Setup database per i test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_flow.sqlite3"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    # Pre-popoliamo la cache con alcuni Zenamon e mosse per i test
    db = TestingSessionLocal()
    moves = json.dumps([
        {"name": "tackle", "power": 40, "type": "normal", "damage_class": "physical"},
        {"name": "ember", "power": 40, "type": "fire", "damage_class": "special"}
    ])
    db.add(ZenamonCache(id=1, name="bulbasaur", types=json.dumps(["grass"]), base_stats=json.dumps({"hp": 45, "speed": 45, "attack": 49, "defense": 49}), moves=moves))
    db.add(ZenamonCache(id=4, name="charmander", types=json.dumps(["fire"]), base_stats=json.dumps({"hp": 39, "speed": 65, "attack": 52, "defense": 43}), moves=moves))
    db.add(ZenamonCache(id=7, name="squirtle", types=json.dumps(["water"]), base_stats=json.dumps({"hp": 44, "speed": 43, "attack": 48, "defense": 65}), moves=moves))
    db.add(ZenamonCache(id=25, name="pikachu", types=json.dumps(["electric"]), base_stats=json.dumps({"hp": 35, "speed": 90, "attack": 55, "defense": 40}), moves=moves))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_full_battle_flow(client):
    # 1. Preparazione
    p1 = client.post("/api/v1/players", json={"nickname": "AAA"}).json()
    p2 = client.post("/api/v1/players", json={"nickname": "BBB"}).json()
    token1, token2 = p1["token"], p2["token"]
    duel = client.post("/api/v1/duels", headers={"X-Session-Token": token1}).json()
    code = duel["duel_code"]
    client.post(f"/api/v1/duels/{code}/join", headers={"X-Session-Token": token2})
    client.post(f"/api/v1/duels/{code}/team", headers={"X-Session-Token": token1}, json={"zenamon_ids": [1, 4, 25]})
    client.post(f"/api/v1/duels/{code}/team", headers={"X-Session-Token": token2}, json={"zenamon_ids": [7, 1, 4]})

    # 2. Inizio Battaglia - Turno 1
    status = client.get(f"/api/v1/duels/{code}/status").json()
    assert status["status"] == "BATTLE"
    assert status["current_turn"] == 1
    assert status["player1"]["active_zenamon_name"] == "bulbasaur"
    assert status["player2"]["active_zenamon_name"] == "squirtle"

    # 3. Invio Azioni (P1 attacca, P2 attacca)
    # Bulbasaur (Speed 45) vs Squirtle (Speed 43) -> Bulbasaur dovrebbe attaccare per primo
    res1 = client.post(f"/api/v1/duels/{code}/action", 
                       headers={"X-Session-Token": token1},
                       json={"type": "ATTACK", "move_name": "tackle"})
    assert res1.status_code == 200
    
    # Verifica che P1 sia pronto
    status = client.get(f"/api/v1/duels/{code}/status").json()
    assert status["player1"]["is_ready"] is True
    assert status["player2"]["is_ready"] is False

    res2 = client.post(f"/api/v1/duels/{code}/action", 
                       headers={"X-Session-Token": token2},
                       json={"type": "ATTACK", "move_name": "tackle"})
    assert res2.status_code == 200

    # 4. Verifica Risoluzione Turno
    status = client.get(f"/api/v1/duels/{code}/status").json()
    assert status["current_turn"] == 2
    assert len(status["new_events"]) > 0
    # Almeno uno Zenamon deve aver perso HP
    assert status["player1"]["active_zenamon_hp"] < status["player1"]["active_zenamon_max_hp"] or \
           status["player2"]["active_zenamon_hp"] < status["player2"]["active_zenamon_max_hp"]

def test_switch_action(client):
    # 1. Preparazione (come sopra)
    p1 = client.post("/api/v1/players", json={"nickname": "AAA"}).json()
    p2 = client.post("/api/v1/players", json={"nickname": "BBB"}).json()
    token1, token2 = p1["token"], p2["token"]
    duel = client.post("/api/v1/duels", headers={"X-Session-Token": token1}).json()
    code = duel["duel_code"]
    client.post(f"/api/v1/duels/{code}/join", headers={"X-Session-Token": token2})
    client.post(f"/api/v1/duels/{code}/team", headers={"X-Session-Token": token1}, json={"zenamon_ids": [1, 4, 25]})
    client.post(f"/api/v1/duels/{code}/team", headers={"X-Session-Token": token2}, json={"zenamon_ids": [7, 1, 4]})

    # 2. Switch P1 (cambia Bulbasaur con Charmander - posizione 2)
    client.post(f"/api/v1/duels/{code}/action", 
                headers={"X-Session-Token": token1},
                json={"type": "SWITCH", "zenamon_index": 2})
    
    # P2 attacca
    client.post(f"/api/v1/duels/{code}/action", 
                headers={"X-Session-Token": token2},
                json={"type": "ATTACK", "move_name": "tackle"})
    
    # 3. Verifica Switch
    status = client.get(f"/api/v1/duels/{code}/status").json()
    assert status["player1"]["active_zenamon_name"] == "charmander"

def test_fainted_active_forces_immediate_switch(client):
    p1 = client.post("/api/v1/players", json={"nickname": "AAA"}).json()
    p2 = client.post("/api/v1/players", json={"nickname": "BBB"}).json()
    token1, token2 = p1["token"], p2["token"]
    duel = client.post("/api/v1/duels", headers={"X-Session-Token": token1}).json()
    code = duel["duel_code"]
    client.post(f"/api/v1/duels/{code}/join", headers={"X-Session-Token": token2})
    client.post(f"/api/v1/duels/{code}/team", headers={"X-Session-Token": token1}, json={"zenamon_ids": [25, 4, 1]})
    client.post(f"/api/v1/duels/{code}/team", headers={"X-Session-Token": token2}, json={"zenamon_ids": [1, 7, 4]})

    db = TestingSessionLocal()
    try:
        p2_active = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == code,
            DuelZenamon.player_id == p2["id"],
            DuelZenamon.is_active == True
        ).first()
        p2_active.current_hp = 1
        db.commit()
    finally:
        db.close()

    res1 = client.post(
        f"/api/v1/duels/{code}/action",
        headers={"X-Session-Token": token1},
        json={"type": "ATTACK", "move_name": "tackle"}
    )
    assert res1.status_code == 200

    res2 = client.post(
        f"/api/v1/duels/{code}/action",
        headers={"X-Session-Token": token2},
        json={"type": "ATTACK", "move_name": "tackle"}
    )
    assert res2.status_code == 200

    status = client.get(f"/api/v1/duels/{code}/status").json()
    assert status["status"] == "BATTLE"
    assert status["player2"]["active_zenamon_is_fainted"] is True
    assert status["player2"]["active_zenamon_hp"] == 0

    blocked_attack = client.post(
        f"/api/v1/duels/{code}/action",
        headers={"X-Session-Token": token1},
        json={"type": "ATTACK", "move_name": "tackle"}
    )
    assert blocked_attack.status_code == 400

    invalid_fainted_attack = client.post(
        f"/api/v1/duels/{code}/action",
        headers={"X-Session-Token": token2},
        json={"type": "ATTACK", "move_name": "tackle"}
    )
    assert invalid_fainted_attack.status_code == 400

    switch = client.post(
        f"/api/v1/duels/{code}/action",
        headers={"X-Session-Token": token2},
        json={"type": "SWITCH", "zenamon_index": 2}
    )
    assert switch.status_code == 200

    status = client.get(f"/api/v1/duels/{code}/status").json()
    assert status["current_turn"] == 3
    assert status["player2"]["active_zenamon_name"] == "squirtle"
    assert status["player2"]["active_zenamon_is_fainted"] is False

def test_full_preparation_flow(client):
    # 1. Registrazione Giocatori
    p1 = client.post("/api/v1/players", json={"nickname": "AAA"}).json()
    p2 = client.post("/api/v1/players", json={"nickname": "BBB"}).json()
    token1, token2 = p1["token"], p2["token"]

    # 2. Creazione Duello
    duel = client.post("/api/v1/duels", headers={"X-Session-Token": token1}).json()
    code = duel["duel_code"]

    # 3. Join
    client.post(f"/api/v1/duels/{code}/join", headers={"X-Session-Token": token2})

    # 4. Selezione Squadra P1
    res1 = client.post(f"/api/v1/duels/{code}/team", 
                       headers={"X-Session-Token": token1},
                       json={"zenamon_ids": [1, 4, 25]})
    assert res1.status_code == 200
    assert res1.json()["status"] == "READY"

    # 5. Selezione Squadra P2
    res2 = client.post(f"/api/v1/duels/{code}/team", 
                       headers={"X-Session-Token": token2},
                       json={"zenamon_ids": [7, 1, 4]})
    assert res2.status_code == 200
    # Ora dovrebbe essere in fase BATTLE
    assert res2.json()["status"] == "BATTLE"

def test_set_team_invalid_count(client):
    p1 = client.post("/api/v1/players", json={"nickname": "AAA"}).json()
    token = p1["token"]
    duel = client.post("/api/v1/duels", headers={"X-Session-Token": token}).json()
    code = duel["duel_code"]
    client.post(f"/api/v1/duels/{code}/join", headers={"X-Session-Token": token}) # Join se stesso (status cambia in SELECTION)

    res = client.post(f"/api/v1/duels/{code}/team", 
                       headers={"X-Session-Token": token},
                       json={"zenamon_ids": [1, 4]}) # Solo 2
    assert res.status_code == 400

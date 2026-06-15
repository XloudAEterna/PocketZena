import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app, get_db
from backend.models.database import Base, Player, Duel, ZenamonCache, Turn, Reaction, DuelZenamon

# Setup database per i test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rooms.sqlite3"
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
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_player(client):
    response = client.post("/api/v1/players", json={"nickname": "AAA"})
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "AAA"
    assert "token" in data

def test_create_player_invalid_nickname(client):
    response = client.post("/api/v1/players", json={"nickname": "aa"}) # Troppo corto
    assert response.status_code == 422
    response = client.post("/api/v1/players", json={"nickname": "ABCDEFGHIJK"}) # Troppo lungo
    assert response.status_code == 422

def test_create_duel(client):
    # Prima crea un giocatore
    res_player = client.post("/api/v1/players", json={"nickname": "PLA"})
    assert res_player.status_code == 200, res_player.json()
    token = res_player.json()["token"]
    
    # Crea duello
    response = client.post("/api/v1/duels", headers={"X-Session-Token": token})
    assert response.status_code == 200
    data = response.json()
    assert "duel_code" in data
    assert data["status"] == "WAITING"

def test_join_duel(client):
    # Crea Giocatore 1
    res_p1 = client.post("/api/v1/players", json={"nickname": "PBA"})
    token1 = res_p1.json()["token"]
    
    # Crea duello
    res_duel = client.post("/api/v1/duels", headers={"X-Session-Token": token1})
    duel_code = res_duel.json()["duel_code"]
    
    # Crea Giocatore 2
    res_p2 = client.post("/api/v1/players", json={"nickname": "PBB"})
    token2 = res_p2.json()["token"]
    
    # Join duello
    response = client.post(f"/api/v1/duels/{duel_code}/join", headers={"X-Session-Token": token2})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "SELECTION"

def test_join_duel_not_found(client):
    res_p1 = client.post("/api/v1/players", json={"nickname": "PCA"})
    token1 = res_p1.json()["token"]
    
    response = client.post("/api/v1/duels/NONO/join", headers={"X-Session-Token": token1})
    assert response.status_code == 404

def test_spectate_duel(client):
    # Crea Giocatore 1
    res_p1 = client.post("/api/v1/players", json={"nickname": "PDA"})
    token1 = res_p1.json()["token"]
    
    # Crea duello
    res_duel = client.post("/api/v1/duels", headers={"X-Session-Token": token1})
    duel_code = res_duel.json()["duel_code"]
    
    # Spettatore
    res_spectator = client.post("/api/v1/players", json={"nickname": "SPE"})
    token_spec = res_spectator.json()["token"]
    
    response = client.post(f"/api/v1/duels/{duel_code}/spectate", headers={"X-Session-Token": token_spec})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["role"] == "SPECTATOR"

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base, ZenamonCache
from backend.pokeapi_client import get_zenamon_data
import httpx

# Setup database in memoria per i test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_get_zenamon_data_from_api_and_cache(db_session):
    """Test che verifica il recupero da PokeAPI e il salvataggio in cache."""
    mock_data = {
        "id": 25,
        "name": "pikachu",
        "sprites": {"front_default": "http://example.com/sprite.png"},
        "types": [{"type": {"name": "electric"}}],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 35},
            {"stat": {"name": "attack"}, "base_stat": 55}
        ],
        "moves": []
    }
    
    # Mockiamo l'AsyncClient e la risposta
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock() # Non asincrono
        mock_get.return_value = mock_response
        
        # Esecuzione (Pikachu non è in cache)
        result = await get_zenamon_data("pikachu", db_session)
        
        # Verifiche
        assert result is not None
        assert result["id"] == 25
        assert result["name"] == "pikachu"
        assert "electric" in result["types"]
        assert result["base_stats"]["hp"] == 35
        
        # Verifica che sia stato salvato in cache (database)
        cached = db_session.query(ZenamonCache).filter_by(id=25).first()
        assert cached is not None
        assert cached.name == "pikachu"
        assert "electric" in json.loads(cached.types)

@pytest.mark.asyncio
async def test_get_zenamon_data_from_cache(db_session):
    """Test che verifica il recupero diretto dalla cache senza chiamare l'API."""
    # Prepariamo la cache manualmente
    new_zenamon = ZenamonCache(
        id=1,
        name="bulbasaur",
        sprite_url="http://example.com/b.png",
        types=json.dumps(["grass", "poison"]),
        base_stats=json.dumps({"hp": 45, "attack": 49})
    )
    db_session.add(new_zenamon)
    db_session.commit()
    
    # In questo caso NON dovrebbe esserci nessuna chiamata a httpx.AsyncClient.get
    with patch("httpx.AsyncClient.get") as mock_get:
        result = await get_zenamon_data("bulbasaur", db_session)
        
        assert result["id"] == 1
        assert result["name"] == "bulbasaur"
        assert "grass" in result["types"]
        # Verifichiamo che l'API non sia stata chiamata
        mock_get.assert_not_called()

@pytest.mark.asyncio
async def test_get_zenamon_data_not_found(db_session):
    """Test che verifica la gestione del 404 da PokeAPI."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        # Simuliamo raise_for_status che solleva un'eccezione (metodo sincrono)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response
        
        result = await get_zenamon_data("unknown_zenamon", db_session)
        assert result is None

@pytest.mark.asyncio
async def test_get_zenamon_data_by_id(db_session):
    """Test che verifica la ricerca tramite ID numerico."""
    mock_data = {
        "id": 4,
        "name": "charmander",
        "sprites": {"front_default": "http://example.com/c.png"},
        "types": [{"type": {"name": "fire"}}],
        "stats": [{"stat": {"name": "hp"}, "base_stat": 39}],
        "moves": []
    }
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Cerchiamo tramite stringa numerica "4"
        result = await get_zenamon_data("4", db_session)
        assert result is not None
        assert result["id"] == 4
        assert result["name"] == "charmander"

@pytest.mark.asyncio
async def test_get_zenamon_data_api_error(db_session):
    """Test che verifica la gestione di un errore generico dell'API."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Connessione fallita")
        
        result = await get_zenamon_data("pikachu", db_session)
        assert result is None

import httpx
import json
import asyncio
from sqlalchemy.orm import Session
from .models.database import ZenamonCache
from sqlalchemy import or_

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

# Cache in memoria per la lista dei nomi per supportare la ricerca parziale
_ZENAMON_NAMES_CACHE = []
_CACHE_LOCK = asyncio.Lock()

async def _get_all_names():
    global _ZENAMON_NAMES_CACHE
    if _ZENAMON_NAMES_CACHE:
        return _ZENAMON_NAMES_CACHE
    
    async with _CACHE_LOCK:
        if _ZENAMON_NAMES_CACHE:
            return _ZENAMON_NAMES_CACHE
        
        async with httpx.AsyncClient() as client:
            try:
                # Recuperiamo tutti i nomi (circa 1300 attualmente)
                response = await client.get(f"{POKEAPI_BASE_URL}/pokemon?limit=2000")
                if response.status_code == 200:
                    data = response.json()
                    _ZENAMON_NAMES_CACHE = [r["name"] for r in data["results"]]
            except Exception as e:
                print(f"Errore nel recupero della lista nomi da PokeAPI: {e}")
    
    return _ZENAMON_NAMES_CACHE

async def search_zenamon_names(query: str, limit: int = 10):
    query = query.lower().strip()
    if not query:
        return []
    
    all_names = await _get_all_names()
    
    # Priorità: 1. Inizia con, 2. Contiene
    matches = [n for n in all_names if n.startswith(query)]
    if len(matches) < limit:
        contains = [n for n in all_names if query in n and n not in matches]
        matches.extend(contains)
    
    return matches[:limit]

async def get_zenamon_basic_data(name: str, db: Session):
    """Versione leggera di get_zenamon_data che non recupera le mosse se non necessario."""
    cached = db.query(ZenamonCache).filter(ZenamonCache.name == name).first()
    if cached:
        return {
            "id": cached.id,
            "name": cached.name,
            "sprite_url": cached.sprite_url,
            "types": json.loads(cached.types)
        }
    
    # Se non in cache, recuperiamo solo i dati base da PokeAPI
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{POKEAPI_BASE_URL}/pokemon/{name}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data["id"],
                    "name": data["name"],
                    "sprite_url": data["sprites"]["front_default"],
                    "types": [t["type"]["name"] for t in data["types"]]
                }
        except:
            pass
    return {"name": name}

async def get_zenamon_data(zenamon_name_or_id: str, db: Session):
    # 1. Pulizia input
    zenamon_name_or_id = str(zenamon_name_or_id).lower().strip()
    
    if not zenamon_name_or_id:
        return None
    
    # 2. Se non è un ID, proviamo a risolvere il nome parziale
    is_id = zenamon_name_or_id.isdigit()
    
    if not is_id:
        # 1. Cerchiamo un match esatto (in cache o nella lista completa)
        exact_cached = db.query(ZenamonCache).filter(ZenamonCache.name == zenamon_name_or_id).first()
        if exact_cached:
            zenamon_name_or_id = exact_cached.name
        else:
            all_names = await _get_all_names()
            if zenamon_name_or_id in all_names:
                # È un nome esatto, non facciamo nulla e proseguiamo
                pass
            else:
                # 2. Se non è un match esatto, cerchiamo un match parziale
                # Prima in cache locale
                partial_cached = db.query(ZenamonCache).filter(ZenamonCache.name.like(f"{zenamon_name_or_id}%")).first()
                if partial_cached:
                    zenamon_name_or_id = partial_cached.name
                else:
                    # Poi nella lista completa
                    match = next((n for n in all_names if n.startswith(zenamon_name_or_id)), None)
                    if not match:
                        match = next((n for n in all_names if zenamon_name_or_id in n), None)
                    
                    if match:
                        zenamon_name_or_id = match

    # 3. Controlla in cache locale (DB) con il nome risolto (o ID)
    if is_id:
        cached = db.query(ZenamonCache).filter(ZenamonCache.id == int(zenamon_name_or_id)).first()
    else:
        cached = db.query(ZenamonCache).filter(ZenamonCache.name == zenamon_name_or_id).first()
        
    if cached:
        return {
            "id": cached.id,
            "name": cached.name,
            "sprite_url": cached.sprite_url,
            "types": json.loads(cached.types),
            "base_stats": json.loads(cached.base_stats),
            "moves": json.loads(cached.moves) if cached.moves else []
        }

    # 2. Se non in cache, chiama PokeAPI
    # Usiamo un timeout più lungo per il recupero delle mosse
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.get(f"{POKEAPI_BASE_URL}/pokemon/{zenamon_name_or_id}")
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Estraiamo i dati necessari
            zenamon_id = data["id"]
            name = data["name"]
            sprite_url = data["sprites"]["front_default"]
            types = [t["type"]["name"] for t in data["types"]]
            stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
            
            # Recupero delle prime 4 mosse che hanno potenza
            # Ottimizzazione: cerchiamo di recuperare le mosse in parallelo o limitiamo la ricerca
            moves = []
            possible_moves = data["moves"]
            
            # Filtriamo le mosse per cercare quelle che probabilmente hanno potenza (evitando troppe chiamate)
            # Spesso le prime mosse sono di stato.
            
            async def get_move_details(m_url):
                try:
                    m_res = await client.get(m_url)
                    if m_res.status_code == 200:
                        m_data = m_res.json()
                        if m_data.get("power"):
                            return {
                                "name": m_data["name"],
                                "power": m_data["power"],
                                "type": m_data["type"]["name"],
                                "damage_class": m_data["damage_class"]["name"]
                            }
                except:
                    pass
                return None

            # Proviamo a controllare le prime 20 mosse per trovarne 4 con potenza
            tasks = []
            for m in possible_moves[:20]:
                tasks.append(get_move_details(m["move"]["url"]))
            
            results = await asyncio.gather(*tasks)
            moves = [r for r in results if r is not None][:4]
            
            # Se ha meno di 4 mosse con potenza, ne prendiamo alcune anche senza potenza per riempire
            if len(moves) < 4:
                for m in possible_moves:
                    if len(moves) >= 4: break
                    if any(existing["name"] == m["move"]["name"] for existing in moves): continue
                    moves.append({
                        "name": m["move"]["name"],
                        "power": 0,
                        "type": "normal",
                        "damage_class": "status"
                    })
            
            # Se ha meno di 4 mosse con potenza, pazienza, ma solitamente ne hanno molte.

            # 3. Salva in cache
            new_zenamon = ZenamonCache(
                id=zenamon_id,
                name=name,
                sprite_url=sprite_url,
                types=json.dumps(types),
                base_stats=json.dumps(stats),
                moves=json.dumps(moves)
            )
            db.add(new_zenamon)
            db.commit()
            db.refresh(new_zenamon)
            
            return {
                "id": zenamon_id,
                "name": name,
                "sprite_url": sprite_url,
                "types": types,
                "base_stats": stats,
                "moves": moves
            }
        except httpx.HTTPStatusError:
            return None
        except Exception as e:
            print(f"Errore durante la chiamata a PokeAPI: {e}")
            return None

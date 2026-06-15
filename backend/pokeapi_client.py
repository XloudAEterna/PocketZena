import httpx
import json
import asyncio
from sqlalchemy.orm import Session
from .models.database import ZenamonCache

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

async def get_zenamon_data(zenamon_name_or_id: str, db: Session):
    # 1. Controlla in cache locale (DB)
    zenamon_name_or_id = str(zenamon_name_or_id).lower().strip()
    
    if not zenamon_name_or_id:
        return None
    
    # Cerchiamo per nome o per ID
    if zenamon_name_or_id.isdigit():
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

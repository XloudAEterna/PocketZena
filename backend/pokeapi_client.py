import httpx
import json
from sqlalchemy.orm import Session
from .models.database import ZenamonCache

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

async def get_zenamon_data(zenamon_name_or_id: str, db: Session):
    # 1. Controlla in cache locale (DB)
    zenamon_name_or_id = str(zenamon_name_or_id).lower()
    
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
            "base_stats": json.loads(cached.base_stats)
        }

    # 2. Se non in cache, chiama PokeAPI
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{POKEAPI_BASE_URL}/pokemon/{zenamon_name_or_id}")
            response.raise_for_status()
            data = response.json()
            
            # Estraiamo i dati necessari
            zenamon_id = data["id"]
            name = data["name"]
            sprite_url = data["sprites"]["front_default"]
            types = [t["type"]["name"] for t in data["types"]]
            stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
            
            # 3. Salva in cache
            new_zenamon = ZenamonCache(
                id=zenamon_id,
                name=name,
                sprite_url=sprite_url,
                types=json.dumps(types),
                base_stats=json.dumps(stats)
            )
            db.add(new_zenamon)
            db.commit()
            db.refresh(new_zenamon)
            
            return {
                "id": zenamon_id,
                "name": name,
                "sprite_url": sprite_url,
                "types": types,
                "base_stats": stats
            }
        except httpx.HTTPStatusError:
            return None
        except Exception as e:
            print(f"Errore durante la chiamata a PokeAPI: {e}")
            return None

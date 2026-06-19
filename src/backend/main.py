import uuid
import random
import string
import json
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

from models.database import SessionLocal, engine, Base, Player, Duel, ZenamonCache, DuelZenamon, Turn, Reaction, init_db
from schemas.player import PlayerCreate, PlayerResponse
from schemas.duel import DuelCreateResponse, DuelJoinResponse, DuelSpectateResponse
from schemas.zenamon import ZenamonResponse, TeamCreate, ZenamonSearchResult
from schemas.battle import BattleStatusResponse, PlayerBattleStatus, BattleAction, ReactionCreate
from pokeapi_client import get_zenamon_data, search_zenamon_names, get_zenamon_basic_data
from battle_engine import resolve_turn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Evento di startup per inizializzare il DB in modo asincrono rispetto all'importazione
    # Utile per ambienti ASGI (come uvicorn locale)
    import time
    start = time.time()
    if os.environ.get("SKIP_DB_INIT") != "1":
        print("STARTUP: Inizializzazione database via Lifespan...")
        try:
            init_db()
            print(f"STARTUP: Database inizializzato in {time.time() - start:.2f} secondi.")
        except Exception as e:
            print(f"CRITICAL ERROR durante lo startup: {e}")
    yield

app = FastAPI(title="POCKET-ZENA API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestore eccezioni globale per catturare errori 500 e garantire risposte JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"GLOBAL ERROR: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Errore interno del server", "message": str(exc)},
    )

# Configurazione CORS ottimizzata per produzione
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Dependency per il database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper per generare codice stanza
def generate_duel_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

# Helper per ottenere il giocatore dal token
async def get_current_player(x_session_token: str = Header(...), db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.session_token == x_session_token).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessione non valida"
        )
    return player

@app.post("/api/v1/players", response_model=PlayerResponse)
async def create_player(player_in: PlayerCreate, db: Session = Depends(get_db)):
    session_token = str(uuid.uuid4())
    new_player = Player(
        nickname=player_in.nickname,
        session_token=session_token
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return {
        "id": new_player.id,
        "nickname": new_player.nickname,
        "token": new_player.session_token
    }

@app.post("/api/v1/duels", response_model=DuelCreateResponse)
async def create_duel(current_player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    # Genera un codice univoco
    duel_code = generate_duel_code()
    while db.query(Duel).filter(Duel.id == duel_code).first():
        duel_code = generate_duel_code()
    
    new_duel = Duel(
        id=duel_code,
        player1_id=current_player.id,
        status="WAITING"
    )
    db.add(new_duel)
    db.commit()
    
    return {
        "duel_code": new_duel.id,
        "status": new_duel.status
    }

@app.post("/api/v1/duels/{code}/join", response_model=DuelJoinResponse)
async def join_duel(code: str, current_player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    duel = db.query(Duel).filter(Duel.id == code.upper()).first()
    
    if not duel:
        raise HTTPException(status_code=404, detail="Duello non trovato")
    
    if duel.player1_id == current_player.id:
        # Se è lo stesso giocatore, consideriamo che sia già dentro
        return {
            "success": True,
            "status": duel.status
        }
    
    if duel.player2_id is not None and duel.player2_id != current_player.id:
        raise HTTPException(status_code=400, detail="Duello già al completo")
    
    if duel.status != "WAITING":
         raise HTTPException(status_code=400, detail="Duello già iniziato")

    duel.player2_id = current_player.id
    duel.status = "SELECTION"
    db.commit()
    
    return {
        "success": True,
        "status": duel.status
    }

@app.post("/api/v1/duels/{code}/spectate", response_model=DuelSpectateResponse)
async def spectate_duel(code: str, current_player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    duel = db.query(Duel).filter(Duel.id == code.upper()).first()
    
    if not duel:
        raise HTTPException(status_code=404, detail="Duello non trovato")
    
    # Gli spettatori non cambiano lo stato del duello, ma verifichiamo che il giocatore esista
    return {
        "success": True,
        "role": "SPECTATOR"
    }

@app.get("/api/v1/zenamon/search", response_model=ZenamonSearchResult)
async def search_zenamon(name: str, db: Session = Depends(get_db)):
    query = name.strip()
    if query.isdigit():
        result = await get_zenamon_basic_data(query, db)
        if not result:
            return {"results": []}

        return {"results": [{
            "id": result.get("id"),
            "name": result["name"],
            "types": result.get("types"),
            "sprite": result.get("sprite_url")
        }]}

    names = await search_zenamon_names(query)
    if not names:
        return {"results": []}
    
    # Carichiamo i dati base per tutti i nomi trovati in sequenza (per sicurezza della sessione DB)
    results = []
    for n in names:
        res = await get_zenamon_basic_data(n, db)
        results.append(res)
    
    formatted_results = []
    for r in results:
        formatted_results.append({
            "id": r.get("id"),
            "name": r["name"],
            "types": r.get("types"),
            "sprite": r.get("sprite_url")
        })
    
    return {"results": formatted_results}

@app.get("/api/v1/zenamon/{name_or_id}", response_model=ZenamonResponse)
async def get_zenamon_details(name_or_id: str, db: Session = Depends(get_db)):
    data = await get_zenamon_data(name_or_id, db)
    if not data:
        raise HTTPException(status_code=404, detail="Zenamon non trovato")
    
    return {
        "id": data["id"],
        "name": data["name"],
        "types": data["types"],
        "sprite": data["sprite_url"],
        "moves": data["moves"]
    }

@app.post("/api/v1/duels/{code}/team")
async def set_team(code: str, team_in: TeamCreate, current_player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    duel = db.query(Duel).filter(Duel.id == code.upper()).first()
    if not duel:
        raise HTTPException(status_code=404, detail="Duello non trovato")
    
    if duel.player1_id != current_player.id and duel.player2_id != current_player.id:
        raise HTTPException(status_code=403, detail="Non partecipi a questo duello")
    
    if duel.status != "SELECTION":
        raise HTTPException(status_code=400, detail="Fase di selezione terminata o non ancora iniziata")
    
    if len(team_in.zenamon_ids) != 3:
        raise HTTPException(status_code=400, detail="Devi selezionare esattamente 3 Zenamon")
    
    # Verifica se ha già inviato la squadra
    existing_team = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == current_player.id).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Squadra già inviata")
    
    # 1. Assicuriamoci che tutti gli Zenamon siano in cache (caricamento seriale per sicurezza sessione DB)
    for z_id in team_in.zenamon_ids:
        await get_zenamon_data(str(z_id), db)
    
    # 2. Ora procediamo con l'aggiunta alla squadra nel duello
    for i, z_id in enumerate(team_in.zenamon_ids):
        z_cache = db.query(ZenamonCache).filter(ZenamonCache.id == z_id).first()
        if not z_cache:
            # Non dovrebbe succedere dopo il gather sopra, ma per sicurezza:
            raise HTTPException(status_code=404, detail=f"Zenamon con ID {z_id} non trovato")

        stats = json.loads(z_cache.base_stats)
        hp = stats.get("hp", 100) # Fallback
        
        new_dz = DuelZenamon(
            duel_id=duel.id,
            player_id=current_player.id,
            zenamon_id=z_cache.id,
            current_hp=hp,
            position=i + 1,
            is_active=(i == 0) # Il primo è attivo
        )
        db.add(new_dz)
    
    db.commit()
    
    # Controlliamo se entrambi hanno inviato la squadra per passare alla fase BATTLE
    p1_team_count = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == duel.player1_id).count()
    p2_team_count = db.query(DuelZenamon).filter(DuelZenamon.duel_id == duel.id, DuelZenamon.player_id == duel.player2_id).count()
    
    if p1_team_count == 3 and p2_team_count == 3:
        duel.status = "BATTLE"
        duel.current_turn = 1
        # Inizializziamo il primo turno
        new_turn = Turn(duel_id=duel.id, turn_number=1)
        db.add(new_turn)
        db.commit()
    
    return {"status": "READY" if duel.status == "SELECTION" else duel.status}

@app.get("/api/v1/duels/{code}/status", response_model=BattleStatusResponse)
async def get_duel_status(code: str, db: Session = Depends(get_db)):
    duel = db.query(Duel).filter(Duel.id == code.upper()).first()
    if not duel:
        raise HTTPException(status_code=404, detail="Duello non trovato")
    
    p1 = db.get(Player, duel.player1_id)
    p2 = db.get(Player, duel.player2_id) if duel.player2_id else None
    
    # Dati Zenamon Attivi
    def get_team_info(player_id):
        if not player_id:
            return []

        team = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == duel.id,
            DuelZenamon.player_id == player_id
        ).order_by(DuelZenamon.position).all()

        result = []
        for dz in team:
            z_cache = db.get(ZenamonCache, dz.zenamon_id)
            max_hp = json.loads(z_cache.base_stats).get("hp", 100)
            result.append({
                "position": dz.position,
                "name": z_cache.name,
                "current_hp": dz.current_hp,
                "max_hp": max_hp,
                "is_active": dz.is_active,
                "is_fainted": dz.is_fainted
            })
        return result

    def get_active_info(player_id):
        if not player_id: return None, None, None, None, False
        active = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == duel.id, 
            DuelZenamon.player_id == player_id,
            DuelZenamon.is_active == True
        ).first()
        if not active: return None, None, None, None, False
        z_cache = db.get(ZenamonCache, active.zenamon_id)
        max_hp = json.loads(z_cache.base_stats).get("hp", 100)
        return z_cache.name, active.current_hp, max_hp, z_cache.sprite_url, active.is_fainted

    p1_z_name, p1_z_hp, p1_z_max, p1_z_sprite, p1_z_fainted = get_active_info(duel.player1_id)
    p2_z_name, p2_z_hp, p2_z_max, p2_z_sprite, p2_z_fainted = get_active_info(duel.player2_id)
    p1_team = get_team_info(duel.player1_id)
    p2_team = get_team_info(duel.player2_id)
    
    # Verifica se i giocatori sono pronti per il turno corrente
    turn = db.query(Turn).filter(Turn.duel_id == duel.id, Turn.turn_number == duel.current_turn).first()
    p1_ready = turn.p1_action is not None if turn else False
    p2_ready = turn.p2_action is not None if turn else False
    
    # Eventi (Log del turno precedente o corrente se processato)
    events = []
    last_processed_turn = db.query(Turn).filter(
        Turn.duel_id == duel.id, 
        Turn.processed == True
    ).order_by(Turn.turn_number.desc()).first()
    
    if last_processed_turn and last_processed_turn.resolution_log:
        events = last_processed_turn.resolution_log.split("\n")
    
    # Reazioni
    reactions = db.query(Reaction).filter(Reaction.duel_id == duel.id).order_by(Reaction.created_at.desc()).limit(5).all()
    reaction_list = [{"id": r.id, "emoji": r.emoji} for r in reversed(reactions)]
    
    winner = db.get(Player, duel.winner_id) if duel.winner_id else None

    return {
        "status": duel.status,
        "current_turn": duel.current_turn,
        "player1": {
            "nickname": p1.nickname,
            "active_zenamon_name": p1_z_name,
            "active_zenamon_hp": p1_z_hp,
            "active_zenamon_max_hp": p1_z_max,
            "active_zenamon_sprite": p1_z_sprite,
            "active_zenamon_is_fainted": p1_z_fainted,
            "team": p1_team,
            "is_ready": p1_ready
        },
        "player2": {
            "nickname": p2.nickname if p2 else "---",
            "active_zenamon_name": p2_z_name,
            "active_zenamon_hp": p2_z_hp,
            "active_zenamon_max_hp": p2_z_max,
            "active_zenamon_sprite": p2_z_sprite,
            "active_zenamon_is_fainted": p2_z_fainted,
            "team": p2_team,
            "is_ready": p2_ready
        } if p2 else { "nickname": "---", "is_ready": False, "team": [] },
        "new_events": events,
        "reactions": reaction_list,
        "winner_id": winner.id if winner else None,
        "winner_nickname": winner.nickname if winner else None
    }

@app.post("/api/v1/duels/{code}/action")
async def send_action(code: str, action: BattleAction, current_player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    duel = db.query(Duel).filter(Duel.id == code.upper()).first()
    if not duel:
        raise HTTPException(status_code=404, detail="Duello non trovato")

    if duel.status != "BATTLE":
        raise HTTPException(status_code=400, detail="Non sei in fase di combattimento")

    turn = db.query(Turn).filter(Turn.duel_id == duel.id, Turn.turn_number == duel.current_turn).first()
    if not turn:
        raise HTTPException(status_code=500, detail="Turno non trovato")

    if current_player.id not in (duel.player1_id, duel.player2_id):
        raise HTTPException(status_code=403, detail="Non partecipi a questo duello")

    action.type = action.type.upper()
    if action.type not in ("ATTACK", "SWITCH"):
        raise HTTPException(status_code=400, detail="Azione non valida")

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
    active_by_player = {duel.player1_id: p1_active, duel.player2_id: p2_active}
    forced_switch_players = {
        player_id for player_id, active in active_by_player.items()
        if active and active.is_fainted
    }

    if current_player.id in forced_switch_players and action.type != "SWITCH":
        raise HTTPException(status_code=400, detail="Il tuo Zenamon e' esausto: devi cambiarlo")
    if forced_switch_players and current_player.id not in forced_switch_players:
        raise HTTPException(status_code=400, detail="Attendi che l'avversario cambi lo Zenamon esausto")

    if action.type == "ATTACK":
        if not action.move_name:
            raise HTTPException(status_code=400, detail="Devi scegliere una mossa")
    else:
        if action.zenamon_index is None:
            raise HTTPException(status_code=400, detail="Devi scegliere uno Zenamon")
        target = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == duel.id,
            DuelZenamon.player_id == current_player.id,
            DuelZenamon.position == action.zenamon_index
        ).first()
        if not target:
            raise HTTPException(status_code=400, detail="Zenamon non trovato nella tua squadra")
        if target.is_active:
            raise HTTPException(status_code=400, detail="Questo Zenamon e' gia' in campo")
        if target.is_fainted:
            raise HTTPException(status_code=400, detail="Questo Zenamon e' esausto")

        if current_player.id not in forced_switch_players:
            if not action.move_name:
                raise HTTPException(status_code=400, detail="Devi scegliere una mossa per il nuovo Zenamon")
            z_cache = db.get(ZenamonCache, target.zenamon_id)
            moves = json.loads(z_cache.moves) if z_cache and z_cache.moves else []
            if not any(m["name"] == action.move_name for m in moves):
                raise HTTPException(status_code=400, detail=f"Mossa {action.move_name} non valida per {z_cache.name}")

    if current_player.id == duel.player1_id:
        if turn.p1_action:
            raise HTTPException(status_code=400, detail="Azione gia' inviata per questo turno")
        turn.p1_action = action.model_dump_json()
    else:
        if turn.p2_action:
            raise HTTPException(status_code=400, detail="Azione gia' inviata per questo turno")
        turn.p2_action = action.model_dump_json()

    db.commit()

    p1_must_switch = duel.player1_id in forced_switch_players
    p2_must_switch = duel.player2_id in forced_switch_players
    forced_actions_ready = (
        forced_switch_players
        and (not p1_must_switch or turn.p1_action)
        and (not p2_must_switch or turn.p2_action)
    )

    # In un turno normale servono entrambi. Dopo un KO attivo servono solo gli switch obbligatori.
    if (not forced_switch_players and turn.p1_action and turn.p2_action) or forced_actions_ready:
        resolve_turn(duel, db)

    return {"accepted": True}


@app.post("/api/v1/duels/{code}/reaction")
async def send_reaction(code: str, reaction_in: ReactionCreate, current_player: Player = Depends(get_current_player), db: Session = Depends(get_db)):
    duel = db.query(Duel).filter(Duel.id == code.upper()).first()
    if not duel:
        raise HTTPException(status_code=404, detail="Duello non trovato")
    
    new_reaction = Reaction(
        duel_id=duel.id,
        emoji=reaction_in.emoji
    )
    db.add(new_reaction)
    db.commit()
    
    return {"success": True}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "POCKET-ZENA API"}

# Monta i file statici del frontend alla fine per non interferire con le rotte API
# Usiamo percorsi assoluti per robustezza su PythonAnywhere
#frontend_path = os.path.join(BASE_DIR, "frontend")
#app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend_static")
#app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend_root")

import uuid
import random
import string
import json
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.models.database import SessionLocal, engine, Base, Player, Duel, ZenamonCache, DuelZenamon, Turn, Reaction, init_db
from backend.schemas.player import PlayerCreate, PlayerResponse
from backend.schemas.duel import DuelCreateResponse, DuelJoinResponse, DuelSpectateResponse
from backend.schemas.zenamon import ZenamonResponse, TeamCreate, ZenamonSearchResult
from backend.schemas.battle import BattleStatusResponse, PlayerBattleStatus, BattleAction, ReactionCreate
from backend.pokeapi_client import get_zenamon_data, search_zenamon_names, get_zenamon_basic_data
from backend.battle_engine import resolve_turn

# Inizializza il DB all'avvio
init_db()

app = FastAPI(title="POCKET-ZENA API")

# Configurazione CORS per sviluppo locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    names = await search_zenamon_names(name)
    if not names:
        return {"results": []}
    
    # Carichiamo i dati base per tutti i nomi trovati
    tasks = [get_zenamon_basic_data(n, db) for n in names]
    results = await asyncio.gather(*tasks)
    
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
    
    for i, z_id in enumerate(team_in.zenamon_ids):
        # Assicuriamoci che lo Zenamon sia in cache
        z_cache = db.query(ZenamonCache).filter(ZenamonCache.id == z_id).first()
        if not z_cache:
            # Proviamo a recuperarlo se non c'è (potrebbe capitare se il client manda un ID a caso)
            z_data = await get_zenamon_data(str(z_id), db)
            if not z_data:
                raise HTTPException(status_code=404, detail=f"Zenamon con ID {z_id} non trovato")
            z_cache = db.query(ZenamonCache).filter(ZenamonCache.id == z_id).first()

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
    
    turn = db.query(Turn).filter(Turn.duel_id == duel.id, Turn.turn_number == duel.current_turn).first()

    # Dati Zenamon Attivi
    def get_player_info(player_id):
        if not player_id: return {
            "nickname": "---", "active_zenamon_name": None, "active_zenamon_hp": None, 
            "active_zenamon_max_hp": None, "active_zenamon_sprite": None, "team": [], "is_ready": False
        }
        
        # Info Zenamon Attivo
        active = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == duel.id, 
            DuelZenamon.player_id == player_id,
            DuelZenamon.is_active == True
        ).first()
        
        z_name, z_hp, z_max, z_sprite = None, None, None, None
        if active:
            z_cache = db.get(ZenamonCache, active.zenamon_id)
            z_max = json.loads(z_cache.base_stats).get("hp", 100)
            z_name, z_hp, z_sprite = z_cache.name, active.current_hp, z_cache.sprite_url
            
        # Info Squadra
        team_dz = db.query(DuelZenamon).filter(
            DuelZenamon.duel_id == duel.id, 
            DuelZenamon.player_id == player_id
        ).order_by(DuelZenamon.position).all()
        
        team_status = []
        for dz in team_dz:
            zc = db.get(ZenamonCache, dz.zenamon_id)
            m_hp = json.loads(zc.base_stats).get("hp", 100)
            team_status.append({
                "name": zc.name,
                "current_hp": dz.current_hp,
                "max_hp": m_hp,
                "is_fainted": dz.is_fainted
            })
            
        ready = False
        if turn:
            ready = (turn.p1_action is not None) if player_id == duel.player1_id else (turn.p2_action is not None)
            
        player_obj = db.get(Player, player_id)
        
        return {
            "nickname": player_obj.nickname,
            "active_zenamon_name": z_name,
            "active_zenamon_hp": z_hp,
            "active_zenamon_max_hp": z_max,
            "active_zenamon_sprite": z_sprite,
            "team": team_status,
            "is_ready": ready
        }

    p1_info = get_player_info(duel.player1_id)
    p2_info = get_player_info(duel.player2_id)
    
    # Eventi (Log del turno precedente o corrente se processato)
    events = []
    last_processed_turn = db.query(Turn).filter(
        Turn.duel_id == duel.id, 
        Turn.processed == True
    ).order_by(Turn.turn_number.desc()).first()
    
    if last_processed_turn and last_processed_turn.resolution_log:
        events = last_processed_turn.resolution_log.split("\n")
    
    # Reazioni
    reactions = db.query(Reaction).filter(Reaction.duel_id == duel.id).order_by(Reaction.created_at.desc()).limit(10).all()
    reaction_list = [{"id": r.id, "emoji": r.emoji} for r in reactions]
    
    winner = db.get(Player, duel.winner_id) if duel.winner_id else None

    return {
        "status": duel.status,
        "current_turn": duel.current_turn,
        "player1": p1_info,
        "player2": p2_info,
        "new_events": events,
        "reactions": reaction_list,
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

    # Validazione Zenamon esausto: deve switchare
    active_zenamon = db.query(DuelZenamon).filter(
        DuelZenamon.duel_id == duel.id,
        DuelZenamon.player_id == current_player.id,
        DuelZenamon.is_active == True
    ).first()
    
    if active_zenamon and active_zenamon.is_fainted:
        if action.type != "SWITCH" and action.zenamon_index is None:
            raise HTTPException(status_code=400, detail="Il tuo Zenamon è esausto, devi cambiarlo!")

    if current_player.id == duel.player1_id:
        if turn.p1_action:
            raise HTTPException(status_code=400, detail="Azione già inviata per questo turno")
        turn.p1_action = action.model_dump_json()
    elif current_player.id == duel.player2_id:
        if turn.p2_action:
            raise HTTPException(status_code=400, detail="Azione già inviata per questo turno")
        turn.p2_action = action.model_dump_json()
    else:
        raise HTTPException(status_code=403, detail="Non partecipi a questo duello")
    
    db.commit()
    
    # Se entrambi pronti, risolvi il turno
    if turn.p1_action and turn.p2_action:
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

# Monta i file statici del frontend alla fine per non interferire con le rotte API
# Supportiamo sia l'accesso alla root che l'accesso tramite la sottocartella /frontend
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend_static")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend_root")

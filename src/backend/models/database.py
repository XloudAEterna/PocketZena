from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import os
import sys

# CORSO
# controlliamo che la variabile d'ambiente DB_BASEDIR sia settata, se non lo e' usciamo dal programma
try:
    db_basedir = os.environ["DB_BASEDIR"]
except KeyError:
    sys.exit("CRITICAL: DB_BASEDIR environment variable missing.")

try:
    CACHE_BASEDIR = os.environ["CACHE_BASEDIR"]
except KeyError:
    sys.exit("CRITICAL: CACHE_BASEDIR environment variable missing.")

# CORSO
# usiamo il valore di db_basedir e se non c'e' usiamo un default, e' impossibile che non ci sia perche'
# abbiamo fatto il controllo sopra, ma questo e' il modo pythonico di usare un valore di default in caso
# non sia settata una env var
db_basedir = os.environ.get("DB_BASEDIR", "/app/db/development/")

# CORSO
# la riga sotto legge il path assoluto dove e' stato lanciato il programma per scriverci poi il db
# antipattern!
#BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Calcola il percorso relativo del DB a partire dalla ENV var DB_PATH
DB_PATH = os.path.join(db_basedir, "pocket_zena.sqlite3")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(3), nullable=False)
    session_token = Column(String, unique=True, index=True)
    last_active = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

class ZenamonCache(Base):
    __tablename__ = "zenamon_cache"
    id = Column(Integer, primary_key=True, index=True) # PokeAPI ID
    name = Column(String, index=True)
    sprite_url = Column(String)
    types = Column(Text) # JSON string
    base_stats = Column(Text) # JSON string
    moves = Column(Text) # JSON string con le 4 mosse [ {name, power, type, damage_class}, ... ]

class Duel(Base):
    __tablename__ = "duels"
    id = Column(String, primary_key=True, index=True) # Code like XZY1
    player1_id = Column(Integer, ForeignKey("players.id"))
    player2_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    status = Column(String, default="WAITING") # WAITING, SELECTION, BATTLE, FINISHED
    current_turn = Column(Integer, default=0)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

class DuelZenamon(Base):
    __tablename__ = "duel_zenamon"
    id = Column(Integer, primary_key=True, index=True)
    duel_id = Column(String, ForeignKey("duels.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    zenamon_id = Column(Integer, ForeignKey("zenamon_cache.id"))
    current_hp = Column(Integer)
    is_fainted = Column(Boolean, default=False)
    position = Column(Integer) # 1, 2, 3
    is_active = Column(Boolean, default=False)

class Turn(Base):
    __tablename__ = "turns"
    id = Column(Integer, primary_key=True, index=True)
    duel_id = Column(String, ForeignKey("duels.id"))
    turn_number = Column(Integer)
    p1_action = Column(Text) # JSON
    p2_action = Column(Text) # JSON
    resolution_log = Column(Text)
    processed = Column(Boolean, default=False)

class Reaction(Base):
    __tablename__ = "reactions"
    id = Column(Integer, primary_key=True, index=True)
    duel_id = Column(String, ForeignKey("duels.id"))
    emoji = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

def init_db():
    Base.metadata.create_all(bind=engine)

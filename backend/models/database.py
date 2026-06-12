from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./pocket_zena.sqlite3"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String(3), nullable=False)
    session_token = Column(String, unique=True, index=True)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)

class ZenamonCache(Base):
    __tablename__ = "zenamon_cache"
    id = Column(Integer, primary_key=True, index=True) # PokeAPI ID
    name = Column(String, index=True)
    sprite_url = Column(String)
    types = Column(Text) # JSON string
    base_stats = Column(Text) # JSON string

class Duel(Base):
    __tablename__ = "duels"
    id = Column(String, primary_key=True, index=True) # Code like XZY1
    player1_id = Column(Integer, ForeignKey("players.id"))
    player2_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    status = Column(String, default="WAITING") # WAITING, SELECTION, BATTLE, FINISHED
    current_turn = Column(Integer, default=0)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

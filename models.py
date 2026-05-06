import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database import Base


class Player(Base):
    __tablename__ = 'player'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    api_key = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    rolls = relationship('DiceRoll', back_populates='player')
    pins = relationship('Pin', back_populates='player')


class DiceRoll(Base):
    __tablename__ = 'dice_roll'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'), nullable=False)
    player_name = Column(String(50), nullable=False)
    dice_type = Column(String(10), nullable=False)
    result = Column(Integer, nullable=False)
    formula = Column(String(50), nullable=False)
    total = Column(Integer, nullable=False)
    individual = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    player = relationship('Player', back_populates='rolls')


class Pin(Base):
    __tablename__ = 'pin'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'), nullable=False)
    player_name = Column(String(50), nullable=False)
    npc_name = Column(String(50), nullable=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    player = relationship('Player', back_populates='pins')


class MapImage(Base):
    __tablename__ = 'map_image'

    id = Column(Integer, primary_key=True)
    data_url = Column(Text, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

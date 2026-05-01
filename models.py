import uuid
from datetime import datetime
from database import db


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    api_key = db.Column(db.String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)


class DiceRoll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player_name = db.Column(db.String(50), nullable=False)
    dice_type = db.Column(db.String(10), nullable=False)
    result = db.Column(db.Integer, nullable=False)
    formula = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    individual = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship('Player', backref='rolls')


class Pin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    player_name = db.Column(db.String(50), nullable=False)
    npc_name = db.Column(db.String(50), nullable=True)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    player = db.relationship('Player', backref='pins')


class MapImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_url = db.Column(db.Text, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

from datetime import datetime
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Player
from auth import require_player

router = APIRouter(prefix='/api', tags=['auth'])


class PlayerCreate(BaseModel):
    name: str


@router.post('/players')
def create_or_login(body: PlayerCreate, db: Session = Depends(get_db)):
    name = body.name.strip().title()
    if len(name) < 2 or len(name) > 30:
        raise HTTPException(status_code=400, detail='Nome deve ter entre 2 e 30 caracteres')

    player = db.query(Player).filter(Player.name == name).first()
    if not player:
        player = Player(name=name)
        db.add(player)

    player.last_seen = datetime.utcnow()
    db.commit()

    return {
        'player': {
            'id': player.id,
            'name': player.name,
            'api_key': player.api_key,
            'color': player.color,
        }
    }


class PlayerLogin(BaseModel):
    name: str


class PlayerColorBody(BaseModel):
    color: str


@router.post('/players/color')
def set_player_color(
    body: PlayerColorBody,
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    if not re.match(r'^#[0-9a-fA-F]{6}$', body.color):
        raise HTTPException(status_code=400, detail='Cor inválida. Use formato #RRGGBB')
    player.color = body.color
    db.commit()
    return {'color': player.color}


@router.post('/players/login')
def login(body: PlayerLogin, db: Session = Depends(get_db)):
    name = body.name.strip().title()
    player = db.query(Player).filter(Player.name == name).first()
    if not player:
        raise HTTPException(status_code=404, detail='Jogador não encontrado')

    player.last_seen = datetime.utcnow()
    db.commit()

    return {
        'player': {
            'id': player.id,
            'name': player.name,
            'api_key': player.api_key,
        }
    }

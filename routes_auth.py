from datetime import datetime

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
        }
    }


class PlayerLogin(BaseModel):
    name: str


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

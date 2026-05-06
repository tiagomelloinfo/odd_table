from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Player


async def require_player(
    x_api_key: str = Header(None, alias='X-API-Key'),
    db: Session = Depends(get_db),
) -> Player:
    """Dependência FastAPI — extrai o jogador pelo header X-API-Key."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail='Token de autenticação ausente. Envie X-API-Key.',
        )

    player = db.query(Player).filter(Player.api_key == x_api_key).first()
    if not player:
        raise HTTPException(
            status_code=401,
            detail='Token inválido. Faça login novamente.',
        )

    return player

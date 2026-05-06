import asyncio
import json
import random
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from database import get_db
from models import Player, DiceRoll, Pin, MapImage
from auth import require_player

router = APIRouter(prefix='/api', tags=['dice'])

DICE_PATTERN = re.compile(r'^(\d+)?d(\d+)([+-]\d+)?$')

# SSE: fila global de eventos
_sse_queues: list[asyncio.Queue] = []


def _broadcast(event: str, data: dict):
    """Envia evento SSE para todos os clientes conectados."""
    payload = json.dumps({'event': event, 'data': data})
    dead = []
    for q in _sse_queues:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _sse_queues.remove(q)


def parse_dice(formula: str):
    """Parse fórmula de dados tipo 'd20', '2d6+3', '3d8-2'."""
    formula = formula.strip().lower()
    m = DICE_PATTERN.match(formula)
    if not m:
        return None
    qty = int(m.group(1)) if m.group(1) else 1
    sides = int(m.group(2))
    modifier = int(m.group(3)) if m.group(3) else 0

    if qty < 1 or qty > 100:
        return None
    if sides not in (4, 6, 8, 10, 12, 20, 100):
        return None

    return {'qty': qty, 'sides': sides, 'modifier': modifier}


def get_online_players(db: Session):
    """Retorna lista de jogadores que deram ping nos últimos 60 segundos."""
    threshold = datetime.utcnow() - timedelta(seconds=60)
    players = db.query(Player).filter(Player.last_seen >= threshold).all()
    return [{'id': p.id, 'name': p.name} for p in players]


class RollBody(BaseModel):
    dice: str = 'd20'


@router.post('/roll')
def roll_dice(
    body: RollBody,
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    parsed = parse_dice(body.dice)
    if not parsed:
        raise HTTPException(status_code=400, detail='Fórmula inválida. Use algo como d20, 2d6+3')

    rolls = [random.randint(1, parsed['sides']) for _ in range(parsed['qty'])]
    total = sum(rolls) + parsed['modifier']
    dice_type = f"d{parsed['sides']}"

    roll = DiceRoll(
        player_id=player.id,
        player_name=player.name,
        dice_type=dice_type,
        result=rolls[0] if len(rolls) == 1 else sum(rolls),
        formula=body.dice,
        total=total,
        individual=rolls,
    )
    db.add(roll)
    db.commit()

    roll_dict = {
        'id': roll.id,
        'player_name': roll.player_name,
        'dice_type': roll.dice_type,
        'result': roll.result,
        'formula': roll.formula,
        'total': roll.total,
        'individual': rolls,
        'created_at': roll.created_at.isoformat(),
    }

    online = get_online_players(db)
    _broadcast('new_roll', {'roll': roll_dict, 'online': online})

    return {'roll': roll_dict}


@router.get('/rolls')
def list_rolls(
    x_api_key: str | None = Header(None, alias='X-API-Key'),
    db: Session = Depends(get_db),
):
    player = None
    if x_api_key:
        player = db.query(Player).filter(Player.api_key == x_api_key).first()

    rolls = db.query(DiceRoll).order_by(DiceRoll.created_at.desc()).limit(50).all()
    return {
        'rolls': [{
            'id': r.id,
            'player_name': r.player_name,
            'dice_type': r.dice_type,
            'result': r.result,
            'formula': r.formula,
            'total': r.total,
            'individual': r.individual,
            'created_at': r.created_at.isoformat(),
        } for r in rolls],
        'online': get_online_players(db),
        'current_player': player.name if player else None,
    }


@router.get('/stream')
async def event_stream():
    """SSE endpoint nativo do FastAPI — sem bloqueio, sem threads."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _sse_queues.append(queue)

    async def generate():
        try:
            yield f"event: connected\ndata: {json.dumps({'status': 'ok'})}\n\n"
            while True:
                payload = await queue.get()
                yield f"{payload}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in _sse_queues:
                _sse_queues.remove(queue)

    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


class PingBody(BaseModel):
    pass


@router.post('/ping')
def ping(
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    player.last_seen = datetime.utcnow()
    db.commit()

    online = get_online_players(db)
    _broadcast('online_update', {'online': online})

    return {'online': online}  # ← mudado: retorna dict, não Response


class PinBody(BaseModel):
    x: float
    y: float
    npc_name: str | None = None


class MapImageBody(BaseModel):
    data_url: str
    width: int = 0
    height: int = 0


def _serialize_pins(db: Session):
    return [{
        'id': p.id,
        'player_name': p.player_name,
        'npc_name': p.npc_name,
        'x': p.x,
        'y': p.y,
    } for p in db.query(Pin).all()]


@router.post('/pins')
def set_pin(
    body: PinBody,
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    """Define a posição do PIN.

    - Jogadores comuns: 1 pin por jogador (remove o anterior)
    - Mestre: múltiplos pins. Se npc_name já existir, move o pin existente.
    """
    x = body.x
    y = body.y
    npc_name = body.npc_name

    if player.name == 'Mestre':
        if npc_name:
            existing = db.query(Pin).filter(Pin.npc_name == npc_name).first()
            if existing:
                existing.x = x
                existing.y = y
                db.commit()
                pins = _serialize_pins(db)
                _broadcast('pins_update', {'pins': pins})
                return {
                    'pin': {
                        'id': existing.id,
                        'player_name': existing.player_name,
                        'npc_name': existing.npc_name,
                        'x': existing.x,
                        'y': existing.y,
                    }
                }

        pin = Pin(player_id=player.id, player_name=player.name, npc_name=npc_name, x=x, y=y)
        db.add(pin)
    else:
        db.query(Pin).filter(Pin.player_id == player.id).delete()
        pin = Pin(player_id=player.id, player_name=player.name, npc_name=None, x=x, y=y)
        db.add(pin)

    db.commit()
    pins = _serialize_pins(db)
    _broadcast('pins_update', {'pins': pins})

    return {
        'pin': {
            'id': pin.id,
            'player_name': pin.player_name,
            'npc_name': pin.npc_name,
            'x': pin.x,
            'y': pin.y,
        }
    }


@router.get('/pins')
def get_pins(db: Session = Depends(get_db)):
    return {'pins': _serialize_pins(db)}


@router.delete('/pins/{pin_id}')
def remove_pin_by_id(
    pin_id: int,
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    pin = db.query(Pin).filter(Pin.id == pin_id).first()
    if not pin:
        raise HTTPException(status_code=404, detail='Pin não encontrado')

    if player.name != 'Mestre' and pin.player_id != player.id:
        raise HTTPException(status_code=403, detail='Você não pode remover o pin de outro jogador')

    db.delete(pin)
    db.commit()

    pins = _serialize_pins(db)
    _broadcast('pins_update', {'pins': pins})

    return {'sucesso': True}


@router.delete('/pins')
def remove_own_pin(
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    if player.name == 'Mestre':
        raise HTTPException(status_code=400, detail='Mestre deve remover pins individualmente pelo nome')

    db.query(Pin).filter(Pin.player_id == player.id).delete()
    db.commit()

    pins = _serialize_pins(db)
    _broadcast('pins_update', {'pins': pins})

    return {'sucesso': True}


@router.post('/map-image')
def set_map_image(
    body: MapImageBody,
    player: Player = Depends(require_player),
    db: Session = Depends(get_db),
):
    if player.name != 'Mestre':
        raise HTTPException(status_code=403, detail='Apenas o Mestre pode carregar a imagem do mapa')

    db.query(MapImage).delete()
    img = MapImage(data_url=body.data_url, width=body.width, height=body.height)
    db.add(img)
    db.commit()

    _broadcast('map_image_update', {
        'data_url': img.data_url,
        'width': img.width,
        'height': img.height,
    })

    return {'sucesso': True}


@router.get('/map-image')
def get_map_image(db: Session = Depends(get_db)):
    img = db.query(MapImage).first()
    if not img:
        return {'data_url': None}
    return {
        'data_url': img.data_url,
        'width': img.width,
        'height': img.height,
    }

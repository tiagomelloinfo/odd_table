import re
import random
import json
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, Response, stream_with_context
from database import db
from models import Player, DiceRoll, Pin, MapImage
from sse_manager import sse_manager
from auth import require_player

bp = Blueprint('dice', __name__, url_prefix='/api')

DICE_PATTERN = re.compile(r'^(\d+)?d(\d+)([+-]\d+)?$')


def parse_dice(formula):
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


def get_online_players():
    """Retorna lista de jogadores que deram ping nos últimos 60 segundos."""
    threshold = datetime.utcnow() - timedelta(seconds=60)
    players = Player.query.filter(Player.last_seen >= threshold).all()
    return [{'id': p.id, 'name': p.name} for p in players]


@bp.route('/roll', methods=['POST'])
@require_player
def roll_dice(player):
    data = request.get_json()
    formula = data.get('dice', 'd20') if data else 'd20'
    parsed = parse_dice(formula)
    if not parsed:
        return jsonify({'erro': 'Fórmula inválida. Use algo como d20, 2d6+3'}), 400

    rolls = [random.randint(1, parsed['sides']) for _ in range(parsed['qty'])]
    total = sum(rolls) + parsed['modifier']
    dice_type = f"d{parsed['sides']}"

    roll = DiceRoll(
        player_id=player.id,
        player_name=player.name,
        dice_type=dice_type,
        result=rolls[0] if len(rolls) == 1 else sum(rolls),
        formula=formula,
        total=total,
        individual=rolls,
    )
    db.session.add(roll)
    db.session.commit()

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

    online = get_online_players()
    sse_manager.broadcast('new_roll', {'roll': roll_dict, 'online': online})

    return jsonify({'roll': roll_dict})


@bp.route('/rolls', methods=['GET'])
def list_rolls():
    api_key = request.headers.get('X-API-Key')
    player = Player.query.filter_by(api_key=api_key).first() if api_key else None

    rolls = DiceRoll.query.order_by(DiceRoll.created_at.desc()).limit(50).all()
    return jsonify({
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
        'online': get_online_players(),
        'current_player': player.name if player else None,
    })


@bp.route('/stream')
def stream():
    def event_stream():
        q = sse_manager.subscribe()
        try:
            yield f"event: connected\ndata: {json.dumps({'status': 'ok'})}\n\n"
            while True:
                msg = q.get()
                yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
        except GeneratorExit:
            pass
        finally:
            sse_manager.unsubscribe(q)

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@bp.route('/ping', methods=['POST'])
@require_player
def ping(player):
    player.last_seen = datetime.utcnow()
    db.session.commit()

    online = get_online_players()
    sse_manager.broadcast('online_update', {'online': online})

    return jsonify({'online': online})


@bp.route('/pins', methods=['POST'])
@require_player
def set_pin(player):
    """Define a posição do PIN.

    - Jogadores comuns: 1 pin por jogador (remove o anterior)
    - Mestre: múltiplos pins. Se npc_name já existir, move o pin existente.
    """
    data = request.get_json()
    if not data or 'x' not in data or 'y' not in data:
        return jsonify({'erro': 'Envie x e y'}), 400

    x = float(data['x'])
    y = float(data['y'])
    npc_name = data.get('npc_name', '').strip() or None

    if player.name == 'Mestre':
        # Mestre: se npc_name já existir (em qualquer pin), move ele
        if npc_name:
            existing = Pin.query.filter_by(npc_name=npc_name).first()
            if existing:
                existing.x = x
                existing.y = y
                db.session.commit()
                pins = [{'id': p.id, 'player_name': p.player_name, 'npc_name': p.npc_name, 'x': p.x, 'y': p.y} for p in Pin.query.all()]
                sse_manager.broadcast('pins_update', {'pins': pins})
                return jsonify({'pin': {'id': existing.id, 'player_name': existing.player_name, 'npc_name': existing.npc_name, 'x': existing.x, 'y': existing.y}})

        # Novo pin
        pin = Pin(player_id=player.id, player_name=player.name, npc_name=npc_name, x=x, y=y)
        db.session.add(pin)
    else:
        # Jogador comum: 1 pin por jogador
        Pin.query.filter_by(player_id=player.id).delete()
        pin = Pin(player_id=player.id, player_name=player.name, npc_name=None, x=x, y=y)
        db.session.add(pin)

    db.session.commit()

    pins = [{'id': p.id, 'player_name': p.player_name, 'npc_name': p.npc_name, 'x': p.x, 'y': p.y} for p in Pin.query.all()]
    sse_manager.broadcast('pins_update', {'pins': pins})

    return jsonify({'pin': {'id': pin.id, 'player_name': pin.player_name, 'npc_name': pin.npc_name, 'x': pin.x, 'y': pin.y}})


@bp.route('/pins', methods=['GET'])
def get_pins():
    """Retorna todos os pins ativos."""
    pins = Pin.query.all()
    return jsonify({
        'pins': [{'id': p.id, 'player_name': p.player_name, 'npc_name': p.npc_name, 'x': p.x, 'y': p.y} for p in pins]
    })


@bp.route('/pins/<int:pin_id>', methods=['DELETE'])
@require_player
def remove_pin_by_id(player, pin_id):
    """Remove um PIN específico pelo ID. Só o Mestre ou o dono pode remover."""
    pin = Pin.query.get(pin_id)
    if not pin:
        return jsonify({'erro': 'Pin não encontrado'}), 404

    if player.name != 'Mestre' and pin.player_id != player.id:
        return jsonify({'erro': 'Você não pode remover o pin de outro jogador'}), 403

    db.session.delete(pin)
    db.session.commit()

    pins = [{'id': p.id, 'player_name': p.player_name, 'npc_name': p.npc_name, 'x': p.x, 'y': p.y} for p in Pin.query.all()]
    sse_manager.broadcast('pins_update', {'pins': pins})

    return jsonify({'sucesso': True})


@bp.route('/pins', methods=['DELETE'])
@require_player
def remove_own_pin(player):
    """Remove o(s) PIN(s) do próprio jogador (jogador comum remove o seu único)."""
    if player.name == 'Mestre':
        return jsonify({'erro': 'Mestre deve remover pins individualmente pelo nome'}), 400

    Pin.query.filter_by(player_id=player.id).delete()
    db.session.commit()

    pins = [{'id': p.id, 'player_name': p.player_name, 'npc_name': p.npc_name, 'x': p.x, 'y': p.y} for p in Pin.query.all()]
    sse_manager.broadcast('pins_update', {'pins': pins})

    return jsonify({'sucesso': True})


@bp.route('/map-image', methods=['POST'])
@require_player
def set_map_image(player):
    """Só o Mestre pode carregar imagem do mapa."""
    if player.name != 'Mestre':
        return jsonify({'erro': 'Apenas o Mestre pode carregar a imagem do mapa'}), 403

    data = request.get_json()
    if not data or 'data_url' not in data:
        return jsonify({'erro': 'Envie data_url'}), 400

    # Substitui a imagem existente
    MapImage.query.delete()
    img = MapImage(
        data_url=data['data_url'],
        width=int(data.get('width', 0)),
        height=int(data.get('height', 0)),
    )
    db.session.add(img)
    db.session.commit()

    sse_manager.broadcast('map_image_update', {
        'data_url': img.data_url,
        'width': img.width,
        'height': img.height,
    })

    return jsonify({'sucesso': True})


@bp.route('/map-image', methods=['GET'])
def get_map_image():
    """Retorna a imagem do mapa atual."""
    img = MapImage.query.first()
    if not img:
        return jsonify({'data_url': None})
    return jsonify({
        'data_url': img.data_url,
        'width': img.width,
        'height': img.height,
    })

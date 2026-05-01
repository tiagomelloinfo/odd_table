import re
import random
import json
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, Response, stream_with_context
from database import db
from models import Player, DiceRoll
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

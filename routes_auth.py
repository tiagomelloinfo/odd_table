from flask import Blueprint, request, jsonify
from database import db
from models import Player

bp = Blueprint('auth', __name__, url_prefix='/api')


@bp.route('/players', methods=['POST'])
def create_or_login():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Corpo da requisição vazio'}), 400

    name = data.get('name', '').strip().title()
    if len(name) < 2 or len(name) > 30:
        return jsonify({'erro': 'Nome deve ter entre 2 e 30 caracteres'}), 400

    player = Player.query.filter_by(name=name).first()
    if not player:
        player = Player(name=name)
        db.session.add(player)

    player.last_seen = __import__('datetime').datetime.utcnow()
    db.session.commit()

    return jsonify({
        'player': {
            'id': player.id,
            'name': player.name,
            'api_key': player.api_key,
        }
    })


@bp.route('/players/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Corpo da requisição vazio'}), 400

    name = data.get('name', '').strip().title()
    player = Player.query.filter_by(name=name).first()
    if not player:
        return jsonify({'erro': 'Jogador não encontrado'}), 404

    player.last_seen = __import__('datetime').datetime.utcnow()
    db.session.commit()

    return jsonify({
        'player': {
            'id': player.id,
            'name': player.name,
            'api_key': player.api_key,
        }
    })

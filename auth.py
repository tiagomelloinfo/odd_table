from functools import wraps
from flask import request, jsonify
from models import Player


def require_player(f):
    """Decorator que extrai o jogador pelo header X-API-Key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'erro': 'Token de autenticação ausente. Envie X-API-Key.'}), 401

        player = Player.query.filter_by(api_key=api_key).first()
        if not player:
            return jsonify({'erro': 'Token inválido. Faça login novamente.'}), 401

        return f(player=player, *args, **kwargs)
    return decorated

from flask import Flask, render_template
from database import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dice_roller.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from models import Player, DiceRoll  # noqa
        db.create_all()

    from routes_auth import bp as auth_bp
    from routes_dice import bp as dice_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dice_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

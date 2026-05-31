"""
Composition root — Task Manager API refatorada para MVC.

Melhorias aplicadas:
  - config/settings.py        — SECRET_KEY e DATABASE_URL via variáveis de ambiente
  - models/user.py            — SHA-256+salt em vez de MD5; to_dict() sem senha
  - controllers/task_controller.py  — lógica de negócio extraída das routes
  - controllers/user_controller.py  — lógica de negócio extraída das routes
  - routes/task_routes.py     — apenas mapeamento URL → controller
  - routes/user_routes.py     — apenas mapeamento URL → controller
  - middlewares/error_handler.py    — error handling centralizado
  - services/notification_service.py — credenciais via env vars
  - APIs deprecated: .query.get() → db.session.get() em todos os controllers
"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

from config.settings import Config
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from middlewares.error_handler import register_error_handlers

logging.basicConfig(level=logging.INFO)


def create_app(config=Config):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['DEBUG'] = config.DEBUG

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    register_error_handlers(app)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

    @app.route('/')
    def index():
        return jsonify({'message': 'Task Manager API', 'version': '2.0'})

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)

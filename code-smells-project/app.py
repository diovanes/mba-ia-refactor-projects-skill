"""
Composition root — monta a aplicação Flask usando estrutura MVC.

Estrutura MVC criada em src/:
  src/config/settings.py        — configurações via variáveis de ambiente
  src/models/produto_model.py   — model de produto (queries parametrizadas)
  src/models/usuario_model.py   — model de usuário (hash de senha)
  src/models/pedido_model.py    — model de pedido (JOIN elimina N+1)
  src/controllers/              — orquestração request → model → response
  src/views/                    — blueprints com apenas mapeamento de rotas
  src/middlewares/error_handler — error handling centralizado
"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS

from src.config.settings import Config
from src.views.produto_routes import produto_bp
from src.views.usuario_routes import usuario_bp
from src.views.pedido_routes import pedido_bp
from src.middlewares.error_handler import register_error_handlers
from database import get_db

logging.basicConfig(level=logging.INFO)


def create_app(config=Config):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG

    CORS(app)

    # Inicializa o banco ao arrancar a app
    with app.app_context():
        get_db()

    # Registra blueprints
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)

    # Error handling centralizado
    register_error_handlers(app)

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "2.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health"
            }
        })

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 50)
    print("SERVIDOR INICIADO (refatorado para MVC)")
    print("Rodando em http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)

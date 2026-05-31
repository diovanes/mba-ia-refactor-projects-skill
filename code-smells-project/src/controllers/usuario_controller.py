"""Controller de Usuários."""
import logging
from flask import request, jsonify
from src.models.usuario_model import UsuarioModel
from database import get_db

logger = logging.getLogger(__name__)


def listar_usuarios():
    db = get_db()
    usuarios = UsuarioModel.get_all(db)
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    db = get_db()
    usuario = UsuarioModel.get_by_id(db, id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    db = get_db()
    usuario_id = UsuarioModel.create(db, nome, email, senha)
    logger.info("Usuário criado: email=%s", email)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    db = get_db()
    usuario = UsuarioModel.login(db, email, senha)
    if usuario:
        logger.info("Login bem-sucedido: email=%s", email)
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
    else:
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401

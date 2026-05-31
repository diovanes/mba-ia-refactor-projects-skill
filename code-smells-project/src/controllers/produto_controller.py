"""Controller de Produtos — orquestra request → model → response."""
import logging
from flask import request, jsonify
from src.models.produto_model import ProdutoModel
from src.config.settings import Config
from database import get_db

logger = logging.getLogger(__name__)


def listar_produtos():
    db = get_db()
    produtos = ProdutoModel.get_all(db)
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria") or None
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    db = get_db()
    resultados = ProdutoModel.search(db, termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def buscar_produto(id):
    db = get_db()
    produto = ProdutoModel.get_by_id(db, id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")

    if not nome or len(nome) < 2:
        return jsonify({"erro": "Nome inválido (mínimo 2 caracteres)"}), 400
    if len(nome) > 200:
        return jsonify({"erro": "Nome muito longo"}), 400
    if preco is None or preco < 0:
        return jsonify({"erro": "Preço inválido"}), 400
    if estoque is None or estoque < 0:
        return jsonify({"erro": "Estoque inválido"}), 400

    categoria = dados.get("categoria", "geral")
    if categoria not in Config.CATEGORIAS_VALIDAS:
        return jsonify({"erro": f"Categoria inválida. Válidas: {Config.CATEGORIAS_VALIDAS}"}), 400

    db = get_db()
    produto_id = ProdutoModel.create(db, nome, dados.get("descricao", ""), preco, estoque, categoria)
    logger.info("Produto criado: id=%s", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    db = get_db()
    if not ProdutoModel.get_by_id(db, id):
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")

    if not nome or len(nome) < 2:
        return jsonify({"erro": "Nome inválido"}), 400
    if preco is None or preco < 0:
        return jsonify({"erro": "Preço inválido"}), 400
    if estoque is None or estoque < 0:
        return jsonify({"erro": "Estoque inválido"}), 400

    ProdutoModel.update(db, id, nome, dados.get("descricao", ""), preco, estoque, dados.get("categoria", "geral"))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    db = get_db()
    if not ProdutoModel.get_by_id(db, id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    ProdutoModel.delete(db, id)
    logger.info("Produto deletado: id=%s", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

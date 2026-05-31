"""Controller de Pedidos e Relatórios."""
import logging
from flask import request, jsonify
from src.models.pedido_model import PedidoModel
from database import get_db

logger = logging.getLogger(__name__)

STATUSES_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "usuario_id é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    db = get_db()
    resultado = PedidoModel.create(db, usuario_id, itens)

    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info("Pedido criado: id=%s usuario=%s", resultado["pedido_id"], usuario_id)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado"}), 201


def listar_todos_pedidos():
    db = get_db()
    pedidos = PedidoModel.get_all(db)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_pedidos_usuario(usuario_id):
    db = get_db()
    pedidos = PedidoModel.get_by_usuario(db, usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in STATUSES_VALIDOS:
        return jsonify({"erro": f"Status inválido. Válidos: {STATUSES_VALIDOS}"}), 400

    db = get_db()
    PedidoModel.update_status(db, pedido_id, novo_status)
    logger.info("Status do pedido %s atualizado para: %s", pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    db = get_db()
    relatorio = PedidoModel.relatorio_vendas(db)
    return jsonify({"dados": relatorio, "sucesso": True}), 200


def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]

    # Apenas informações seguras — sem secrets, paths ou configurações internas
    return jsonify({
        "status": "ok",
        "database": "connected",
        "version": "2.0.0",
        "counts": {
            "produtos": produtos,
            "usuarios": usuarios,
            "pedidos": pedidos
        }
    }), 200

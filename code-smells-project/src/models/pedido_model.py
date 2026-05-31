"""Model de Pedido — JOIN elimina N+1, queries parametrizadas."""
from src.config.settings import Config


class PedidoModel:

    @staticmethod
    def _rows_to_pedidos(rows):
        """Agrupa linhas do JOIN em lista de pedidos com itens."""
        pedidos = {}
        for row in rows:
            pid = row["id"]
            if pid not in pedidos:
                pedidos[pid] = {
                    "id": pid,
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": []
                }
            if row["produto_id"]:
                pedidos[pid]["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"],
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"]
                })
        return list(pedidos.values())

    @staticmethod
    def _query_pedidos_com_itens(db, usuario_id=None):
        """JOIN único — elimina N+1 queries."""
        sql = """
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   ip.produto_id, ip.quantidade, ip.preco_unitario,
                   pr.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = ip.produto_id
        """
        params = []
        if usuario_id is not None:
            sql += " WHERE p.usuario_id = ?"
            params.append(usuario_id)
        sql += " ORDER BY p.id"

        cursor = db.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    @classmethod
    def get_all(cls, db):
        rows = cls._query_pedidos_com_itens(db)
        return cls._rows_to_pedidos(rows)

    @classmethod
    def get_by_usuario(cls, db, usuario_id):
        rows = cls._query_pedidos_com_itens(db, usuario_id)
        return cls._rows_to_pedidos(rows)

    @staticmethod
    def create(db, usuario_id, itens):
        cursor = db.cursor()

        # Valida e calcula total em uma passagem
        total = 0
        for item in itens:
            cursor.execute(
                "SELECT preco, estoque, nome FROM produtos WHERE id = ?",
                (item["produto_id"],)
            )
            produto = cursor.fetchone()
            if produto is None:
                return {"erro": f"Produto {item['produto_id']} não encontrado"}
            if produto["estoque"] < item["quantidade"]:
                return {"erro": f"Estoque insuficiente para {produto['nome']}"}
            total += produto["preco"] * item["quantidade"]

        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total)
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            cursor.execute(
                "SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],)
            )
            preco = cursor.fetchone()["preco"]
            cursor.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], preco)
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"])
            )

        db.commit()
        return {"pedido_id": pedido_id, "total": total}

    @staticmethod
    def update_status(db, pedido_id, novo_status):
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def relatorio_vendas(db):
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos")
        total_pedidos, faturamento = cursor.fetchone()

        cursor.execute(
            "SELECT status, COUNT(*) FROM pedidos GROUP BY status"
        )
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        desconto = 0
        for limite, taxa in Config.DESCONTO_RULES:
            if faturamento > limite:
                desconto = faturamento * taxa
                break

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": status_counts.get("pendente", 0),
            "pedidos_aprovados": status_counts.get("aprovado", 0),
            "pedidos_cancelados": status_counts.get("cancelado", 0),
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
        }

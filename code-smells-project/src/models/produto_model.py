"""Model de Produto — queries parametrizadas, sem SQL injection."""


class ProdutoModel:

    @staticmethod
    def get_all(db):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM produtos")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(db, produto_id):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def search(db, termo="", categoria=None, preco_min=None, preco_max=None):
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []

        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)

        cursor = db.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def create(db, nome, descricao, preco, estoque, categoria):
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update(db, produto_id, nome, descricao, preco, estoque, categoria):
        cursor = db.cursor()
        cursor.execute(
            "UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, categoria=? WHERE id=?",
            (nome, descricao, preco, estoque, categoria, produto_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def delete(db, produto_id):
        cursor = db.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()
        return cursor.rowcount > 0

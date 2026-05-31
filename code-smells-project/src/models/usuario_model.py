"""Model de Usuário — com hash de senha e queries parametrizadas."""
import hashlib
import os


def _hash_senha(senha):
    """Gera hash seguro com salt aleatório."""
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((senha + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verificar_senha(senha, stored_hash):
    """Verifica senha contra o hash armazenado."""
    try:
        salt, hashed = stored_hash.split(":")
        return hashlib.sha256((senha + salt).encode()).hexdigest() == hashed
    except Exception:
        return False


class UsuarioModel:

    @staticmethod
    def get_all(db):
        cursor = db.cursor()
        cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(db, usuario_id):
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
            (usuario_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(db, nome, email, senha, tipo="cliente"):
        cursor = db.cursor()
        senha_hash = _hash_senha(senha)
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def login(db, email, senha):
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        )
        row = cursor.fetchone()
        if row and _verificar_senha(senha, row["senha"]):
            return {
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "tipo": row["tipo"]
            }
        return None

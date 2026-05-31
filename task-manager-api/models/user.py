"""Model de Usuário — hash seguro com SHA-256 + salt (sem MD5)."""
from database import db
from datetime import datetime
import hashlib
import os


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialização segura — NÃO inclui password."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):
        """Hash seguro com SHA-256 + salt aleatório."""
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((pwd + salt).encode()).hexdigest()
        self.password = f"{salt}:{hashed}"

    def check_password(self, pwd):
        """Verifica senha contra hash armazenado."""
        try:
            salt, hashed = self.password.split(':', 1)
            return hashlib.sha256((pwd + salt).encode()).hexdigest() == hashed
        except Exception:
            return False

    def is_admin(self):
        return self.role == 'admin'

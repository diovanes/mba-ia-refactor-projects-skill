"""Configurações centralizadas — sem credenciais hardcoded."""
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # SMTP — lidos de variáveis de ambiente
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASS = os.environ.get('SMTP_PASS', '')

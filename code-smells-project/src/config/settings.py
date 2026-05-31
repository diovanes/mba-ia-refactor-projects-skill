import os


class Config:
    # Segurança — use variável de ambiente em produção
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

    # Banco de dados
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

    # Modo debug — nunca True em produção
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Categorias válidas de produtos
    CATEGORIAS_VALIDAS = [
        "informatica", "moveis", "vestuario",
        "geral", "eletronicos", "livros"
    ]

    # Regras de desconto (thresholds de faturamento → taxa)
    DESCONTO_RULES = [
        (10000, 0.10),  # acima de R$10.000 → 10%
        (5000, 0.05),   # acima de R$5.000  → 5%
        (1000, 0.02),   # acima de R$1.000  → 2%
    ]

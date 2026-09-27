"""
Configurações centrais do projeto.

Lê as variáveis do arquivo .env e monta a URL de conexão com o PostgreSQL.
Os outros módulos (load.py, app.py) importam daqui, assim a configuração
fica em um único lugar.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import URL

# Procura o arquivo .env (subindo pelas pastas) e carrega suas variáveis
load_dotenv()

# --- Banco de dados ---------------------------------------------------------
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")   # 2º argumento = valor padrão
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))   # porta precisa ser número
DB_NAME = os.getenv("POSTGRES_DB")

# URL de conexão no formato que o SQLAlchemy entende.
# "postgresql+psycopg" = banco PostgreSQL usando o driver psycopg (versão 3).
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

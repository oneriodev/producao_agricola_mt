"""
Configurações centrais do projeto.

Tudo que pode mudar (códigos do IBGE, caminhos, conexão com o banco)
fica aqui. Os outros módulos importam deste arquivo, assim cada
configuração existe em um único lugar.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL

# Procura o arquivo .env (subindo pelas pastas) e carrega suas variáveis
load_dotenv()

# --- Caminhos ---------------------------------------------------------------
# __file__ = este arquivo (src/config.py). Subindo 2 níveis chegamos à raiz.
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"              # dados brutos da API
PROCESSED_DIR = BASE_DIR / "data" / "processed"  # dados tratados

# --- API SIDRA / IBGE -------------------------------------------------------
# Documentação da tabela: https://apisidra.ibge.gov.br/desctabapi.aspx?c=5457
SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"
SIDRA_TABELA = "5457"        # PAM - lavouras temporárias e permanentes
SIDRA_CLASSIFICACAO = "782"  # classificação "Produto das lavouras"
UF_CODIGO = "51"             # código IBGE de Mato Grosso
PERIODO = "last 16"          # últimos 16 anos disponíveis (2010 a 2025)

# Variáveis: código SIDRA -> descrição
VARIAVEIS = {
    "8331": "Área plantada (ha)",
    "216": "Área colhida (ha)",
    "214": "Quantidade produzida (t)",
    "112": "Rendimento médio (kg/ha)",
    "215": "Valor da produção (mil R$)",
}

# Produtos: código SIDRA -> nome
PRODUTOS = {
    "40124": "Soja",
    "40122": "Milho",
    "40099": "Algodão herbáceo",
    "40106": "Cana-de-açúcar",
    "40112": "Feijão",
    "40102": "Arroz",
    "40125": "Sorgo",
}

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
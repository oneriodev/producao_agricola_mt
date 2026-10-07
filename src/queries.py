"""
Consultas de análise usadas pelo painel.

O SQL de cada consulta fica em um arquivo próprio na pasta sql/.
Este módulo lê esses arquivos e executa com parâmetros de forma segura
(os valores nunca são colados no texto do SQL).

Teste rápido (a partir da raiz do projeto, com o banco no ar):
    python -m src.queries
"""

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import BASE_DIR, DATABASE_URL

SQL_DIR = BASE_DIR / "sql"

# Um único engine para o módulo todo: ele gerencia e reaproveita conexões
engine = create_engine(DATABASE_URL)


def ler_sql(nome: str) -> str:
    """Lê o conteúdo do arquivo sql/<nome>.sql."""
    return (SQL_DIR / f"{nome}.sql").read_text(encoding="utf-8")


def executar(nome: str, **params) -> pd.DataFrame:
    """Executa a consulta sql/<nome>.sql com os parâmetros informados."""
    consulta = text(ler_sql(nome))
    with engine.connect() as conn:
        return pd.read_sql(consulta, conn, params=params)


# --- Opções dos filtros -----------------------------------------------------

def listar_anos() -> list[int]:
    return executar("listar_anos")["ano"].tolist()


def listar_produtos() -> list[str]:
    return executar("listar_produtos")["nome"].tolist()


def listar_municipios() -> list[str]:
    return executar("listar_municipios")["nome"].tolist()


# --- Análises ---------------------------------------------------------------

def ranking_municipios(produto: str, ano: int, limite: int = 10) -> pd.DataFrame:
    return executar("ranking_municipios", produto=produto, ano=ano, limite=limite)


def evolucao_estado(produto: str) -> pd.DataFrame:
    return executar("evolucao_estado", produto=produto)


def evolucao_municipio(produto: str, municipio: str) -> pd.DataFrame:
    return executar("evolucao_municipio", produto=produto, municipio=municipio)


def comparacao_culturas(ano: int) -> pd.DataFrame:
    return executar("comparacao_culturas", ano=ano)

def mapa_municipios(produto: str, ano: int) -> pd.DataFrame:
    return executar("mapa_municipios", produto=produto, ano=ano)

if __name__ == "__main__":
    # Mostra todas as colunas sem quebrar a tabela no terminal
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)

    print("Anos:", listar_anos())
    print("Produtos:", listar_produtos())
    print("Municípios:", len(listar_municipios()))

    print("\n=== Ranking: Soja 2025 (top 5) ===")
    print(ranking_municipios("Soja", 2025, limite=5))

    print("\n=== Evolução no estado: Soja ===")
    print(evolucao_estado("Soja"))

    print("\n=== Evolução em Sorriso: Soja ===")
    print(evolucao_municipio("Soja", "Sorriso"))

    print("\n=== Comparação entre culturas: 2025 ===")
    print(comparacao_culturas(2025))

    print("\n=== Mapa: Soja 2025 (primeiras linhas) ===")
    mapa = mapa_municipios("Soja", 2025)
    print(mapa.head())
    print("Linhas:", len(mapa), "| sem dado:", mapa["quantidade_t"].isna().sum())
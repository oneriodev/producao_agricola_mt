"""
Etapa de CARGA do pipeline.

Lê os dados tratados (data/processed/), separa em três tabelas
(municipios, produtos, producao) e grava no PostgreSQL.

Estratégia: carga completa (full refresh) dentro de uma transação.
As tabelas são esvaziadas e preenchidas de novo a cada execução,
então rodar várias vezes sempre dá o mesmo resultado (idempotência).

Como executar (a partir da raiz do projeto, com o banco no ar):
    python -m src.load
"""

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.models import Base
from src.transform import ARQUIVO_TRATADO


def carregar_tratado(caminho=ARQUIVO_TRATADO) -> pd.DataFrame:
    """Lê o CSV tratado, mantendo os códigos como texto."""
    return pd.read_csv(caminho, dtype={"cod_municipio": str, "cod_produto": str})


def separar_tabelas(df: pd.DataFrame):
    """Divide o DataFrame largo nas três tabelas do modelo."""
    municipios = (
        df[["cod_municipio", "municipio"]]
        .drop_duplicates()
        .rename(columns={"municipio": "nome"})
    )

    produtos = (
        df[["cod_produto", "produto"]]
        .drop_duplicates()
        .rename(columns={"produto": "nome"})
    )

    # A tabela de produção guarda só os códigos, não os nomes
    producao = df.drop(columns=["municipio", "produto"])

    return municipios, produtos, producao


def carregar_no_banco(engine, municipios, produtos, producao) -> None:
    """Cria as tabelas (se preciso) e faz a carga completa em uma transação."""
    # Cria as tabelas definidas em models.py, caso ainda não existam
    Base.metadata.create_all(engine)

    # engine.begin() abre uma transação: se algo falhar, tudo é desfeito
    with engine.begin() as conn:
        # Esvazia as tabelas (carga completa = idempotente)
        conn.execute(text("TRUNCATE TABLE producao, produtos, municipios"))

        # Cadastros primeiro, produção depois (por causa das chaves estrangeiras)
        municipios.to_sql("municipios", conn, if_exists="append", index=False)
        produtos.to_sql("produtos", conn, if_exists="append", index=False)
        producao.to_sql("producao", conn, if_exists="append", index=False)


def contar_registros(engine) -> None:
    """Mostra quantas linhas existem em cada tabela."""
    with engine.connect() as conn:
        for tabela in ["municipios", "produtos", "producao"]:
            total = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
            print(f"  {tabela}: {total} linhas")


if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)

    print("Lendo dados tratados...")
    df = carregar_tratado()

    municipios, produtos, producao = separar_tabelas(df)

    print("Gravando no PostgreSQL...")
    carregar_no_banco(engine, municipios, produtos, producao)

    print("Registros no banco:")
    contar_registros(engine)
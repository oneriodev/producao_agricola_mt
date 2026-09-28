"""
Executa o pipeline completo: extração -> transformação -> carga.

Como executar (a partir da raiz do projeto, com o banco no ar):
    python -m src.pipeline
"""

from sqlalchemy import create_engine

from src.config import DATABASE_URL
from src.extract import extrair_dados, salvar_bruto
from src.load import carregar_no_banco, contar_registros, separar_tabelas
from src.transform import salvar_tratado, transformar, validar


def main() -> None:
    print("[1/3] Extraindo dados da API SIDRA...")
    bruto = extrair_dados()
    salvar_bruto(bruto)

    print("\n[2/3] Transformando...")
    tratado = transformar(bruto)
    validar(tratado)
    salvar_tratado(tratado)

    print("\n[3/3] Carregando no PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    municipios, produtos, producao = separar_tabelas(tratado)
    carregar_no_banco(engine, municipios, produtos, producao)
    contar_registros(engine)

    print("\nPipeline concluído!")


if __name__ == "__main__":
    main()
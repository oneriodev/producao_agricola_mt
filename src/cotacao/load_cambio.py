
"""
Carga de cotações PTAX no PostgreSQL.

Execução:
    python -m src.cotacao.load_cambio
"""

from datetime import date

from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.cotacao.extract_cambio import extrair_ptax
from src.cotacao.transform_cambio import transformar_cambio


def gravar_cambio(engine, registro: dict) -> None:
    """Insere ou atualiza uma cotação cambial."""

    comando = text("""
        INSERT INTO cotacao.cambio (
            data_referencia,
            data_hora_cotacao,
            moeda,
            compra,
            venda,
            fonte
        )
        VALUES (
            :data_referencia,
            :data_hora_cotacao,
            :moeda,
            :compra,
            :venda,
            :fonte
        )
        ON CONFLICT (
            data_hora_cotacao,
            moeda,
            fonte
        )
        DO UPDATE SET
            data_referencia = EXCLUDED.data_referencia,
            compra = EXCLUDED.compra,
            venda = EXCLUDED.venda;
    """)

    # A transação é confirmada automaticamente
    # quando o bloco termina sem erros.
    with engine.begin() as conexao:
        conexao.execute(comando, registro)


def executar_pipeline(data_referencia: date) -> None:
    """Executa a extração, transformação e carga."""

    print(f"Consultando PTAX: {data_referencia}")

    dados = extrair_ptax(data_referencia)

    if dados is None:
        print("Não há cotação disponível para essa data.")
        return

    registro = transformar_cambio(dados)

    engine = create_engine(DATABASE_URL)

    try:
        gravar_cambio(engine, registro)

        print("Cotação gravada com sucesso!")
        print(f"Data/hora: {registro['data_hora_cotacao']}")
        print(f"Compra: R$ {registro['compra']}")
        print(f"Venda: R$ {registro['venda']}")

    finally:
        engine.dispose()


if __name__ == "__main__":

    # Mesma data validada no teste de extração.
    data_teste = date(2026, 10, 29)

    executar_pipeline(data_teste)

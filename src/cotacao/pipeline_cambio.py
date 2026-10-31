
"""
Pipeline histórico de cotações PTAX.

Exemplo:
    python -m src.cotacao.pipeline_cambio
"""

from datetime import date

from sqlalchemy import create_engine, text

from src.config import DATABASE_URL
from src.cotacao.extract_cambio import extrair_ptax_periodo
from src.cotacao.transform_cambio import transformar_cambio


def carregar_historico(data_inicial: date, data_final: date):
    """Extrai, transforma e grava o histórico PTAX."""

    print(f"Consultando período: {data_inicial} a {data_final}")

    dados = extrair_ptax_periodo(data_inicial, data_final)

    if not dados:
        print("Nenhuma cotação encontrada no período.")
        return

    registros = [transformar_cambio(item) for item in dados]

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
            venda = EXCLUDED.venda
    """)

    engine = create_engine(DATABASE_URL)

    try:
        with engine.begin() as conexao:
            conexao.execute(comando, registros)

        print(f"Boletins processados: {len(registros)}")
        print("Carga histórica concluída com sucesso!")

    finally:
        engine.dispose()


if __name__ == "__main__":

    carregar_historico(
        date(2026, 10, 1),
        date(2026, 10, 29),
    )

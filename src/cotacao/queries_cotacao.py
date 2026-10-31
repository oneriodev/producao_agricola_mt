
"""
Consultas cambiais ao PostgreSQL.

Responsável por recuperar a PTAX histórica.
"""

from datetime import date

from sqlalchemy import create_engine, text

from src.config import DATABASE_URL


def consultar_cambio(data_referencia: date) -> dict | None:
    """
    Recupera a última PTAX disponível até a data solicitada.

    Em fins de semana e feriados, utiliza a
    cotação mais recente anterior à data.
    """

    sql = text("""
        SELECT
            data_referencia,
            data_hora_cotacao,
            compra,
            venda
        FROM cotacao.vw_cambio_diario
        WHERE data_referencia <= :data_referencia
        ORDER BY data_referencia DESC
        LIMIT 1
    """)

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(
                sql,
                {"data_referencia": data_referencia}
            ).mappings().first()

            return dict(resultado) if resultado else None

    finally:
        engine.dispose()

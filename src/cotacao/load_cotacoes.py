
"""
Carga de cotações fictícias para testes.

Executar na raiz do projeto:
    python -m src.cotacao.load_cotacoes
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, text

from src.config import DATABASE_URL


COTACOES_TESTE = [
    ("FERT-001", "FORN-001", "400.00", "USD", "t"),
    ("FERT-001", "FORN-002", "2250.00", "BRL", "t"),
    ("FERT-001", "FORN-003", "425.00", "USD", "t"),
    ("FERT-002", "FORN-001", "650.00", "USD", "t"),
    ("FERT-003", "FORN-002", "2800.00", "BRL", "t"),
]


def carregar_cotacoes_teste():
    """
    Registra cotações de demonstração.

    Usa códigos de cadastro para localizar os IDs.
    Evita duplicar as mesmas cotações de teste.
    """

    engine = create_engine(DATABASE_URL)

    
    comando = text("""
        INSERT INTO cotacao.cotacoes (
            item_id,
            fornecedor_id,
            data_cotacao,
            validade,
            preco_original,
            moeda_original,
            unidade,
            observacoes
        )
        SELECT
            i.id,
            f.id,
            CAST(:data_cotacao AS DATE),
            CAST(:validade AS DATE),
            CAST(:preco AS NUMERIC(18,6)),
            CAST(:moeda AS CHAR(3)),
            CAST(:unidade AS VARCHAR(20)),
            CAST(:observacoes AS TEXT)

        FROM cotacao.itens i
        CROSS JOIN cotacao.fornecedores f

        WHERE i.cod_item = CAST(:cod_item AS VARCHAR(30))
        AND f.cod_fornecedor = CAST(:cod_fornecedor AS VARCHAR(30))

        AND NOT EXISTS (
            SELECT 1
            FROM cotacao.cotacoes c

            WHERE c.item_id = i.id
                AND c.fornecedor_id = f.id
                AND c.data_cotacao = CAST(:data_cotacao AS DATE)
                AND c.moeda_original = CAST(:moeda AS CHAR(3))
                AND c.preco_original = CAST(:preco AS NUMERIC(18,6))
                AND c.unidade = CAST(:unidade AS VARCHAR(20))
                AND c.observacoes = CAST(:observacoes AS TEXT)
        )

        RETURNING id
    """)

    inseridos = 0

    try:
        with engine.begin() as conexao:
            for cod_item, cod_fornecedor, preco, moeda, unidade in COTACOES_TESTE:

                parametros = {
                    "cod_item": cod_item,
                    "cod_fornecedor": cod_fornecedor,
                    "data_cotacao": date(2026, 10, 29),
                    "validade": date(2026, 11, 5),
                    "preco": Decimal(preco),
                    "moeda": moeda,
                    "unidade": unidade,
                    "observacoes": "DEMONSTRACAO_ETAPA_8",
                }

                resultado = conexao.execute(
                    comando, parametros
                ).scalar_one_or_none()

                if resultado is not None:
                    inseridos += 1

        print(f"Cotações inseridas: {inseridos}")
        print(f"Cotações processadas: {len(COTACOES_TESTE)}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    carregar_cotacoes_teste()

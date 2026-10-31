
"""
Cadastro inicial de insumos e fornecedores.

Os dados utilizados são fictícios e servem
exclusivamente para testes do projeto.

Execução:
    python -m src.cotacao.cadastro_inicial
"""

from sqlalchemy import create_engine, text

from src.config import DATABASE_URL


# Produtos fictícios para testes
INSUMOS = [
    {
        "codigo": "FERT-001",
        "nome": "Ureia 46% N",
        "categoria": "fertilizante",
        "especificacao": "Fertilizante nitrogenado",
        "unidade": "t",
    },
    {
        "codigo": "FERT-002",
        "nome": "MAP 11-52-00",
        "categoria": "fertilizante",
        "especificacao": "Fertilizante fosfatado",
        "unidade": "t",
    },
    {
        "codigo": "FERT-003",
        "nome": "Cloreto de Potássio",
        "categoria": "fertilizante",
        "especificacao": "Fertilizante potássico",
        "unidade": "t",
    },
]

# Fornecedores fictícios
FORNECEDORES = [
    {
        "codigo": "FORN-001",
        "nome": "Fornecedor Agro A",
        "municipio": "Cuiabá",
        "uf": "MT",
    },
    {
        "codigo": "FORN-002",
        "nome": "Fornecedor Agro B",
        "municipio": "Rondonópolis",
        "uf": "MT",
    },
    {
        "codigo": "FORN-003",
        "nome": "Fornecedor Agro C",
        "municipio": "Sorriso",
        "uf": "MT",
    },
]


def cadastrar_dados_iniciais():
    """Cadastra insumos e fornecedores sem duplicar códigos."""

    engine = create_engine(DATABASE_URL)

    sql_item = text("""
        INSERT INTO cotacao.itens (
            cod_item,
            nome,
            categoria,
            especificacao,
            unidade_padrao
        )
        VALUES (
            :codigo,
            :nome,
            :categoria,
            :especificacao,
            :unidade
        )
        ON CONFLICT (cod_item)
        DO UPDATE SET
            nome = EXCLUDED.nome,
            categoria = EXCLUDED.categoria,
            especificacao = EXCLUDED.especificacao,
            unidade_padrao = EXCLUDED.unidade_padrao
    """)

    sql_fornecedor = text("""
        INSERT INTO cotacao.fornecedores (
            cod_fornecedor,
            nome,
            municipio,
            uf
        )
        VALUES (
            :codigo,
            :nome,
            :municipio,
            :uf
        )
        ON CONFLICT (cod_fornecedor)
        DO UPDATE SET
            nome = EXCLUDED.nome,
            municipio = EXCLUDED.municipio,
            uf = EXCLUDED.uf
    """)

    try:
        with engine.begin() as conexao:
            conexao.execute(sql_item, INSUMOS)
            conexao.execute(sql_fornecedor, FORNECEDORES)

        print("Cadastros realizados com sucesso!")
        print(f"Insumos processados: {len(INSUMOS)}")
        print(f"Fornecedores processados: {len(FORNECEDORES)}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    cadastrar_dados_iniciais()

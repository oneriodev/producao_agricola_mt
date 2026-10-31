
"""
Importador de cotações agrícolas CSV e XLSX.

Executar:
    python -m src.cotacao.importar_cotacoes caminho_do_arquivo
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL


COLUNAS = [
    "cod_cotacao",
    "cod_item",
    "cod_fornecedor",
    "data_cotacao",
    "validade",
    "preco_original",
    "moeda_original",
    "unidade",
]


def ler_arquivo(caminho):
    """Lê CSV ou Excel preservando códigos como texto."""

    caminho = Path(caminho)
    extensao = caminho.suffix.lower()

    if extensao == ".csv":
        ultimo_erro = None

        for encoding in ("utf-8-sig", "cp1252"):
            try:
                return pd.read_csv(
                    caminho,
                    sep=None,
                    engine="python",
                    encoding=encoding,
                    dtype=str,
                    keep_default_na=False,
                )
            except UnicodeDecodeError as erro:
                ultimo_erro = erro

        raise ValueError(
            "Codificação CSV não reconhecida."
        ) from ultimo_erro

    if extensao == ".xlsx":
        return pd.read_excel(
            caminho,
            engine="openpyxl",
            dtype=object,
            keep_default_na=False,
        )

    raise ValueError(
        "Formato inválido. Utilize CSV ou XLSX."
    )


def texto(valor):
    """Normaliza valores textuais e campos vazios."""

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def converter_decimal(valor):
    """Converte números brasileiros ou internacionais."""

    valor = texto(valor).replace(" ", "")

    if not valor:
        raise ValueError("Preço vazio.")

    if "," in valor and "." in valor:
        if valor.rfind(",") > valor.rfind("."):
            # Exemplo: 2.250,00
            valor = valor.replace(".", "").replace(",", ".")
        else:
            # Exemplo: 2,250.00
            valor = valor.replace(",", "")

    elif "," in valor:
        # Exemplo: 2250,50
        valor = valor.replace(",", ".")

    try:
        numero = Decimal(valor)
    except InvalidOperation as erro:
        raise ValueError("Preço inválido.") from erro

    if not numero.is_finite() or numero <= 0:
        raise ValueError("Preço deve ser positivo e finito.")

    if numero > Decimal("999999999999.999999"):
        raise ValueError("Preço excede o limite da coluna.")

    if numero.as_tuple().exponent < -6:
        raise ValueError("Máximo de seis casas decimais.")

    return numero


def converter_data(valor, obrigatoria=True):
    """Valida datas ISO ou células de data do Excel."""

    if texto(valor) == "":
        if obrigatoria:
            raise ValueError("Data obrigatória ausente.")
        return None

    if isinstance(valor, (date, datetime)):
        return valor.date() if isinstance(valor, datetime) else valor

    try:
        return date.fromisoformat(texto(valor)[:10])
    except ValueError as erro:
        raise ValueError(
            "Data inválida. Utilize AAAA-MM-DD."
        ) from erro


def validar_linha(linha, itens, fornecedores):
    """Converte e valida um registro da planilha."""

    codigo = texto(linha["cod_cotacao"])
    item = texto(linha["cod_item"])
    fornecedor = texto(linha["cod_fornecedor"])

    moeda = texto(linha["moeda_original"]).upper()
    unidade = texto(linha["unidade"]).lower()

    if not codigo or len(codigo) > 80:
        raise ValueError("Código de cotação inválido.")

    if item not in itens:
        raise ValueError(f"Insumo não cadastrado: {item}")

    if fornecedor not in fornecedores:
        raise ValueError(
            f"Fornecedor não cadastrado: {fornecedor}"
        )

    if moeda not in ("BRL", "USD"):
        raise ValueError("Moeda deve ser BRL ou USD.")

    if not unidade or len(unidade) > 20:
        raise ValueError("Unidade inválida.")

    data_cotacao = converter_data(linha["data_cotacao"])
    validade = converter_data(
        linha["validade"], obrigatoria=False
    )

    if validade and validade < data_cotacao:
        raise ValueError(
            "Validade anterior à data da cotação."
        )

    return {
        "cod_cotacao": codigo,
        "item_id": itens[item],
        "fornecedor_id": fornecedores[fornecedor],
        "data_cotacao": data_cotacao,
        "validade": validade,
        "preco_original": converter_decimal(
            linha["preco_original"]
        ),
        "moeda_original": moeda,
        "unidade": unidade,
        "observacoes": "IMPORTACAO_PLANILHA",
    }


def importar_cotacoes(caminho):
    """Valida a planilha e faz upsert no PostgreSQL."""

    df = ler_arquivo(caminho)
    df.columns = [str(c).strip() for c in df.columns]

    if df.columns.duplicated().any():
        raise ValueError("Existem colunas duplicadas.")

    faltantes = [c for c in COLUNAS if c not in df.columns]

    if faltantes:
        raise ValueError(
            f"Colunas ausentes: {', '.join(faltantes)}"
        )

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            itens = dict(conn.execute(text("""
                SELECT cod_item, id FROM cotacao.itens
            """)).all())

            fornecedores = dict(conn.execute(text("""
                SELECT cod_fornecedor, id
                FROM cotacao.fornecedores
            """)).all())

        validos = []
        rejeitados = []
        codigos_vistos = set()

        for indice, linha in df.iterrows():
            numero_linha = indice + 2

            try:
                registro = validar_linha(
                    linha, itens, fornecedores
                )

                codigo = registro["cod_cotacao"]

                if codigo in codigos_vistos:
                    raise ValueError(
                        "Código duplicado no arquivo."
                    )

                codigos_vistos.add(codigo)
                validos.append(registro)

            except (ValueError, TypeError) as erro:
                rejeitados.append({
                    "linha": numero_linha,
                    "erro": str(erro),
                })

        comando = text("""
            INSERT INTO cotacao.cotacoes (
                cod_cotacao,
                item_id,
                fornecedor_id,
                data_cotacao,
                validade,
                preco_original,
                moeda_original,
                unidade,
                observacoes
            )
            VALUES (
                CAST(:cod_cotacao AS VARCHAR(80)),
                :item_id,
                :fornecedor_id,
                CAST(:data_cotacao AS DATE),
                CAST(:validade AS DATE),
                CAST(:preco_original AS NUMERIC(18,6)),
                CAST(:moeda_original AS CHAR(3)),
                CAST(:unidade AS VARCHAR(20)),
                CAST(:observacoes AS TEXT)
            )
            ON CONFLICT (cod_cotacao)
            DO UPDATE SET
                item_id = EXCLUDED.item_id,
                fornecedor_id = EXCLUDED.fornecedor_id,
                data_cotacao = EXCLUDED.data_cotacao,
                validade = EXCLUDED.validade,
                preco_original = EXCLUDED.preco_original,
                moeda_original = EXCLUDED.moeda_original,
                unidade = EXCLUDED.unidade,
                observacoes = EXCLUDED.observacoes
        """)

        if validos:
            with engine.begin() as conn:
                conn.execute(comando, validos)

        print(f"Linhas válidas processadas: {len(validos)}")
        print(f"Linhas rejeitadas: {len(rejeitados)}")

        for erro in rejeitados:
            print(
                f"Linha {erro['linha']}: {erro['erro']}"
            )

        return {
            "processados": len(validos),
            "rejeitados": rejeitados,
        }

    finally:
        engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python -m src.cotacao.importar_cotacoes "
            "caminho_do_arquivo"
        )

    importar_cotacoes(sys.argv[1])

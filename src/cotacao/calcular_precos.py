
"""
Motor de conversão cambial de insumos agrícolas.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from src.cotacao.queries_cotacao import consultar_cambio


def converter_preco(
    preco: Decimal,
    moeda_origem: str,
    moeda_destino: str,
    data_referencia: date,
) -> dict:
    """
    Converte preços entre BRL e USD usando a PTAX.

    A convenção inicial é:
    - USD -> BRL: taxa de venda
    - BRL -> USD: taxa de compra

    Essas taxas são referências para simulação,
    não custos garantidos de uma operação bancária.
    """

    moedas_validas = {"BRL", "USD"}

    moeda_origem = moeda_origem.upper()
    moeda_destino = moeda_destino.upper()

    if (
        moeda_origem not in moedas_validas
        or moeda_destino not in moedas_validas
    ):
        raise ValueError("Moeda inválida. Use BRL ou USD.")

    preco = Decimal(str(preco))

    if not preco.is_finite() or preco < 0:
        raise ValueError("O preço deve ser finito e não negativo.")

    if moeda_origem == moeda_destino:
        return {
            "preco_original": preco,
            "preco_convertido": preco,
            "moeda": moeda_destino,
            "taxa_utilizada": None,
            "data_cambio": None,
        }

    cambio = consultar_cambio(data_referencia)

    if cambio is None:
        raise ValueError(
            "Nenhuma cotação disponível até a data solicitada."
        )

    if moeda_origem == "USD":
        taxa = Decimal(str(cambio["venda"]))
        convertido = preco * taxa
    else:
        taxa = Decimal(str(cambio["compra"]))
        convertido = preco / taxa

    convertido = convertido.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return {
        "preco_original": preco,
        "preco_convertido": convertido,
        "moeda": moeda_destino,
        "taxa_utilizada": taxa,
        "data_cambio": cambio["data_referencia"],
    }

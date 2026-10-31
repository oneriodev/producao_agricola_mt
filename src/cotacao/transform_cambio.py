
"""
Transformação dos dados cambiais da API PTAX.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation


def transformar_cambio(dados: dict | None) -> dict | None:
    """
    Valida e padroniza uma cotação retornada pelo BCB.
    """

    if dados is None:
        return None

    # Converte a data/hora da API para datetime.
    data_hora = datetime.fromisoformat(
        dados["dataHoraCotacao"]
    )

    if data_hora.tzinfo is not None:
        raise ValueError(
            "Esperada data/hora PTAX sem fuso horário."
        )

    try:
        # Decimal evita erros de precisão do float.
        compra = Decimal(str(dados["cotacaoCompra"]))
        venda = Decimal(str(dados["cotacaoVenda"]))

    except (InvalidOperation, TypeError) as erro:
        raise ValueError(
            "Cotação cambial inválida."
        ) from erro

    if not compra.is_finite() or not venda.is_finite():
        raise ValueError("Cotação não finita.")

    if compra <= 0 or venda <= 0:
        raise ValueError("Valores cambiais devem ser positivos.")

    return {
        "data_referencia": data_hora.date(),
        "data_hora_cotacao": data_hora,
        "moeda": "USD",
        "compra": compra,
        "venda": venda,
        "fonte": "BCB_PTAX",
    }


from datetime import date
import requests

# Endpoint público do Banco Central
URL_PTAX = (
    "https://olinda.bcb.gov.br/olinda/servico/"
    "PTAX/versao/v1/odata/"
    "CotacaoDolarDia(dataCotacao=@dataCotacao)"
)


def extrair_ptax(data_referencia: date):
    """Consulta a PTAX do dólar para uma determinada data."""

    parametros = {
        "@dataCotacao": f"'{data_referencia:%m-%d-%Y}'",
        "$format": "json",
    }

    resposta = requests.get(
        URL_PTAX,
        params=parametros,
        timeout=20,
    )

    resposta.raise_for_status()

    dados = resposta.json().get("value", [])

    if not dados:
        return None

    return dados[-1]



def extrair_ptax_periodo(
    data_inicial: date,
    data_final: date,
) -> list[dict]:
    """Consulta cotações PTAX por período, com paginação."""

    if data_inicial > data_final:
        raise ValueError(
            "A data inicial não pode superar a data final."
        )

    url = (
        "https://olinda.bcb.gov.br/olinda/servico/"
        "PTAX/versao/v1/odata/"
        "CotacaoDolarPeriodo("
        "dataInicial=@dataInicial,"
        "dataFinalCotacao=@dataFinalCotacao)"
    )

    tamanho_pagina = 100
    deslocamento = 0
    resultados = []

    with requests.Session() as sessao:
        while True:
            parametros = {
                "@dataInicial": f"'{data_inicial:%m-%d-%Y}'",
                "@dataFinalCotacao": f"'{data_final:%m-%d-%Y}'",
                "$format": "json",
                "$top": tamanho_pagina,
                "$skip": deslocamento,
            }

            resposta = sessao.get(
                url,
                params=parametros,
                timeout=30,
            )

            if not resposta.ok:
                print("Erro na API PTAX:")
                print("URL:", resposta.url)
                print("Resposta:", resposta.text[:1500])
                resposta.raise_for_status()

            dados = resposta.json()
            lote = dados.get("value", [])

            if not isinstance(lote, list):
                raise ValueError(
                    "Resposta inesperada da API PTAX."
                )

            resultados.extend(lote)

            if len(lote) < tamanho_pagina:
                break

            deslocamento += tamanho_pagina

    # Ordenação realizada no Python
    resultados.sort(
        key=lambda item: item["dataHoraCotacao"]
    )

    return resultados



if __name__ == "__main__":

    # Data utilizada para validar a integração
    data_teste = date(2026, 10, 29)

    cotacao = extrair_ptax(data_teste)

    if cotacao:
        print("Data/hora:", cotacao["dataHoraCotacao"])
        print("Compra (BRL/USD):", cotacao["cotacaoCompra"])
        print("Venda (BRL/USD):", cotacao["cotacaoVenda"])
    else:
        print("Nenhuma PTAX disponível nessa data.")

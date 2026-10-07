"""
Extração da malha municipal de Mato Grosso (API de Malhas do IBGE).

O que este módulo faz:
    1. Baixa os contornos (polígonos) dos municípios de MT em formato GeoJSON.
    2. Valida o arquivo (quantidade de municípios e presença do código IBGE).
    3. Salva localmente, para o painel não depender da internet a cada execução.

Execute a partir da RAIZ do projeto:
    python -m extract.malha_mt
"""

import json
import logging
from pathlib import Path
from src.config import MALHA_MT_PATH

import requests

logger = logging.getLogger(__name__)

# --- Configurações -----------------------------------------------------------
# Código IBGE da UF de Mato Grosso (os códigos de município de MT começam com 51).
CODIGO_UF_MT = 51

# Endpoint da API de Malhas v3 do IBGE. {uf} é preenchido em tempo de execução.
URL_MALHA = "https://servicodados.ibge.gov.br/api/v3/malhas/estados/{uf}"

# Onde o arquivo será salvo (caminho relativo à raiz do projeto).
CAMINHO_SAIDA = MALHA_MT_PATH

# MT tem 141 ou 142 municípios, conforme a versão da malha
# (Boa Esperança do Norte foi instalado recentemente).
QTD_MIN, QTD_MAX = 141, 142


# --- Extração ----------------------------------------------------------------
def baixar_malha(codigo_uf: int = CODIGO_UF_MT, qualidade: str = "intermediaria") -> dict:
    """Baixa a malha municipal de uma UF e devolve o GeoJSON como dicionário.

    Args:
        codigo_uf: código IBGE da UF (51 = MT).
        qualidade: nível de detalhe dos contornos ("minima", "intermediaria"
            ou "maxima"). Quanto maior, mais pesado o arquivo e o mapa.
    """
    params = {
        "formato": "application/vnd.geo+json",  # pede GeoJSON em vez de TopoJSON
        "intrarregiao": "municipio",            # divide a UF em municípios
        "qualidade": qualidade,
    }
    url = URL_MALHA.format(uf=codigo_uf)
    logger.info("Baixando malha de %s (qualidade=%s)...", url, qualidade)

    # timeout evita que o script fique travado para sempre se a API não responder
    resposta = requests.get(url, params=params, timeout=60)
    # Lança erro se o status HTTP for 4xx/5xx, em vez de seguir com dados ruins
    resposta.raise_for_status()
    return resposta.json()


# --- Validação ---------------------------------------------------------------
def validar_malha(geojson: dict) -> None:
    """Confere se o GeoJSON tem o formato e o conteúdo esperados.

    Lança ValueError se algo estiver errado: é melhor falhar aqui do que
    descobrir o problema com o mapa em branco no painel.
    """
    if geojson.get("type") != "FeatureCollection":
        raise ValueError(f"Esperava FeatureCollection, veio: {geojson.get('type')}")

    features = geojson.get("features", [])
    qtd = len(features)
    if not QTD_MIN <= qtd <= QTD_MAX:
        raise ValueError(f"Quantidade inesperada de municípios: {qtd}")

    for feature in features:
        codigo = str(feature.get("properties", {}).get("codarea", ""))
        # Código de município IBGE: 7 dígitos, começando com o código da UF
        if len(codigo) != 7 or not codigo.startswith(str(CODIGO_UF_MT)):
            raise ValueError(f"Código de município inválido: {codigo!r}")

    logger.info("Malha válida: %d municípios.", qtd)


# --- Carga (arquivo local) ---------------------------------------------------
def salvar_malha(geojson: dict, caminho: Path = CAMINHO_SAIDA) -> None:
    """Salva o GeoJSON em disco, criando as pastas se necessário."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    tamanho_kb = caminho.stat().st_size / 1024
    logger.info("Arquivo salvo em %s (%.0f KB).", caminho, tamanho_kb)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Idempotência: se o arquivo já existe, não baixa de novo.
    # Para forçar novo download, apague o arquivo.
    if CAMINHO_SAIDA.exists():
        logger.info("Malha já existe em %s. Nada a fazer.", CAMINHO_SAIDA)
        return

    geojson = baixar_malha()
    validar_malha(geojson)
    salvar_malha(geojson)


if __name__ == "__main__":
    main()
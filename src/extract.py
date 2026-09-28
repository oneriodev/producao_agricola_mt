"""
Etapa de EXTRAÇÃO do pipeline.

Busca na API SIDRA/IBGE os dados da Produção Agrícola Municipal (PAM)
dos municípios de Mato Grosso e salva o resultado BRUTO (sem nenhum
tratamento) em data/raw/. A limpeza fica a cargo do transform.py.

Como executar (a partir da raiz do projeto):
    python -m src.extract
"""

import time

import pandas as pd
import requests

from src.config import (
    PERIODO,
    PRODUTOS,
    RAW_DIR,
    SIDRA_BASE_URL,
    SIDRA_CLASSIFICACAO,
    SIDRA_TABELA,
    UF_CODIGO,
    VARIAVEIS,
)

# Tempo máximo (segundos) esperando a resposta da API
TIMEOUT = 60
# Pausa (segundos) entre requisições, para não sobrecarregar a API pública
PAUSA_ENTRE_REQUISICOES = 1


def montar_url(codigo_produto: str) -> str:
    """Monta a URL da API SIDRA para um produto específico."""
    # Junta os códigos das variáveis separados por vírgula: "8331,216,214,..."
    codigos_variaveis = ",".join(VARIAVEIS.keys())

    return (
        f"{SIDRA_BASE_URL}"
        f"/t/{SIDRA_TABELA}"                        # tabela
        f"/n6/in n3 {UF_CODIGO}"                    # municípios dentro da UF
        f"/v/{codigos_variaveis}"                   # variáveis
        f"/p/{PERIODO}"                             # período
        f"/c{SIDRA_CLASSIFICACAO}/{codigo_produto}" # produto
    )


def buscar_produto(codigo_produto: str) -> pd.DataFrame:
    """Consulta a API para um produto e devolve os dados em um DataFrame."""
    url = montar_url(codigo_produto)

    resposta = requests.get(url, timeout=TIMEOUT)
    # Se a API devolver erro HTTP (404, 500...), interrompe com uma exceção
    resposta.raise_for_status()

    dados = resposta.json()

    # O 1º item da lista é um cabeçalho descritivo, não um dado.
    # "cabecalho" recebe o 1º item; "linhas" recebe todo o resto.
    cabecalho, *linhas = dados

    return pd.DataFrame(linhas)


def extrair_dados() -> pd.DataFrame:
    """Busca todos os produtos configurados e junta em um único DataFrame."""
    partes = []

    for codigo, nome in PRODUTOS.items():
        print(f"Buscando {nome} (código {codigo})...")
        df_produto = buscar_produto(codigo)
        print(f"  -> {len(df_produto)} linhas recebidas")
        partes.append(df_produto)

        time.sleep(PAUSA_ENTRE_REQUISICOES)

    # Empilha os DataFrames de cada produto; ignore_index renumera as linhas
    return pd.concat(partes, ignore_index=True)


def salvar_bruto(df: pd.DataFrame, nome_arquivo: str = "pam_mt_bruto.csv"):
    """Salva o DataFrame bruto em data/raw/ e devolve o caminho do arquivo."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)  # cria a pasta se não existir
    caminho = RAW_DIR / nome_arquivo
    df.to_csv(caminho, index=False, encoding="utf-8")
    return caminho


if __name__ == "__main__":
    df = extrair_dados()
    caminho = salvar_bruto(df)
    print(f"\nTotal: {len(df)} linhas salvas em {caminho}")
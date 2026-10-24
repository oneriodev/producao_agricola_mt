"""
Construção das features dos modelos de Machine Learning.

Execute (raiz do projeto, banco no ar):
    python -m src.ml.features
"""

import numpy as np
import pandas as pd

from src import queries

# Culturas com coluna própria; as demais são somadas em "outras"
CULTURAS_PRINCIPAIS = {"Soja": "soja", "Milho": "milho", "Algodão herbáceo": "algodao"}
GRUPOS = ["soja", "milho", "algodao", "outras"]

# Período que descreve o perfil ATUAL de cada município (média de 5 safras)
PERIODO_RECENTE = (2021, 2025)
# Períodos comparados para medir o crescimento da área (médias de 3 anos)
PERIODO_BASE = (2013, 2015)
PERIODO_FINAL = (2023, 2025)

# Colunas que entram no K-Means (as demais são só para exibição)
FEATURES_CLUSTER = [
    "part_soja",
    "part_milho",
    "part_algodao",
    "part_outras",
    "log_area_media",
    "indice_produtividade",
    "crescimento_area_log",
]


def carregar_producao() -> pd.DataFrame:
    """Lê a produção completa do banco (sql/ml_producao_completa.sql)."""
    return queries.executar("ml_producao_completa")


def _no_periodo(df: pd.DataFrame, inicio: int, fim: int) -> pd.DataFrame:
    """Filtra as linhas com ano entre inicio e fim (inclusive)."""
    return df[df["ano"].between(inicio, fim)]


def participacao_culturas(df: pd.DataFrame) -> pd.DataFrame:
    """Fração da área plantada em cada grupo de cultura + área média anual."""
    recente = _no_periodo(df, *PERIODO_RECENTE).copy()
    recente["grupo"] = recente["produto"].map(CULTURAS_PRINCIPAIS).fillna("outras")

    # Linhas = municípios, colunas = grupos, valores = área somada no período
    area = recente.pivot_table(
        index="cod_municipio",
        columns="grupo",
        values="area_plantada_ha",
        aggfunc="sum",
        fill_value=0,
    ).reindex(columns=GRUPOS, fill_value=0)  # garante as 4 colunas, na ordem

    total = area.sum(axis=1)
    participacao = area.div(total, axis=0).add_prefix("part_")  # cada linha soma 1

    anos = PERIODO_RECENTE[1] - PERIODO_RECENTE[0] + 1
    participacao["area_media_ha"] = total / anos
    return participacao


def indice_produtividade(df: pd.DataFrame) -> pd.Series:
    """Produtividade do município relativa ao estado (1,0 = média de MT).

    Para cada município, cultura e ano: rendimento_municipio / rendimento_estado.
    Depois, média desses índices ponderada pela área colhida.
    """
    recente = _no_periodo(df, *PERIODO_RECENTE).dropna(
        subset=["rendimento_kg_ha", "area_colhida_ha", "quantidade_t"]
    )
    recente = recente[recente["area_colhida_ha"] > 0]

    # Rendimento do estado = produção total / área total (média ponderada)
    estado = recente.groupby(["produto", "ano"]).agg(
        producao_t=("quantidade_t", "sum"), area_ha=("area_colhida_ha", "sum")
    )
    estado["rendimento_estado"] = estado["producao_t"] * 1000 / estado["area_ha"]

    recente = recente.join(estado["rendimento_estado"], on=["produto", "ano"])
    recente["relativo"] = recente["rendimento_kg_ha"] / recente["rendimento_estado"]
    recente["relativo_x_area"] = recente["relativo"] * recente["area_colhida_ha"]

    por_municipio = recente.groupby("cod_municipio")
    indice = (
        por_municipio["relativo_x_area"].sum() / por_municipio["area_colhida_ha"].sum()
    )
    return indice.rename("indice_produtividade")


def crescimento_area(df: pd.DataFrame) -> pd.Series:
    """Crescimento da área plantada total, em escala log, entre dois períodos."""

    def area_media(inicio: int, fim: int) -> pd.Series:
        trecho = _no_periodo(df, inicio, fim)
        # min_count=1: se TODOS os valores forem NaN, o resultado é NaN (e não 0).
        # Sem isso, um município que não existia teria área base 0 e
        # "crescimento infinito".
        area_ano = trecho.groupby(["cod_municipio", "ano"])["area_plantada_ha"].sum(
            min_count=1
        )
        return area_ano.groupby("cod_municipio").mean()

    base = area_media(*PERIODO_BASE)
    final = area_media(*PERIODO_FINAL)
    # Diferença de logs = log da razão; log1p evita problema com área zero
    return (np.log1p(final) - np.log1p(base)).rename("crescimento_area_log")


def features_clusterizacao(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Uma linha por município, com as features da clusterização."""
    if df is None:
        df = carregar_producao()

    nomes = df.drop_duplicates("cod_municipio").set_index("cod_municipio")["municipio"]

    features = pd.concat(
        [participacao_culturas(df), indice_produtividade(df), crescimento_area(df)],
        axis=1,
    )
    features["log_area_media"] = np.log1p(features["area_media_ha"])
    features.insert(0, "municipio", nomes)
    return features


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)

    feats = features_clusterizacao()
    print(f"Municípios: {len(feats)}")
    print("\nValores ausentes por coluna:")
    print(feats[FEATURES_CLUSTER].isna().sum())

    incompletos = feats[feats[FEATURES_CLUSTER].isna().any(axis=1)]
    print(f"\nExcluídos da clusterização ({len(incompletos)}):")
    print(incompletos["municipio"].tolist())

    print("\nResumo estatístico:")
    print(feats[FEATURES_CLUSTER].describe().round(3))
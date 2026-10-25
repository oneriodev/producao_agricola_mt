"""
Previsão da produtividade (kg/ha) por município.

Etapa 4: avalia os BASELINES com validação temporal. Eles são a régua
que qualquer modelo de ML precisa superar.

Execute (raiz do projeto, banco no ar):
    python -m src.ml.previsao
"""

import pandas as pd

from src.ml.features import ALVO, FEATURES_PREVISAO, features_previsao

ANOS_VALIDACAO = range(2020, 2026)  # cada ano é previsto "como se fosse aquele momento"

# Nome do baseline -> coluna que ele usa como previsão
BASELINES = {
    "baseline_ano_anterior": "rend_lag1",
    "baseline_media_3_anos": "rend_media3",
}


def linhas_avaliaveis(dados: pd.DataFrame) -> pd.DataFrame:
    """Linhas com alvo e TODAS as features.

    É o mesmo conjunto para todos os modelos: comparação justa.
    """
    return dados.dropna(subset=[ALVO] + FEATURES_PREVISAO)


def metricas(real: pd.Series, previsto: pd.Series) -> dict:
    erro = (real - previsto).abs()
    return {
        "mae_kg_ha": erro.mean(),
        "mape_pct": (erro / real).mean() * 100,
        "n_previsoes": len(real),
    }


def avaliar_baselines(dados: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Erro de cada baseline por ano e no período de validação inteiro."""
    avaliaveis = linhas_avaliaveis(dados)
    validacao = avaliaveis[avaliaveis["ano"].isin(ANOS_VALIDACAO)]

    por_ano = pd.DataFrame([
        {"ano": ano, "modelo": nome, **metricas(grupo[ALVO], grupo[coluna])}
        for ano, grupo in validacao.groupby("ano")
        for nome, coluna in BASELINES.items()
    ])
    geral = pd.DataFrame([
        {"modelo": nome, **metricas(validacao[ALVO], validacao[coluna])}
        for nome, coluna in BASELINES.items()
    ])
    return por_ano, geral


def main() -> None:
    pd.set_option("display.width", 200)

    dados = features_previsao()
    por_ano, geral = avaliar_baselines(dados)

    print("=== Erro no período de validação (2020-2025) ===")
    print(geral.round(1).to_string(index=False))

    print("\n=== MAE (kg/ha) por ano ===")
    print(por_ano.pivot(index="ano", columns="modelo", values="mae_kg_ha").round(0))


if __name__ == "__main__":
    main()
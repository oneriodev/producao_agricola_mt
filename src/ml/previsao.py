"""
Previsão da produtividade (kg/ha) por município.

Compara, com validação temporal walk-forward (2020-2025):
    - baselines: "ano anterior" e "média dos 3 anos anteriores";
    - Random Forest prevendo a produtividade diretamente;
    - Random Forest prevendo a VARIAÇÃO em relação à média de 3 anos.

Execute (raiz do projeto, banco no ar):
    python -m src.ml.previsao
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from src.ml.features import ALVO, FEATURES_PREVISAO, features_previsao

ANOS_VALIDACAO = range(2020, 2026)

# Nome do baseline -> coluna que ele usa como previsão
BASELINES = {
    "baseline_ano_anterior": "rend_lag1",
    "baseline_media_3_anos": "rend_media3",
}

# Nome do modelo -> se ele prevê a variação em relação à média de 3 anos
MODELOS_RF = {
    "rf_direto": False,
    "rf_variacao": True,
}

MODELOS = list(BASELINES) + list(MODELOS_RF)
REFERENCIA = "baseline_media_3_anos"  # a régua: o baseline mais forte

PARAMETROS_RF = {
    "n_estimators": 300,     # número de árvores
    "min_samples_leaf": 5,   # cada folha com pelo menos 5 exemplos (evita decorar)
    "random_state": 42,      # reprodutível
    "n_jobs": -1,            # usa todos os núcleos do processador
}


def linhas_avaliaveis(dados: pd.DataFrame) -> pd.DataFrame:
    """Linhas com alvo e TODAS as features: o mesmo conjunto para todos os modelos."""
    return dados.dropna(subset=[ALVO] + FEATURES_PREVISAO)


def treinar_rf(treino: pd.DataFrame, prever_variacao: bool) -> RandomForestRegressor:
    """Treina um Random Forest com o valor direto ou com a variação."""
    if prever_variacao:
        y = treino[ALVO] - treino["rend_media3"]  # quanto o ano desviou da média recente
    else:
        y = treino[ALVO]
    return RandomForestRegressor(**PARAMETROS_RF).fit(treino[FEATURES_PREVISAO], y)


def prever_rf(modelo, linhas: pd.DataFrame, prever_variacao: bool) -> pd.Series:
    """Devolve a produtividade prevista (kg/ha), alinhada às linhas recebidas."""
    previsto = pd.Series(modelo.predict(linhas[FEATURES_PREVISAO]), index=linhas.index)
    if prever_variacao:
        return linhas["rend_media3"] + previsto  # média recente + desvio previsto
    return previsto


def validacao_temporal(dados: pd.DataFrame) -> pd.DataFrame:
    """Prevê cada ano de validação treinando SÓ com os anos anteriores a ele.

    Devolve uma linha por município e ano, com o valor real e a previsão
    de cada modelo em uma coluna.
    """
    avaliaveis = linhas_avaliaveis(dados)
    resultados = []

    for ano in ANOS_VALIDACAO:
        treino = avaliaveis[avaliaveis["ano"] < ano]   # só o passado
        teste = avaliaveis[avaliaveis["ano"] == ano]   # o ano a prever

        resultado = teste[["cod_municipio", "municipio", "ano", ALVO]].copy()
        for nome, coluna in BASELINES.items():
            resultado[nome] = teste[coluna]
        for nome, prever_variacao in MODELOS_RF.items():
            modelo = treinar_rf(treino, prever_variacao)
            resultado[nome] = prever_rf(modelo, teste, prever_variacao)

        resultados.append(resultado)

    return pd.concat(resultados, ignore_index=True)


def metricas(real: pd.Series, previsto: pd.Series) -> dict:
    erro = (real - previsto).abs()
    return {
        "mae_kg_ha": erro.mean(),
        "mape_pct": (erro / real).mean() * 100,
        "n_previsoes": len(real),
    }


def resumir_erros(previsoes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Erro de cada modelo no período inteiro e ano a ano."""
    geral = pd.DataFrame([
        {"modelo": modelo, **metricas(previsoes[ALVO], previsoes[modelo])}
        for modelo in MODELOS
    ]).set_index("modelo")

    # Ganho em relação à régua: positivo = o modelo errou MENOS que o baseline
    mae_referencia = geral.loc[REFERENCIA, "mae_kg_ha"]
    geral["ganho_vs_media3_pct"] = (1 - geral["mae_kg_ha"] / mae_referencia) * 100

    por_ano = pd.DataFrame({
        ano: {modelo: (grupo[ALVO] - grupo[modelo]).abs().mean() for modelo in MODELOS}
        for ano, grupo in previsoes.groupby("ano")
    }).T  # .T: transposta, para ficar com os anos nas linhas

    return geral, por_ano


def importancia_features(dados: pd.DataFrame) -> pd.Series:
    """Quanto cada feature contribuiu no modelo de variação (treinado com tudo)."""
    modelo = treinar_rf(linhas_avaliaveis(dados), prever_variacao=True)
    return pd.Series(modelo.feature_importances_, index=FEATURES_PREVISAO).sort_values(
        ascending=False
    )


def main() -> None:
    pd.set_option("display.width", 200)

    dados = features_previsao()
    previsoes = validacao_temporal(dados)
    geral, por_ano = resumir_erros(previsoes)

    print("=== Erro no período de validação (2020-2025) ===")
    print(geral.round(1).to_string())

    print("\n=== MAE (kg/ha) por ano ===")
    print(por_ano.round(0).to_string())

    print("\n=== Importância das features (rf_variacao) ===")
    print(importancia_features(dados).round(3).to_string())


if __name__ == "__main__":
    main()

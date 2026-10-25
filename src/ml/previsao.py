"""
Previsão da produtividade (kg/ha) por município.

Compara, com validação temporal walk-forward (2020-2025):
    - baselines: "ano anterior" e "média dos 3 anos anteriores";
    - Random Forest prevendo a produtividade diretamente;
    - Random Forest prevendo a VARIAÇÃO em relação à média de 3 anos.

Depois prevê o ano seguinte (ex.: 2026) com todos os modelos e grava
tudo no banco. O modelo publicado é o de MENOR erro na validação.

Execute (raiz do projeto, banco no ar):
    python -m src.ml.previsao
"""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sqlalchemy import create_engine, insert

from src.config import DATABASE_URL, PRODUTOS
from src.ml.features import (
    ALVO,
    AREA_MINIMA_PREVISAO_HA,
    FEATURES_PREVISAO,
    PRODUTO_PREVISAO,
    features_previsao,
    features_proximo_ano,
)
from src.models import ExecucaoModelo, MetricaModelo, PrevisaoProdutividade

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


# --- Modelos -------------------------------------------------------------------

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


def prever_todos(treino: pd.DataFrame, linhas: pd.DataFrame) -> pd.DataFrame:
    """Previsão de todos os modelos para as linhas, treinando os RFs com 'treino'."""
    resultado = linhas[["cod_municipio", "municipio", "ano"]].copy()
    for nome, coluna in BASELINES.items():
        resultado[nome] = linhas[coluna]
    for nome, prever_variacao in MODELOS_RF.items():
        modelo = treinar_rf(treino, prever_variacao)
        resultado[nome] = prever_rf(modelo, linhas, prever_variacao)
    return resultado


# --- Validação e previsão do futuro ----------------------------------------------

def validacao_temporal(dados: pd.DataFrame) -> pd.DataFrame:
    """Prevê cada ano de validação treinando SÓ com os anos anteriores a ele."""
    avaliaveis = linhas_avaliaveis(dados)
    resultados = []

    for ano in ANOS_VALIDACAO:
        treino = avaliaveis[avaliaveis["ano"] < ano]   # só o passado
        teste = avaliaveis[avaliaveis["ano"] == ano]   # o ano a prever

        resultado = prever_todos(treino, teste)
        resultado[ALVO] = teste[ALVO]  # valor real, para calcular o erro
        resultados.append(resultado)

    return pd.concat(resultados, ignore_index=True)


def previsoes_futuras(dados: pd.DataFrame) -> pd.DataFrame:
    """Previsão do ano seguinte; os RFs treinam com TODOS os anos disponíveis."""
    return prever_todos(linhas_avaliaveis(dados), features_proximo_ano(dados))


# --- Métricas --------------------------------------------------------------------

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


# --- Gravação no banco -----------------------------------------------------------

def codigo_do_produto(nome: str) -> str:
    """Código IBGE da cultura a partir do nome (config.PRODUTOS: código -> nome)."""
    return next(codigo for codigo, produto in PRODUTOS.items() if produto == nome)


def formato_longo(previsoes: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """De uma coluna por modelo para uma LINHA por modelo (formato da tabela)."""
    longo = previsoes.melt(
        id_vars=["cod_municipio", "ano"],
        value_vars=MODELOS,
        var_name="modelo",
        value_name="previsto_kg_ha",
    )
    return longo.assign(tipo=tipo)


def gravar(engine, backtest, futuro, geral, escolhido) -> int:
    """Grava execução, previsões e métricas em UMA transação. Devolve o id."""
    cod_produto = codigo_do_produto(PRODUTO_PREVISAO)
    parametros = {
        "produto": PRODUTO_PREVISAO,
        "anos_validacao": list(ANOS_VALIDACAO),
        "area_minima_ha": AREA_MINIMA_PREVISAO_HA,
        "features": FEATURES_PREVISAO,
        "parametros_rf": PARAMETROS_RF,
        "modelo_escolhido": escolhido,
        "criterio": "menor MAE na validação temporal",
    }

    linhas = pd.concat(
        [formato_longo(backtest, "backtest"), formato_longo(futuro, "futuro")],
        ignore_index=True,
    )
    previsoes = [
        {
            "cod_municipio": linha.cod_municipio,
            "cod_produto": cod_produto,
            "ano_alvo": int(linha.ano),
            "modelo": linha.modelo,
            "tipo": linha.tipo,
            "previsto_kg_ha": float(linha.previsto_kg_ha),  # float(): tipo do numpy
        }
        for linha in linhas.itertuples()
    ]
    metricas_modelos = [
        {
            "cod_produto": cod_produto,
            "modelo": modelo,
            "mae_kg_ha": float(linha["mae_kg_ha"]),
            "mape_pct": float(linha["mape_pct"]),
            "n_previsoes": int(linha["n_previsoes"]),
        }
        for modelo, linha in geral.iterrows()
    ]

    with engine.begin() as conn:  # se algo falhar, nada é gravado
        execucao_id = conn.execute(
            insert(ExecucaoModelo)
            .values(tipo="previsao", parametros=parametros)
            .returning(ExecucaoModelo.id)
        ).scalar_one()

        conn.execute(
            insert(PrevisaoProdutividade),
            [{"execucao_id": execucao_id, **p} for p in previsoes],
        )
        conn.execute(
            insert(MetricaModelo),
            [{"execucao_id": execucao_id, **m} for m in metricas_modelos],
        )
    return execucao_id


# --- Execução --------------------------------------------------------------------

def main() -> None:
    pd.set_option("display.width", 200)

    dados = features_previsao()
    backtest = validacao_temporal(dados)
    geral, por_ano = resumir_erros(backtest)
    escolhido = geral["mae_kg_ha"].idxmin()  # o modelo de menor erro é o publicado
    futuro = previsoes_futuras(dados)

    print("=== Erro no período de validação (2020-2025) ===")
    print(geral.round(1).to_string())

    print("\n=== MAE (kg/ha) por ano ===")
    print(por_ano.round(0).to_string())

    print("\n=== Importância das features (rf_variacao) ===")
    print(importancia_features(dados).round(3).to_string())

    execucao_id = gravar(create_engine(DATABASE_URL), backtest, futuro, geral, escolhido)

    ano_futuro = int(futuro["ano"].iloc[0])
    print(f"\nModelo escolhido: {escolhido}")
    print(f"Execução {execucao_id} gravada: {len(backtest)} previsões de validação e "
          f"{len(futuro)} municípios com previsão para {ano_futuro} (x {len(MODELOS)} modelos)")


if __name__ == "__main__":
    main()

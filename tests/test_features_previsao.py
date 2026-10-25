"""
Testes das features de previsão: garantem que não há vazamento de dados.

Execute (raiz do projeto):
    python -m pytest -v
"""

import pandas as pd
import pytest

from src.ml.features import features_previsao


def _producao(rendimentos: dict[int, float], area: float = 5_000) -> pd.DataFrame:
    """Monta uma produção FALSA de um município, com valores conhecidos."""
    return pd.DataFrame([
        {
            "cod_municipio": "5100000",
            "municipio": "Teste",
            "produto": "Soja",
            "ano": ano,
            "area_plantada_ha": area,
            "area_colhida_ha": area,
            "quantidade_t": rendimento * area / 1000,
            "rendimento_kg_ha": rendimento,
        }
        for ano, rendimento in rendimentos.items()
    ])


def _linha(resultado: pd.DataFrame, ano: int) -> pd.Series:
    return resultado[resultado["ano"] == ano].iloc[0]


def test_media3_usa_so_anos_anteriores():
    # 2013 tem um valor absurdo: se ele "vazar" para a média, o teste pega
    dados = _producao({2010: 1000, 2011: 2000, 2012: 3000, 2013: 9999})
    linha = _linha(features_previsao(dados), 2013)

    assert linha["rend_lag1"] == 3000
    assert linha["rend_media3"] == pytest.approx(2000)  # (1000 + 2000 + 3000) / 3


def test_ano_faltante_nao_e_pulado():
    # 2012 sem registro: o "ano anterior" de 2013 é desconhecido, e não 2011
    dados = _producao({2010: 1000, 2011: 2000, 2013: 4000})
    linha = _linha(features_previsao(dados), 2013)

    assert pd.isna(linha["rend_lag1"])


def test_area_pequena_vira_desconhecida():
    dados = _producao({2010: 1000, 2011: 2000}, area=10)
    resultado = features_previsao(dados)

    assert resultado["rendimento_kg_ha"].isna().all()
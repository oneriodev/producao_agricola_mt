"""
Etapa de TRANSFORMAÇÃO do pipeline.

Lê os dados brutos extraídos da API SIDRA (data/raw/), limpa, padroniza
e reorganiza no formato "largo" (uma linha por município + produto + ano,
uma coluna por variável). Salva o resultado em data/processed/.

Regras de conversão dos valores (padrão IBGE):
    "-"   -> 0    (zero: não houve produção)
    "..." -> NaN  (dado não disponível)

Como executar (a partir da raiz do projeto):
    python -m src.transform
"""

import pandas as pd

from src.config import PROCESSED_DIR, PRODUTOS, RAW_DIR

ARQUIVO_BRUTO = RAW_DIR / "pam_mt_bruto.csv"
ARQUIVO_TRATADO = PROCESSED_DIR / "pam_mt_tratado.csv"

# Colunas úteis do arquivo bruto -> novos nomes
COLUNAS = {
    "D1C": "cod_municipio",
    "D1N": "municipio",
    "D2C": "cod_variavel",
    "D3N": "ano",
    "D4C": "cod_produto",
    "V": "valor",
}

# Código da variável no SIDRA -> nome da coluna no formato largo
VARIAVEIS_COLUNAS = {
    "8331": "area_plantada_ha",
    "216": "area_colhida_ha",
    "214": "quantidade_t",
    "112": "rendimento_kg_ha",
    "215": "valor_producao_mil_reais",
}

# Colunas que identificam cada linha no formato largo
CHAVES = ["cod_municipio", "municipio", "cod_produto", "produto", "ano"]


def carregar_bruto(caminho=ARQUIVO_BRUTO) -> pd.DataFrame:
    """Lê o CSV bruto mantendo tudo como texto (igual veio da API)."""
    return pd.read_csv(caminho, dtype=str)


def selecionar_e_renomear(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém só as colunas úteis e dá nomes legíveis a elas."""
    return df[list(COLUNAS)].rename(columns=COLUNAS)


def converter_valores(serie: pd.Series) -> pd.Series:
    """Converte a coluna de valores de texto para número."""
    # "-" significa zero no padrão do IBGE
    serie = serie.replace("-", "0")

    # errors="coerce": o que não for número (ex.: "...") vira NaN
    numeros = pd.to_numeric(serie, errors="coerce")

    # Avisa quantos valores ficaram vazios, para não esconder surpresas
    vazios = numeros.isna().sum()
    print(f"  Valores sem informação (viraram vazio): {vazios}")

    return numeros


def limpar(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza textos, tipos e valores."""
    df = df.copy()  # não altera o DataFrame original

    # "Sorriso - MT" -> "Sorriso"
    df["municipio"] = df["municipio"].str.removesuffix(" - MT")

    # "40124" -> "Soja" (nomes curtos definidos no config.py)
    df["produto"] = df["cod_produto"].map(PRODUTOS)

    # "214" -> "quantidade_t" (nome da futura coluna)
    df["variavel"] = df["cod_variavel"].map(VARIAVEIS_COLUNAS)

    df["ano"] = df["ano"].astype(int)
    df["valor"] = converter_valores(df["valor"])

    return df


def pivotar(df: pd.DataFrame) -> pd.DataFrame:
    """Converte do formato longo para o largo (uma coluna por variável)."""
    # pivot (e não pivot_table) dá ERRO se houver duplicatas,
    # em vez de tirar uma média escondida delas.
    largo = df.pivot(index=CHAVES, columns="variavel", values="valor")

    # Transforma o índice de volta em colunas normais
    largo = largo.reset_index()
    largo.columns.name = None  # remove o nome "variavel" do cabeçalho

    # Garante a ordem das colunas: chaves primeiro, depois as variáveis
    return largo[CHAVES + list(VARIAVEIS_COLUNAS.values())]


def validar(df: pd.DataFrame) -> None:
    """Confere se o resultado faz sentido. Interrompe se algo estiver errado."""
    esperado = (
        df["cod_municipio"].nunique()
        * df["cod_produto"].nunique()
        * df["ano"].nunique()
    )
    assert len(df) == esperado, f"Esperava {esperado} linhas, veio {len(df)}"

    duplicadas = df.duplicated(subset=["cod_municipio", "cod_produto", "ano"])
    assert not duplicadas.any(), f"{duplicadas.sum()} linhas duplicadas"

    numericas = list(VARIAVEIS_COLUNAS.values())
    # fillna(0) só para a comparação: NaN não é negativo nem positivo
    assert (df[numericas].fillna(0) >= 0).all().all(), "Há valores negativos"

    print("  Validação OK")


def transformar(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Executa todas as etapas de transformação em sequência."""
    df = selecionar_e_renomear(df_bruto)
    df = limpar(df)
    df = pivotar(df)
    return df


def salvar_tratado(df: pd.DataFrame, caminho=ARQUIVO_TRATADO):
    """Salva o DataFrame tratado e devolve o caminho do arquivo."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8")
    return caminho


if __name__ == "__main__":
    print("Carregando dados brutos...")
    bruto = carregar_bruto()
    print(f"  {len(bruto)} linhas")

    print("Transformando...")
    tratado = transformar(bruto)
    validar(tratado)

    caminho = salvar_tratado(tratado)
    print(f"\nTotal: {len(tratado)} linhas salvas em {caminho}")
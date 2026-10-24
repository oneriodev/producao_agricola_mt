"""
Clusterização dos municípios de MT por perfil produtivo (K-Means).

Fluxo:
    1. monta as features (src/ml/features.py);
    2. separa por REGRA os municípios com área plantada < AREA_MINIMA_HA;
    3. padroniza e agrupa os demais com K-Means;
    4. dá nome a cada grupo a partir das suas características;
    5. grava execução, perfis e municípios no banco, em uma transação.

As escolhas (k = 5, 500 ha) vêm da exploração em notebooks/exploracao_clusters.ipynb.

Execute (raiz do projeto, banco no ar):
    python -m src.ml.clusterizacao
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine, insert

from src.config import DATABASE_URL
from src.ml.features import FEATURES_CLUSTER, features_clusterizacao
from src.models import ClusterMunicipio, ExecucaoModelo, PerfilCluster

# --- Parâmetros (definidos na exploração do notebook) -------------------------
K = 5
AREA_MINIMA_HA = 500
RANDOM_STATE = 42  # fixo: mesmo resultado a cada execução (reprodutível)
N_INIT = 10        # o K-Means roda 10 vezes e fica com a melhor

# Perfil definido por regra, fora do K-Means. -1 é uma convenção comum
# em clusterização para "fora dos grupos" (o DBSCAN usa -1 para ruído).
CLUSTER_REGRA = -1
NOME_REGRA = "Lavouras pouco expressivas"


def agrupar(feats: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Aplica a regra de área mínima e o K-Means.

    Devolve os municípios com a coluna 'cluster' e a silhueta do K-Means.
    """
    completos = feats.dropna(subset=FEATURES_CLUSTER)
    relevantes = completos[completos["area_media_ha"] >= AREA_MINIMA_HA]

    # Escalonamento SÓ com os relevantes (os pequenos distorceriam média e desvio)
    X = StandardScaler().fit_transform(relevantes[FEATURES_CLUSTER])
    modelo = KMeans(n_clusters=K, random_state=RANDOM_STATE, n_init=N_INIT).fit(X)

    resultado = completos.copy()
    resultado["cluster"] = CLUSTER_REGRA                    # todos começam na regra...
    resultado.loc[relevantes.index, "cluster"] = modelo.labels_  # ...relevantes recebem o grupo
    return resultado, float(silhouette_score(X, modelo.labels_))


def resumir(resultado: pd.DataFrame) -> pd.DataFrame:
    """Características médias de cada grupo, nas unidades originais."""
    return resultado.groupby("cluster").agg(
        municipios=("municipio", "count"),
        part_soja=("part_soja", "mean"),
        part_milho=("part_milho", "mean"),
        part_algodao=("part_algodao", "mean"),
        part_outras=("part_outras", "mean"),
        area_mediana_ha=("area_media_ha", "median"),
        crescimento_log=("crescimento_area_log", "median"),
    )


def nomear(resumo: pd.DataFrame) -> dict[int, str]:
    """Dá nome a cada grupo pelas CARACTERÍSTICAS, não pelo número.

    Os números (0 a K-1) mudam se os dados mudarem; as características, não.
    Falha de propósito se algum perfil deixar de ser claro: melhor um erro
    visível do que um nome errado no painel.
    """
    restantes = resumo.drop(index=CLUSTER_REGRA, errors="ignore")
    if len(restantes) != 5:
        raise ValueError(f"As regras de nome esperam 5 grupos; vieram {len(restantes)}.")

    nomes = {CLUSTER_REGRA: NOME_REGRA}

    canavieiro = restantes["part_outras"].idxmax()
    if restantes.loc[canavieiro, "part_outras"] < 0.5:
        raise ValueError("Nenhum grupo com mais de 50% de 'outras': revise no notebook.")
    nomes[canavieiro] = "Polo canavieiro"
    restantes = restantes.drop(index=canavieiro)

    algodao = restantes["part_algodao"].idxmax()
    if restantes.loc[algodao, "part_algodao"] < 0.08:
        raise ValueError("Nenhum grupo com algodão expressivo: revise no notebook.")
    nomes[algodao] = "Polo do algodão"
    restantes = restantes.drop(index=algodao)

    incipiente = restantes["area_mediana_ha"].idxmin()
    nomes[incipiente] = "Agricultura incipiente, com foco em milho"
    restantes = restantes.drop(index=incipiente)

    fronteira = restantes["crescimento_log"].idxmax()
    nomes[fronteira] = "Fronteira agrícola em expansão"
    restantes = restantes.drop(index=fronteira)

    nomes[restantes.index[0]] = "Polo soja-milho consolidado"
    return nomes


def descrever(linha: pd.Series) -> str:
    """Texto curto com as características do grupo (vai para o painel)."""
    area = f"{linha['area_mediana_ha']:,.0f}".replace(",", ".")  # 12,270 -> 12.270
    return (
        f"{int(linha['municipios'])} municípios; área plantada mediana de {area} ha; "
        f"soja {linha['part_soja']:.0%}, milho {linha['part_milho']:.0%}, "
        f"algodão {linha['part_algodao']:.0%}, outras culturas {linha['part_outras']:.0%}."
    )


def gravar(engine, resultado, resumo, nomes, silhueta) -> int:
    """Grava execução, perfis e municípios em UMA transação. Devolve o id."""
    parametros = {
        "k": K,
        "area_minima_ha": AREA_MINIMA_HA,
        "random_state": RANDOM_STATE,
        "n_init": N_INIT,
        "features": FEATURES_CLUSTER,
        "silhueta": round(silhueta, 4),
    }
    perfis = [
        {"cluster_id": int(cid), "nome": nomes[cid], "descricao": descrever(linha)}
        for cid, linha in resumo.iterrows()
    ]
    colunas_json = FEATURES_CLUSTER + ["area_media_ha"]
    municipios = [
        {
            "cod_municipio": cod,
            "cluster_id": int(linha["cluster"]),
            # float(): o JSON não aceita tipos do numpy
            "features": {c: round(float(linha[c]), 4) for c in colunas_json},
        }
        for cod, linha in resultado.iterrows()
    ]

    with engine.begin() as conn:  # se algo falhar, nada é gravado
        execucao_id = conn.execute(
            insert(ExecucaoModelo)
            .values(tipo="clusterizacao", parametros=parametros)
            .returning(ExecucaoModelo.id)  # o banco devolve o id gerado
        ).scalar_one()

        # Perfis antes dos municípios, por causa da chave estrangeira composta
        conn.execute(insert(PerfilCluster), [{"execucao_id": execucao_id, **p} for p in perfis])
        conn.execute(
            insert(ClusterMunicipio), [{"execucao_id": execucao_id, **m} for m in municipios]
        )
    return execucao_id


def main() -> None:
    pd.set_option("display.width", 200)

    feats = features_clusterizacao()
    sem_historico = feats[feats[FEATURES_CLUSTER].isna().any(axis=1)]["municipio"].tolist()

    resultado, silhueta = agrupar(feats)
    resumo = resumir(resultado)
    nomes = nomear(resumo)

    execucao_id = gravar(create_engine(DATABASE_URL), resultado, resumo, nomes, silhueta)

    print(f"Execução {execucao_id} gravada | silhueta: {silhueta:.3f}")
    print(f"Sem histórico (fora da clusterização): {sem_historico}\n")
    tabela = resumo.assign(nome=resumo.index.map(nomes)).sort_values(
        "municipios", ascending=False
    )
    print(tabela[["nome", "municipios", "part_soja", "part_milho", "part_algodao",
                  "part_outras", "area_mediana_ha"]].round(2).to_string())


if __name__ == "__main__":
    main()
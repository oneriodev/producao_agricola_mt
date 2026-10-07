"""
Painel da Produção Agrícola de Mato Grosso (Streamlit + Plotly).

Lê os dados do PostgreSQL através do módulo src/queries.py e exibe:
indicadores (KPIs), ranking de municípios, evolução por ano e
comparação entre culturas.

Como executar (a partir da raiz do projeto, com o banco no ar):
    python -m streamlit run app/app.py
"""

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src import queries
from src.config import MALHA_MT_PATH
from src.geo import orientar_para_plotly

TODO_ESTADO = "Todo o estado"

# Indicadores exibidos: rótulo na tela -> nome da coluna nos dados
METRICAS = {
    "Produção (t)": "quantidade_t",
    "Área colhida (ha)": "area_colhida_ha",
    "Rendimento médio (kg/ha)": "rendimento_kg_ha",
    "Valor da produção (mil R$)": "valor_producao_mil_reais",
}

# Precisa ser o PRIMEIRO comando do Streamlit no script
st.set_page_config(
    page_title="Produção Agrícola MT",
    page_icon="🌾",
    layout="wide",
)


# --- Funções auxiliares -----------------------------------------------------

def formatar_numero(valor, casas: int = 0) -> str:
    """Formata no padrão brasileiro: 1234567.8 -> '1.234.568'. Vazio -> '—'."""
    if valor is None or pd.isna(valor):
        return "—"
    texto = f"{valor:,.{casas}f}"  # padrão americano: 1,234,567.8
    # Troca , por . e . por , usando X como marcador temporário
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def variacao_percentual(atual, anterior):
    """Variação % entre dois valores, ou None se não der para calcular."""
    if atual is None or anterior is None:
        return None
    if pd.isna(atual) or pd.isna(anterior) or anterior == 0:
        return None
    return (atual - anterior) / anterior * 100


# --- Acesso aos dados (com cache) -------------------------------------------
# O Streamlit roda o script inteiro a cada interação. O cache evita
# consultar o banco de novo quando os mesmos filtros já foram usados.

@st.cache_data(ttl=3600)
def opcoes_filtros():
    return (
        queries.listar_produtos(),
        queries.listar_anos(),
        queries.listar_municipios(),
    )


@st.cache_data(ttl=3600)
def dados_ranking(produto, ano, limite):
    return queries.ranking_municipios(produto, ano, limite)


@st.cache_data(ttl=3600)
def dados_evolucao(produto, municipio):
    if municipio == TODO_ESTADO:
        return queries.evolucao_estado(produto)
    return queries.evolucao_municipio(produto, municipio)


@st.cache_data(ttl=3600)
def dados_mapa(produto, ano):
    return queries.mapa_municipios(produto, ano)


# cache_resource (e não cache_data): a malha é grande, só de leitura e igual
# para todos. cache_data devolveria uma CÓPIA a cada uso; cache_resource
# devolve sempre o mesmo objeto, sem custo de cópia.
@st.cache_resource
@st.cache_resource
def carregar_malha() -> dict:
    """Lê o GeoJSON dos municípios e ajusta a orientação para o Plotly."""
    malha = json.loads(MALHA_MT_PATH.read_text(encoding="utf-8"))
    return orientar_para_plotly(malha)

# --- Barra lateral: filtros -------------------------------------------------

produtos, anos, municipios = opcoes_filtros()

st.sidebar.header("Filtros")
produto = st.sidebar.selectbox("Cultura", produtos, index=produtos.index("Soja"))
ano = st.sidebar.selectbox("Safra (ano)", anos)  # anos já vêm do mais recente
municipio = st.sidebar.selectbox("Município", [TODO_ESTADO] + municipios)
limite = st.sidebar.slider("Municípios no ranking", min_value=5, max_value=30, value=10)

local = "Mato Grosso" if municipio == TODO_ESTADO else municipio

# --- Cabeçalho --------------------------------------------------------------

st.title("🌾 Produção Agrícola de Mato Grosso")
st.caption("Fonte: IBGE – Produção Agrícola Municipal (PAM), tabela 5457 do SIDRA.")
st.subheader(f"{produto} em {local} – safra {ano}")

# --- Indicadores (KPIs) -----------------------------------------------------

evolucao = dados_evolucao(produto, municipio)
linha_atual = evolucao[evolucao["ano"] == ano]
linha_anterior = evolucao[evolucao["ano"] == ano - 1]

colunas_kpi = st.columns(len(METRICAS))
# zip junta cada coluna da tela com um indicador: (coluna, (rótulo, coluna_df))
for coluna_tela, (rotulo, coluna_df) in zip(colunas_kpi, METRICAS.items()):
    atual = linha_atual[coluna_df].iloc[0] if not linha_atual.empty else None
    anterior = linha_anterior[coluna_df].iloc[0] if not linha_anterior.empty else None
    variacao = variacao_percentual(atual, anterior)

    coluna_tela.metric(
        label=rotulo,
        value=formatar_numero(atual),
        delta=None if variacao is None else f"{variacao:+.1f}% vs {ano - 1}",
    )

# --- Abas -------------------------------------------------------------------

aba_ranking, aba_mapa, aba_evolucao, aba_comparacao, aba_sobre = st.tabs(
    ["🏆 Ranking", "🗺️ Mapa", "📈 Evolução", "🌱 Comparação entre culturas",
     "ℹ️ Sobre os dados"]
)

# Aba 1: ranking dos municípios (sempre do estado inteiro)
with aba_ranking:
    ranking = dados_ranking(produto, ano, limite)

    if ranking.empty:
        st.info("Nenhum município produziu essa cultura nesta safra.")
    else:
        fig = px.bar(
            ranking,
            x="quantidade_t",
            y="municipio",
            orientation="h",
            labels={"quantidade_t": "Produção (t)", "municipio": ""},
            title=f"Maiores produtores de {produto} em MT – {ano}",
            height=max(400, limite * 28),  # mais municípios = gráfico mais alto
        )
        fig.update_yaxes(autorange="reversed")  # 1º colocado no topo
        st.plotly_chart(fig)

        tabela = pd.DataFrame({
            "Posição": ranking["posicao"],
            "Município": ranking["municipio"],
            "Produção (t)": ranking["quantidade_t"].map(formatar_numero),
            "Área colhida (ha)": ranking["area_colhida_ha"].map(formatar_numero),
            "Rendimento (kg/ha)": ranking["rendimento_kg_ha"].map(formatar_numero),
            "Participação no estado (%)": ranking["participacao_pct"].map(
                lambda v: formatar_numero(v, 2)
            ),
        })
        st.dataframe(tabela, hide_index=True)

# Aba: mapa coroplético dos municípios (sempre do estado inteiro)
with aba_mapa:
    # key é obrigatório: a aba Evolução tem outro radio com o mesmo rótulo
    # e as mesmas opções; sem key, o Streamlit acusaria widget duplicado.
    rotulo_mapa = st.radio(
        "Indicador", list(METRICAS), horizontal=True, key="indicador_mapa"
    )
    coluna_mapa = METRICAS[rotulo_mapa]

    malha = carregar_malha()
    dados = dados_mapa(produto, ano)

    # NULL = "sem dado" (NÃO é zero). Separamos em dois grupos para
    # pintar os sem dado de cinza, em vez de sumirem do mapa.
    tem_dado = dados[coluna_mapa].notna()
    com_dado = dados[tem_dado]
    sem_dado = dados[~tem_dado]

    if com_dado.empty:
        st.info("Nenhum município tem esse indicador para essa cultura nesta safra.")
    else:
        # Camada 1: municípios com dado, coloridos pelo indicador
        fig = px.choropleth(
            com_dado,
            geojson=malha,
            locations="cod_municipio",          # coluna com o código no DataFrame
            featureidkey="properties.codarea",  # onde está o código no GeoJSON
            color=coluna_mapa,
            color_continuous_scale="YlGn",      # amarelo (pouco) -> verde (muito)
            hover_name="municipio",
            hover_data={coluna_mapa: ":,.0f", "cod_municipio": False},
            labels={coluna_mapa: rotulo_mapa},
        )

        # Camada 2: municípios sem dado, em cinza e sem legenda de cor
        if not sem_dado.empty:
            fig.add_trace(go.Choropleth(
                geojson=malha,
                locations=sem_dado["cod_municipio"],
                featureidkey="properties.codarea",
                z=[0] * len(sem_dado),          # valor fictício: a cor é fixa
                colorscale=[[0, "lightgray"], [1, "lightgray"]],
                showscale=False,
                text=sem_dado["municipio"],
                hovertemplate="<b>%{text}</b><br>Sem dado nesta safra<extra></extra>",
            ))

        # Enquadra o mapa em MT e esconde o fundo (mundo, oceanos)
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            title=f"{rotulo_mapa} – {produto} em MT – {ano}",
            height=650,
            margin={"l": 0, "r": 0, "t": 50, "b": 0},
            separators=",.",  # decimal com vírgula, milhar com ponto (padrão BR)
        )
        st.plotly_chart(fig)

        st.caption("Municípios em cinza: sem dado para esta cultura nesta safra.")

        # Mesma lógica da validação da Etapa 2 (conjunto B − M), agora no painel
        codigos_malha = {f["properties"]["codarea"] for f in malha["features"]}
        fora_da_malha = com_dado[~com_dado["cod_municipio"].isin(codigos_malha)]
        if not fora_da_malha.empty:
            st.caption(
                "Sem contorno na malha do IBGE usada (os dados aparecem nas "
                "outras abas): " + ", ".join(fora_da_malha["municipio"]) + "."
            )

# Aba 2: evolução ao longo dos anos (estado ou município)
with aba_evolucao:
    rotulo = st.radio("Indicador", list(METRICAS), horizontal=True)
    coluna_df = METRICAS[rotulo]

    fig = px.line(
        evolucao,
        x="ano",
        y=coluna_df,
        markers=True,
        labels={"ano": "Ano", coluna_df: rotulo},
        title=f"{rotulo} – {produto} em {local}",
    )
    # Linha pontilhada marcando a safra escolhida no filtro
    fig.add_vline(x=ano, line_dash="dot", line_color="gray")
    st.plotly_chart(fig)

    if evolucao[coluna_df].isna().any():
        st.caption("Anos sem ponto no gráfico: dado não disponível no IBGE "
                   "(por exemplo, município criado recentemente).")

# Aba 3: comparação entre as culturas (sempre do estado inteiro)
@st.cache_data(ttl=3600)
def dados_comparacao(ano):
    return queries.comparacao_culturas(ano)

with aba_comparacao:
    st.markdown(f"**Todas as culturas em Mato Grosso – safra {ano}**")

    comparacao = dados_comparacao(ano)
    # Valor gerado por hectare (mil R$ -> R$, dividido pela área)
    comparacao = comparacao.assign(
        valor_por_ha=comparacao["valor_producao_mil_reais"] * 1000
        / comparacao["area_plantada_ha"]
    )

    col_esquerda, col_direita = st.columns(2)
    with col_esquerda:
        fig_area = px.bar(
            comparacao,
            x="produto",
            y="area_plantada_ha",
            labels={"produto": "", "area_plantada_ha": "Área plantada (ha)"},
            title="Área plantada",
        )
        st.plotly_chart(fig_area)
    with col_direita:
        fig_valor = px.bar(
            comparacao,
            x="produto",
            y="valor_producao_mil_reais",
            labels={"produto": "", "valor_producao_mil_reais": "Valor (mil R$)"},
            title="Valor da produção",
        )
        st.plotly_chart(fig_valor)

    tabela = pd.DataFrame({
        "Cultura": comparacao["produto"],
        "Área plantada (ha)": comparacao["area_plantada_ha"].map(formatar_numero),
        "Participação na área plantada (%)": comparacao["participacao_area_pct"].map(
            lambda v: formatar_numero(v, 2)
        ),
        "Valor por hectare (R$)": comparacao["valor_por_ha"].map(formatar_numero),
        "Municípios produtores": comparacao["municipios_produtores"],
    })
    st.dataframe(tabela, hide_index=True)

    st.caption("A mesma terra pode ser plantada mais de uma vez no ano "
               "(ex.: milho safrinha depois da soja), então a soma das áreas "
               "pode ser maior que a área agrícola real.")

# Aba 4: notas metodológicas
with aba_sobre:
    st.markdown("""
**Fonte:** IBGE – Produção Agrícola Municipal (PAM), tabela 5457,
obtida pela API do SIDRA.

**Cuidados na leitura dos dados:**

- **Dados de 2025 são preliminares** e podem ser revisados pelo IBGE.
- **Valores em reais correntes**, sem correção pela inflação. Comparações
  de valor entre anos distantes misturam produção, preço e inflação.
- **Área plantada** pode ser contada mais de uma vez quando há cultivos
  sucessivos na mesma terra no mesmo ano.
- **Rendimento do estado** é uma média ponderada: produção total ÷ área
  colhida total (e não a média simples dos municípios).
- **Valores ausentes:** o IBGE usa "-" para zero e "..." para dado não
  disponível. No painel, "—" indica dado não disponível.
- **Boa Esperança do Norte** só tem dados a partir de 2025, por ser um
  município recém-criado.
""")
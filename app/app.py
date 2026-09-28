"""
Painel da Produção Agrícola de Mato Grosso (Streamlit + Plotly).

Lê os dados do PostgreSQL através do módulo src/queries.py e exibe:
indicadores (KPIs), ranking de municípios, evolução por ano e
comparação entre culturas.

Como executar (a partir da raiz do projeto, com o banco no ar):
    python -m streamlit run app/app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src import queries

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
def dados_comparacao(ano):
    return queries.comparacao_culturas(ano)


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

aba_ranking, aba_evolucao, aba_comparacao, aba_sobre = st.tabs(
    ["🏆 Ranking", "📈 Evolução", "🌱 Comparação entre culturas", "ℹ️ Sobre os dados"]
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
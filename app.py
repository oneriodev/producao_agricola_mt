
"""
Aplicação principal - Produção Agrícola MT.

Executar:
    python -m streamlit run app.py
"""

import streamlit as st


st.set_page_config(
    page_title="Produção Agrícola MT",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

pagina_agricola = st.Page(
    "streamlit_app.py",
    title="Análise Agrícola",
    icon=":material/agriculture:",
    default=True,
)

pagina_importacao = st.Page(
    "src/cotacao/page_importar.py",
    title="Importar Cotações",
    icon=":material/upload_file:",
)

navegacao = st.navigation(
    {
        "Análise Agrícola": [
            pagina_agricola,
        ],
        "Cotação de Insumos": [
            pagina_importacao,
        ],
    }
)

navegacao.run()

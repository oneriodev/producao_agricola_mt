
"""
Interface Streamlit para importação de cotações.

Execução:
    streamlit run src/cotacao/page_importar.py
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import streamlit as st

from src.cotacao.importar_cotacoes import (
    ler_arquivo,
    importar_cotacoes,
    COLUNAS,
)


st.set_page_config(
    page_title="Cotação de Insumos",
    page_icon="📊",
    layout="wide",
)

st.title("Cotação de Insumos Agrícolas")
st.subheader("Importação de cotações")

st.write(
    "Importe planilhas de fornecedores nos formatos "
    "CSV ou Excel para armazenar as cotações "
    "no PostgreSQL."
)

arquivo = st.file_uploader(
    "Selecione uma planilha de cotações",
    type=["csv", "xlsx"],
    help="Formatos aceitos: .csv e .xlsx",
)

if arquivo is not None:

    extensao = Path(arquivo.name).suffix.lower()

    if arquivo.size > 10 * 1024 * 1024:
        st.error("O arquivo excede o limite de 10 MB.")
        st.stop()

    caminho_temporario = None

    try:
        # Salva temporariamente o arquivo recebido.
        with NamedTemporaryFile(
            suffix=extensao,
            delete=False,
        ) as temporario:

            temporario.write(arquivo.getvalue())
            caminho_temporario = Path(temporario.name)

        # Faz a leitura usando nosso importador existente.
        df = ler_arquivo(caminho_temporario)

        st.success("Arquivo lido com sucesso!")

        st.markdown("### Pré-visualização")

        st.dataframe(
            df.head(20),
            use_container_width=True,
            hide_index=True,
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Linhas recebidas", len(df))
        col2.metric("Colunas identificadas", len(df.columns))

        faltantes = [
            coluna
            for coluna in COLUNAS
            if coluna not in df.columns
        ]

        col3.metric(
            "Colunas obrigatórias ausentes",
            len(faltantes),
        )

        if faltantes:
            st.error(
                "Colunas ausentes: " + ", ".join(faltantes)
            )

        st.markdown("### Processamento")

        st.info(
            "A importação validará os códigos de insumos "
            "e fornecedores já cadastrados. Registros "
            "com o mesmo código de cotação serão atualizados."
        )

        if st.button(
            "Validar e importar cotações",
            type="primary",
            disabled=bool(faltantes) or df.empty,
        ):

            with st.spinner("Processando cotações..."):

                resultado = importar_cotacoes(
                    caminho_temporario
                )

            st.success("Processamento concluído!")

            st.metric(
                "Linhas válidas processadas",
                resultado["processados"],
            )

            rejeitados = resultado["rejeitados"]

            if rejeitados:
                st.warning(
                    f"{len(rejeitados)} linha(s) rejeitada(s)."
                )

                st.dataframe(
                    rejeitados,
                    use_container_width=True,
                )
            else:
                st.success(
                    "Nenhuma linha rejeitada."
                )

    except Exception as erro:
        st.error(f"Falha no processamento: {erro}")

    finally:
        # Remove o arquivo temporário ao final.
        if caminho_temporario is not None:
            caminho_temporario.unlink(
                missing_ok=True
            )

"""
Etapa 2 do mapa: confere se os códigos de município da malha (GeoJSON)
batem com os códigos da tabela `municipios` no banco.

A ideia é matemática de conjuntos:
    M = códigos da malha       B = códigos do banco
    M ∩ B  -> municípios que vão aparecer coloridos no mapa
    M − B  -> estão no mapa, mas sem dados (ficam em branco)
    B − M  -> têm dados, mas não têm contorno (somem do mapa)

O script só LÊ do banco (SELECT); não altera nada.

Execute a partir da RAIZ do projeto:
    python src/validar_codigos.py
"""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

CAMINHO_MALHA = Path("dados/geo/municipios_mt.geojson")


def codigos_da_malha(caminho: Path = CAMINHO_MALHA) -> set[str]:
    """Lê o GeoJSON salvo na Etapa 1 e devolve o conjunto de códigos IBGE."""
    geojson = json.loads(caminho.read_text(encoding="utf-8"))
    return {str(f["properties"]["codarea"]) for f in geojson["features"]}


def codigos_do_banco() -> dict[str, str]:
    """Consulta a tabela municipios e devolve {codigo: nome}.

    As credenciais vêm do .env (nunca escritas no código).
    """
    load_dotenv()  # carrega as variáveis do arquivo .env para o ambiente

    # Monta a URL de conexão a partir das variáveis de ambiente.
    # "postgresql+psycopg2" indica o driver; troque para "postgresql+psycopg"
    # se o seu projeto usa o psycopg versão 3.
    url = (
        "postgresql+psycopg://"
        f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.environ.get('POSTGRES_HOST', 'localhost')}"
        f":{os.environ.get('POSTGRES_PORT', '5432')}"
        f"/{os.environ['POSTGRES_DB']}"
    )
    engine = create_engine(url)

    # "with" garante que a conexão é fechada mesmo se der erro
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("SELECT cod_municipio, nome FROM municipios")
        )
        return {codigo: nome for codigo, nome in resultado}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    malha = codigos_da_malha()
    banco = codigos_do_banco()
    codigos_banco = set(banco)  # set() de um dicionário pega só as chaves

    em_ambos = malha & codigos_banco          # interseção
    so_na_malha = malha - codigos_banco       # diferença M − B
    so_no_banco = codigos_banco - malha       # diferença B − M

    logger.info("Municípios na malha: %d", len(malha))
    logger.info("Municípios no banco: %d", len(codigos_banco))
    logger.info("Em ambos (aparecem no mapa): %d", len(em_ambos))

    if so_na_malha:
        logger.warning("Só na malha (sem dados no banco): %s", sorted(so_na_malha))
    if so_no_banco:
        # Aqui temos o nome, porque ele vem do banco
        nomes = [f"{c} - {banco[c]}" for c in sorted(so_no_banco)]
        logger.warning("Só no banco (sem contorno no mapa): %s", nomes)

    if not so_na_malha and not so_no_banco:
        logger.info("Correspondência perfeita entre malha e banco.")


if __name__ == "__main__":
    main()
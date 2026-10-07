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
from pathlib import Path
from sqlalchemy import create_engine, text

from src.config import DATABASE_URL, MALHA_MT_PATH

logger = logging.getLogger(__name__)

CAMINHO_MALHA = MALHA_MT_PATH


def codigos_da_malha(caminho: Path = CAMINHO_MALHA) -> set[str]:
    """Lê o GeoJSON salvo na Etapa 1 e devolve o conjunto de códigos IBGE."""
    geojson = json.loads(caminho.read_text(encoding="utf-8"))
    return {str(f["properties"]["codarea"]) for f in geojson["features"]}


def codigos_do_banco() -> dict[str, str]:
    """Consulta a tabela municipios e devolve {codigo: nome}."""
    engine = create_engine(DATABASE_URL)  # conexão vem do config.py
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("SELECT cod_municipio, nome FROM municipios")
        )
        return {codigo: nome for codigo, nome in resultado}

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
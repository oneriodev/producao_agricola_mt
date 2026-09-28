"""
Modelos das tabelas do banco de dados (SQLAlchemy ORM).

Cada classe representa uma tabela; cada atributo, uma coluna.
Modelo estrela simplificado:
    municipios (cadastro) --< producao (números) >-- produtos (cadastro)
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Classe base: o SQLAlchemy registra aqui todas as tabelas."""


class Municipio(Base):
    """Cadastro dos municípios de Mato Grosso."""

    __tablename__ = "municipios"

    cod_municipio: Mapped[str] = mapped_column(String(7), primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)


class Produto(Base):
    """Cadastro das culturas agrícolas."""

    __tablename__ = "produtos"

    cod_produto: Mapped[str] = mapped_column(String(10), primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


class Producao(Base):
    """Números da produção: um registro por município + produto + ano."""

    __tablename__ = "producao"

    # Chave primária composta: a combinação dos três é única
    cod_municipio: Mapped[str] = mapped_column(
        ForeignKey("municipios.cod_municipio"), primary_key=True
    )
    cod_produto: Mapped[str] = mapped_column(
        ForeignKey("produtos.cod_produto"), primary_key=True
    )
    ano: Mapped[int] = mapped_column(primary_key=True)

    # Variáveis (podem ser NULL quando o IBGE não tem o dado)
    area_plantada_ha: Mapped[float | None]
    area_colhida_ha: Mapped[float | None]
    quantidade_t: Mapped[float | None]
    rendimento_kg_ha: Mapped[float | None]
    valor_producao_mil_reais: Mapped[float | None]
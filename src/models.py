"""
Modelos das tabelas do banco de dados (SQLAlchemy ORM).

Cada classe representa uma tabela; cada atributo, uma coluna.
Modelo estrela simplificado:
    municipios (cadastro) --< producao (números) >-- produtos (cadastro)
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    func,
    text,
)

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    func,
    text,
)

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    func,
    text,
)


from sqlalchemy.dialects.postgresql import JSONB
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

    # =============================================================================
# Tabelas de Machine Learning (aba "Previsões")
# Os resultados são gerados por scripts em src/ml/ e só LIDOS pelo painel.
# =============================================================================


class ExecucaoModelo(Base):
    """Uma execução de modelo: registra quando rodou e com quais parâmetros.

    Permite comparar versões ("a execução 3 errou menos que a 2?").
    """

    __tablename__ = "execucoes_modelo"
    __table_args__ = (
        # O banco só aceita estes dois tipos (protege contra erros de digitação)
        CheckConstraint("tipo IN ('clusterizacao', 'previsao')", name="ck_execucao_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)  # gerado automaticamente
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    # server_default: o PRÓPRIO banco preenche a data/hora no momento da inserção
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # JSONB: guarda um dicionário (ex.: {"k": 4, "anos": [2021, 2025]})
    # server_default: o BANCO preenche '{}' quando ninguém informar o valor,
    # inclusive em inserções feitas fora do Python (ex.: pelo psql)
    parametros: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

class PerfilCluster(Base):
    """Nome e descrição de cada grupo da clusterização, definidos por você."""

    __tablename__ = "perfis_cluster"

    # ondelete="CASCADE": apagar a execução apaga também os perfis dela
    execucao_id: Mapped[int] = mapped_column(
        ForeignKey("execucoes_modelo.id", ondelete="CASCADE"), primary_key=True
    )
    cluster_id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(60))
    descricao: Mapped[str | None] = mapped_column(Text)


class ClusterMunicipio(Base):
    """A qual perfil cada município pertence, em cada execução."""

    __tablename__ = "clusters_municipios"
    __table_args__ = (
        # Chave estrangeira COMPOSTA: o par (execução, cluster) precisa existir
        # em perfis_cluster. Impede apontar para um cluster inexistente.
        ForeignKeyConstraint(
            ["execucao_id", "cluster_id"],
            ["perfis_cluster.execucao_id", "perfis_cluster.cluster_id"],
            ondelete="CASCADE",
        ),
    )

    execucao_id: Mapped[int] = mapped_column(primary_key=True)
    cod_municipio: Mapped[str] = mapped_column(
        ForeignKey("municipios.cod_municipio"), primary_key=True
    )
    cluster_id: Mapped[int] = mapped_column(nullable=False)
    # Valores das features usadas (participação de cada cultura etc.).
    # JSONB porque as features podem mudar entre experimentos.
    features: Mapped[dict] = mapped_column(JSONB, nullable=False)


class PrevisaoProdutividade(Base):
    """Produtividade prevista (kg/ha) por município, cultura, ano e MODELO.

    Formato "longo": uma linha por modelo, para comparar vários modelos
    sem precisar mudar a tabela quando um modelo entra ou sai.
    O valor real não é gravado aqui: ele já está na tabela producao.

    tipo = 'backtest': previsão de um ano passado (comparável ao real)
    tipo = 'futuro':   previsão do próximo ano (ainda sem valor real)
    """

    __tablename__ = "previsoes_produtividade"
    __table_args__ = (
        CheckConstraint("tipo IN ('backtest', 'futuro')", name="ck_previsao_tipo"),
    )

    execucao_id: Mapped[int] = mapped_column(
        ForeignKey("execucoes_modelo.id", ondelete="CASCADE"), primary_key=True
    )
    cod_municipio: Mapped[str] = mapped_column(
        ForeignKey("municipios.cod_municipio"), primary_key=True
    )
    cod_produto: Mapped[str] = mapped_column(
        ForeignKey("produtos.cod_produto"), primary_key=True
    )
    ano_alvo: Mapped[int] = mapped_column(primary_key=True)
    modelo: Mapped[str] = mapped_column(String(30), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    previsto_kg_ha: Mapped[float] = mapped_column(nullable=False)

class MetricaModelo(Base):
    """Erro de cada modelo na validação, para comparar com o baseline."""

    __tablename__ = "metricas_modelo"

    execucao_id: Mapped[int] = mapped_column(
        ForeignKey("execucoes_modelo.id", ondelete="CASCADE"), primary_key=True
    )
    cod_produto: Mapped[str] = mapped_column(
        ForeignKey("produtos.cod_produto"), primary_key=True
    )
    modelo: Mapped[str] = mapped_column(String(30), primary_key=True)  # ex.: 'random_forest'
    mae_kg_ha: Mapped[float] = mapped_column(nullable=False)   # erro médio absoluto
    mape_pct: Mapped[float | None]                              # erro percentual médio
    n_previsoes: Mapped[int] = mapped_column(nullable=False)

-- Módulo de Cotação de Insumos
-- Criação do schema e da tabela de câmbio

CREATE SCHEMA IF NOT EXISTS cotacao;

CREATE TABLE IF NOT EXISTS cotacao.cambio (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    data_referencia DATE NOT NULL,

    data_hora_cotacao TIMESTAMP NOT NULL,

    moeda VARCHAR(3) NOT NULL DEFAULT 'USD',

    compra NUMERIC(18,6) NOT NULL,

    venda NUMERIC(18,6) NOT NULL,

    fonte VARCHAR(30) NOT NULL DEFAULT 'BCB_PTAX',

    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_cambio_cotacao
        UNIQUE (
            data_hora_cotacao,
            moeda,
            fonte
        ),

    CONSTRAINT ck_cambio_valores
        CHECK (compra > 0 AND venda > 0)
);

CREATE INDEX IF NOT EXISTS idx_cambio_data
ON cotacao.cambio (data_referencia DESC);

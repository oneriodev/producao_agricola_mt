
-- ===========================================
-- MÓDULO: COTAÇÃO DE INSUMOS AGRÍCOLAS
-- Tabelas de cadastro e cotações
-- ===========================================

CREATE SCHEMA IF NOT EXISTS cotacao;

-- 1. Cadastro de insumos
CREATE TABLE IF NOT EXISTS cotacao.itens (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_item VARCHAR(30) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    categoria VARCHAR(20) NOT NULL,
    especificacao TEXT,
    unidade_padrao VARCHAR(20) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_item_categoria CHECK (
        categoria IN (
            'fertilizante',
            'semente',
            'defensivo',
            'material'
        )
    )
);

-- 2. Cadastro de fornecedores
CREATE TABLE IF NOT EXISTS cotacao.fornecedores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod_fornecedor VARCHAR(30) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    municipio VARCHAR(100),
    uf CHAR(2),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Conversão de unidades
CREATE TABLE IF NOT EXISTS cotacao.unidades_conversao (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES cotacao.itens(id),
    unidade_origem VARCHAR(20) NOT NULL,
    unidade_destino VARCHAR(20) NOT NULL,
    fator NUMERIC(20,8) NOT NULL,

    CONSTRAINT ck_fator_positivo CHECK (fator > 0),

    CONSTRAINT uq_conversao UNIQUE (
        item_id,
        unidade_origem,
        unidade_destino
    )
);

-- 4. Registro das cotações comerciais
CREATE TABLE IF NOT EXISTS cotacao.cotacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    item_id BIGINT NOT NULL
        REFERENCES cotacao.itens(id),

    fornecedor_id BIGINT NOT NULL
        REFERENCES cotacao.fornecedores(id),

    data_cotacao DATE NOT NULL,
    validade DATE,

    preco_original NUMERIC(18,6) NOT NULL,
    moeda_original CHAR(3) NOT NULL,
    unidade VARCHAR(20) NOT NULL,

    observacoes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_preco_positivo CHECK (
        preco_original > 0
    ),

    CONSTRAINT ck_moeda CHECK (
        moeda_original IN ('BRL', 'USD')
    ),

    CONSTRAINT ck_validade CHECK (
        validade IS NULL
        OR validade >= data_cotacao
    )
);

CREATE INDEX IF NOT EXISTS idx_cotacoes_item_data
ON cotacao.cotacoes (item_id, data_cotacao DESC);

CREATE INDEX IF NOT EXISTS idx_cotacoes_fornecedor
ON cotacao.cotacoes (fornecedor_id);

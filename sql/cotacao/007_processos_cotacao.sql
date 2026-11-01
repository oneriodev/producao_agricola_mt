
-- ============================================
-- ETAPA 11: GESTÃO DE PROCESSOS DE COTAÇÃO
-- ============================================

-- 1. Cabeçalho do processo de cotação

CREATE TABLE IF NOT EXISTS cotacao.processos_cotacao (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    codigo VARCHAR(40) NOT NULL UNIQUE,
    titulo VARCHAR(150) NOT NULL,

    propriedade VARCHAR(150),
    safra VARCHAR(20),
    finalidade TEXT,

    data_criacao DATE NOT NULL DEFAULT CURRENT_DATE,

    status VARCHAR(20) NOT NULL DEFAULT 'rascunho',

    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_processo_status CHECK (
        status IN (
            'rascunho',
            'em_cotacao',
            'em_analise',
            'finalizado',
            'cancelado'
        )
    )
);


-- 2. Insumos solicitados no processo

CREATE TABLE IF NOT EXISTS cotacao.processo_itens (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    processo_id BIGINT NOT NULL
        REFERENCES cotacao.processos_cotacao(id)
        ON DELETE CASCADE,

    item_id BIGINT NOT NULL
        REFERENCES cotacao.itens(id),

    quantidade NUMERIC(18,4) NOT NULL,
    unidade VARCHAR(20) NOT NULL,

    observacoes TEXT,

    CONSTRAINT ck_quantidade_positiva CHECK (
        quantidade > 0
    ),

    CONSTRAINT uq_processo_item UNIQUE (
        processo_id,
        item_id
    ),

    CONSTRAINT uq_processo_item_id UNIQUE (
        id,
        item_id
    )
);


-- 3. Ofertas associadas aos itens solicitados

CREATE TABLE IF NOT EXISTS cotacao.processo_ofertas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    processo_item_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,

    cotacao_id BIGINT NOT NULL UNIQUE
        REFERENCES cotacao.cotacoes(id),

    criada_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_oferta_processo_item
        FOREIGN KEY (processo_item_id, item_id)
        REFERENCES cotacao.processo_itens(id, item_id),

    CONSTRAINT uq_processo_oferta UNIQUE (
        processo_item_id,
        cotacao_id
    )
);


-- Índices para consultas e relatórios

CREATE INDEX IF NOT EXISTS idx_processo_status
ON cotacao.processos_cotacao (status);

CREATE INDEX IF NOT EXISTS idx_processo_itens_processo
ON cotacao.processo_itens (processo_id);

CREATE INDEX IF NOT EXISTS idx_processo_ofertas_item
ON cotacao.processo_ofertas (processo_item_id);

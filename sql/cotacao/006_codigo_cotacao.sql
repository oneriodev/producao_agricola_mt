
-- Adiciona identificador comercial às cotações.
-- Os registros antigos permanecem preservados.

ALTER TABLE cotacao.cotacoes
ADD COLUMN IF NOT EXISTS cod_cotacao VARCHAR(80);

-- Garante unicidade dos códigos informados.
-- PostgreSQL permite múltiplos NULL nesta restrição,
-- preservando cotações de testes anteriores.

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_cotacoes_cod_cotacao
ON cotacao.cotacoes (cod_cotacao);

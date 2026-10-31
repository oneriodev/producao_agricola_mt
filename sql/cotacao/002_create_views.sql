-- Seleciona o último boletim PTAX de cada dia.

CREATE OR REPLACE VIEW cotacao.vw_cambio_diario AS

SELECT DISTINCT ON (data_referencia)
    data_referencia,
    data_hora_cotacao,
    moeda,
    compra,
    venda,
    fonte

FROM cotacao.cambio

WHERE moeda = 'USD'
  AND fonte = 'BCB_PTAX'

ORDER BY
    data_referencia,
    data_hora_cotacao DESC;

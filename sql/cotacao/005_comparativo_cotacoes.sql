
-- Comparativo de cotações de insumos agrícolas
-- Conversão USD/BRL pela PTAX histórica.

SELECT
    i.nome AS insumo,
    f.nome AS fornecedor,
    c.data_cotacao,
    c.preco_original,
    c.moeda_original,
    c.unidade,

    cambio.data_referencia AS data_ptax,
    cambio.venda AS ptax_venda,

    ROUND(
        CASE
            WHEN c.moeda_original = 'USD'
                THEN c.preco_original * cambio.venda
            ELSE c.preco_original
        END,
        2
    ) AS preco_brl

FROM cotacao.cotacoes c

INNER JOIN cotacao.itens i
    ON i.id = c.item_id

INNER JOIN cotacao.fornecedores f
    ON f.id = c.fornecedor_id

LEFT JOIN LATERAL (
    SELECT
        data_referencia,
        venda
    FROM cotacao.vw_cambio_diario
    WHERE data_referencia <= c.data_cotacao
    ORDER BY data_referencia DESC
    LIMIT 1
) cambio ON TRUE

WHERE c.observacoes = 'DEMONSTRACAO_ETAPA_8'
  AND (
      c.moeda_original = 'BRL'
      OR cambio.venda IS NOT NULL
  )

ORDER BY
    i.nome,
    preco_brl ASC;

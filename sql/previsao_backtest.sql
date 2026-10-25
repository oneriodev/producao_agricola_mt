-- Previsões de validação (anos passados) de todos os modelos, com o valor REAL.
-- O real vem da tabela producao: não precisa ser gravado de novo.
WITH ultima AS (
    SELECT MAX(id) AS id
    FROM execucoes_modelo
    WHERE tipo = 'previsao'
)
SELECT
    pp.cod_municipio,
    m.nome               AS municipio,
    pp.ano_alvo          AS ano,
    pp.modelo,
    pp.previsto_kg_ha,
    pr.rendimento_kg_ha  AS real_kg_ha
FROM previsoes_produtividade AS pp
JOIN ultima     AS u  ON u.id = pp.execucao_id
JOIN municipios AS m  ON m.cod_municipio = pp.cod_municipio
JOIN producao   AS pr ON pr.cod_municipio = pp.cod_municipio
                     AND pr.cod_produto   = pp.cod_produto
                     AND pr.ano           = pp.ano_alvo
WHERE pp.tipo = 'backtest'
ORDER BY m.nome, pp.ano_alvo, pp.modelo;

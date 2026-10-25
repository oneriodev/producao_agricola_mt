-- Previsão do próximo ano feita pelo modelo PUBLICADO, com o último valor real.
WITH ultima AS (
    SELECT id, parametros ->> 'modelo_escolhido' AS escolhido
    FROM execucoes_modelo
    WHERE tipo = 'previsao'
    ORDER BY id DESC
    LIMIT 1
)
SELECT
    pp.cod_municipio,
    m.nome               AS municipio,
    pp.ano_alvo          AS ano,
    pp.previsto_kg_ha,
    pr.rendimento_kg_ha  AS ultimo_real_kg_ha
FROM previsoes_produtividade AS pp
JOIN ultima     AS u ON u.id = pp.execucao_id
                    AND pp.modelo = u.escolhido
JOIN municipios AS m ON m.cod_municipio = pp.cod_municipio
LEFT JOIN producao AS pr ON pr.cod_municipio = pp.cod_municipio
                        AND pr.cod_produto   = pp.cod_produto
                        AND pr.ano           = pp.ano_alvo - 1
WHERE pp.tipo = 'futuro'
ORDER BY pp.previsto_kg_ha DESC;

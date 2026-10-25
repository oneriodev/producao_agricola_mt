-- Erro de cada modelo na última execução de previsão, e qual foi o publicado.
WITH ultima AS (
    SELECT id, parametros, criado_em
    FROM execucoes_modelo
    WHERE tipo = 'previsao'
    ORDER BY id DESC
    LIMIT 1
)
SELECT
    m.modelo,
    m.mae_kg_ha,
    m.mape_pct,
    m.n_previsoes,
    u.parametros ->> 'modelo_escolhido' AS modelo_escolhido,
    u.criado_em
FROM metricas_modelo AS m
JOIN ultima AS u ON u.id = m.execucao_id
ORDER BY m.mae_kg_ha;

-- Evolução anual de uma cultura no estado inteiro (soma dos municípios).
-- Parâmetro: :produto
SELECT
    p.ano,
    SUM(p.area_plantada_ha)          AS area_plantada_ha,
    SUM(p.area_colhida_ha)           AS area_colhida_ha,
    SUM(p.quantidade_t)              AS quantidade_t,
    SUM(p.valor_producao_mil_reais)  AS valor_producao_mil_reais,
    -- média PONDERADA: produção total (em kg) / área total colhida.
    -- NULLIF evita divisão por zero (vira NULL se a área for 0).
    SUM(p.quantidade_t) * 1000 / NULLIF(SUM(p.area_colhida_ha), 0)
                                     AS rendimento_kg_ha
FROM producao p
JOIN produtos pr ON pr.cod_produto = p.cod_produto
WHERE pr.nome = :produto
GROUP BY p.ano
ORDER BY p.ano;
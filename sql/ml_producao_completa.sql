-- Produção completa (todos os anos, municípios e culturas) para os modelos de ML.
SELECT
    p.cod_municipio,
    m.nome  AS municipio,
    pr.nome AS produto,
    p.ano,
    p.area_plantada_ha,
    p.area_colhida_ha,
    p.quantidade_t,
    p.rendimento_kg_ha
FROM producao   AS p
JOIN municipios AS m  ON m.cod_municipio = p.cod_municipio
JOIN produtos   AS pr ON pr.cod_produto  = p.cod_produto;

-- Evolução anual de uma cultura em um município específico.
-- Parâmetros: :produto, :municipio
SELECT
    p.ano,
    p.area_plantada_ha,
    p.area_colhida_ha,
    p.quantidade_t,
    p.rendimento_kg_ha,
    p.valor_producao_mil_reais
FROM producao p
JOIN municipios m ON m.cod_municipio = p.cod_municipio
JOIN produtos  pr ON pr.cod_produto  = p.cod_produto
WHERE pr.nome = :produto
  AND m.nome = :municipio
ORDER BY p.ano;
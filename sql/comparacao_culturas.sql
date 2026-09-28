-- Comparação entre as culturas em um ano, no estado inteiro.
-- Parâmetro: :ano
--
-- Comparamos por ÁREA e VALOR, não por toneladas: cana-de-açúcar pesa
-- muito mais que feijão por hectare, então toneladas distorcem a comparação.
SELECT
    pr.nome                                  AS produto,
    SUM(p.area_plantada_ha)                  AS area_plantada_ha,
    SUM(p.quantidade_t)                      AS quantidade_t,
    SUM(p.valor_producao_mil_reais)          AS valor_producao_mil_reais,
    -- participação na área total plantada (janela sobre o resultado agrupado)
    100.0 * SUM(p.area_plantada_ha)
          / SUM(SUM(p.area_plantada_ha)) OVER ()
                                             AS participacao_area_pct,
    -- quantos municípios produziram a cultura naquele ano
    COUNT(*) FILTER (WHERE p.quantidade_t > 0)
                                             AS municipios_produtores
FROM producao p
JOIN produtos pr ON pr.cod_produto = p.cod_produto
WHERE p.ano = :ano
GROUP BY pr.nome
ORDER BY area_plantada_ha DESC;
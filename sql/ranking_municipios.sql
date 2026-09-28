-- Ranking dos municípios que mais produziram uma cultura em um ano.
-- Parâmetros: :produto (nome da cultura), :ano, :limite (quantos mostrar)
SELECT
    RANK() OVER (ORDER BY p.quantidade_t DESC)             AS posicao,
    m.nome                                                 AS municipio,
    p.quantidade_t,
    p.area_colhida_ha,
    p.rendimento_kg_ha,
    p.valor_producao_mil_reais,
    -- participação no total do estado (função de janela)
    100.0 * p.quantidade_t / SUM(p.quantidade_t) OVER ()   AS participacao_pct
FROM producao p
JOIN municipios m ON m.cod_municipio = p.cod_municipio
JOIN produtos  pr ON pr.cod_produto  = p.cod_produto
WHERE pr.nome = :produto
  AND p.ano = :ano
  AND p.quantidade_t > 0          -- ignora quem não produziu
ORDER BY p.quantidade_t DESC
LIMIT :limite;
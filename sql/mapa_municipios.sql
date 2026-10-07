-- Valores de uma cultura em uma safra para TODOS os municípios de MT.
-- Usado pela aba "Mapa" do painel.
--
-- Parâmetros: :produto (nome da cultura), :ano
--
-- Por que LEFT JOIN partindo de municipios?
--   Queremos uma linha para cada município, mesmo os que não têm registro
--   de produção naquela cultura/ano (eles vêm com NULL e ficam cinza no mapa).
--
-- Por que os filtros de ano e produto estão no ON e não no WHERE?
--   Num LEFT JOIN, um filtro no WHERE sobre a tabela da direita (producao)
--   descarta as linhas com NULL, transformando o LEFT JOIN num INNER JOIN
--   sem avisar. No ON, o filtro só decide QUAL linha de producao combina.

SELECT
    m.cod_municipio,
    m.nome                      AS municipio,
    p.quantidade_t,
    p.area_colhida_ha,
    p.rendimento_kg_ha,
    p.valor_producao_mil_reais
FROM municipios AS m
LEFT JOIN produtos AS pr
       ON pr.nome = :produto
LEFT JOIN producao AS p
       ON p.cod_municipio = m.cod_municipio
      AND p.cod_produto   = pr.cod_produto
      AND p.ano           = :ano
ORDER BY m.nome;
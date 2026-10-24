-- Perfil de cada município na clusterização mais recente.
-- O operador ->> extrai um campo do JSONB como texto; ::float converte para número.
WITH ultima AS (
    SELECT MAX(id) AS id
    FROM execucoes_modelo
    WHERE tipo = 'clusterizacao'
)
SELECT
    c.cod_municipio,
    m.nome                                   AS municipio,
    p.nome                                   AS perfil,
    (c.features ->> 'area_media_ha')::float  AS area_media_ha
FROM clusters_municipios AS c
JOIN ultima         AS u ON u.id = c.execucao_id
JOIN perfis_cluster AS p ON p.execucao_id = c.execucao_id
                        AND p.cluster_id  = c.cluster_id
JOIN municipios     AS m ON m.cod_municipio = c.cod_municipio
ORDER BY m.nome;

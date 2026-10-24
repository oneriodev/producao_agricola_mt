-- Perfis da clusterização mais recente, com quantos municípios cada um tem.
WITH ultima AS (
    SELECT id, criado_em
    FROM execucoes_modelo
    WHERE tipo = 'clusterizacao'
    ORDER BY id DESC
    LIMIT 1
)
SELECT
    p.cluster_id,
    p.nome                 AS perfil,
    p.descricao,
    COUNT(c.cod_municipio) AS municipios,
    u.criado_em
FROM perfis_cluster AS p
JOIN ultima AS u ON u.id = p.execucao_id
LEFT JOIN clusters_municipios AS c
       ON c.execucao_id = p.execucao_id
      AND c.cluster_id  = p.cluster_id
GROUP BY p.cluster_id, p.nome, p.descricao, u.criado_em
ORDER BY municipios DESC;


-- Consultar os insumos cadastrados
SELECT
    id,
    cod_item,
    nome,
    categoria,
    unidade_padrao
FROM cotacao.itens
ORDER BY nome;

-- Consultar os fornecedores cadastrados
SELECT
    id,
    cod_fornecedor,
    nome,
    municipio,
    uf
FROM cotacao.fornecedores
ORDER BY nome;

# 🌾 Produção Agrícola de Mato Grosso

Pipeline de dados completo (ETL) com a produção agrícola dos 142 municípios de
Mato Grosso, a partir dos dados oficiais do IBGE. Os dados são extraídos da API
SIDRA, tratados com pandas, armazenados em PostgreSQL (Docker) e apresentados
em um painel interativo com Streamlit.

## 📊 Destaques dos dados

- A produção de **soja em MT cresceu 2,7 vezes** entre 2010 e 2025, de 18,8
  para 50,2 milhões de toneladas, com a área dobrando e o rendimento subindo
  de ~3.000 para ~3.900 kg/ha.
- **Sorriso** é o maior produtor de soja do estado (2,34 milhões de t em 2025),
  mas responde por apenas **4,7%** do total: a produção é distribuída entre
  muitos municípios de grande porte.
- Em **2024**, a produção de soja caiu 14% mesmo com aumento de área, com
  forte queda no rendimento médio.
- O **algodão** gera cerca de **R$ 19,5 mil por hectare**, quase três vezes a
  soja, e é produzido em menos da metade dos municípios.
- Em peso, o **milho** supera a soja (54,3 × 50,2 milhões de t em 2025), mas
  vale menos da metade: boa parte é a "safrinha", plantada na mesma terra
  após a colheita da soja.

## 🏗️ Arquitetura

```mermaid
flowchart LR
    A[API SIDRA / IBGE] -->|requests| B[extract.py<br/>data/raw]
    B -->|pandas| C[transform.py<br/>data/processed]
    C -->|SQLAlchemy| D[(PostgreSQL<br/>Docker)]
    D -->|SQL| E[queries.py]
    E --> F[Painel<br/>Streamlit + Plotly]
```

| Etapa | Módulo | O que faz |
|---|---|---|
| Extração | `src/extract.py` | Consulta a API SIDRA (tabela 5457) por cultura e salva o dado bruto |
| Transformação | `src/transform.py` | Converte tipos, trata valores ausentes, pivota para formato largo e valida |
| Carga | `src/load.py` | Grava em 3 tabelas relacionais, com carga completa em transação |
| Análise | `src/queries.py` + `sql/` | Consultas SQL parametrizadas usadas pelo painel |
| Visualização | `app/app.py` | Painel com KPIs, ranking, evolução e comparação entre culturas |

## 🛠️ Stack

- **Python 3.12** · requests · pandas
- **PostgreSQL 16** em Docker (docker compose)
- **SQLAlchemy 2.0** (ORM para modelagem, Core para consultas) · psycopg 3
- **Streamlit** + **Plotly** para o painel
- **Git/GitHub** para versionamento

## 📁 Estrutura do projeto

```
producao_agricola_mt/
├── app/
│   └── app.py              # painel Streamlit
├── data/
│   ├── raw/                # dados brutos da API (não versionados)
│   └── processed/          # dados tratados (não versionados)
├── sql/                    # consultas de análise (.sql)
├── src/
│   ├── config.py           # configurações centrais (códigos IBGE, caminhos, banco)
│   ├── extract.py          # extração
│   ├── transform.py        # transformação e validação
│   ├── models.py           # modelos das tabelas (SQLAlchemy)
│   ├── load.py             # carga no banco
│   ├── queries.py          # execução das consultas
│   └── pipeline.py         # executa extração + transformação + carga
├── docker-compose.yml      # PostgreSQL
├── .env.example            # modelo das variáveis de ambiente
└── requirements.txt
```

## 🗄️ Modelo de dados

Modelo estrela simplificado: uma tabela de fatos com os números da produção e
duas tabelas de cadastro.

```mermaid
erDiagram
    municipios ||--o{ producao : possui
    produtos   ||--o{ producao : possui
    municipios {
        string cod_municipio PK
        string nome
    }
    produtos {
        string cod_produto PK
        string nome
    }
    producao {
        string cod_municipio PK, FK
        string cod_produto PK, FK
        int ano PK
        float area_plantada_ha
        float area_colhida_ha
        float quantidade_t
        float rendimento_kg_ha
        float valor_producao_mil_reais
    }
```

A chave primária composta (município + cultura + ano) impede registros
duplicados diretamente no banco.

## 🚀 Como executar

**Pré-requisitos:** Python 3.12+, Docker com Docker Compose e Git.

**1. Clonar o repositório**
```bash
git clone https://github.com/oneriodev/producao_agricola_mt.git
cd producao_agricola_mt
```

**2. Criar o ambiente virtual e instalar as dependências**
```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

**3. Configurar as variáveis de ambiente**
```bash
cp .env.example .env             # Linux/Mac
# copy .env.example .env         # Windows
```
Edite o `.env` e defina uma senha para o banco.

**4. Subir o PostgreSQL**
```bash
docker compose up -d
```

**5. Rodar o pipeline** (extração, transformação e carga)
```bash
python -m src.pipeline
```

**6. Abrir o painel**
```bash
python -m streamlit run app/app.py
```
O painel abre em `http://localhost:8501`.

## 🧠 Decisões técnicas

- **Dado bruto preservado:** a extração salva a resposta da API sem alterações.
  Se a transformação mudar, basta reprocessar, sem consultar a API de novo.
- **Tratamento de valores ausentes seguindo o padrão do IBGE:** `-` significa
  zero e vira `0`; `...` significa dado não disponível e vira `NULL`.
  Transformar tudo em zero distorceria médias e séries históricas.
- **Validação na transformação:** o pipeline confere o número de linhas,
  duplicatas e valores negativos, e interrompe a execução se algo falhar.
- **Carga idempotente:** as tabelas são esvaziadas e recarregadas dentro de
  uma transação. Rodar o pipeline várias vezes sempre produz o mesmo
  resultado, e uma falha no meio não deixa o banco vazio.
- **SQL parametrizado:** os filtros do painel são passados como parâmetros,
  nunca concatenados no texto do SQL, o que evita SQL injection.
- **Rendimento como média ponderada:** o rendimento do estado é calculado
  como produção total ÷ área colhida total, e não como média simples dos
  municípios, que daria o mesmo peso a municípios pequenos e grandes.
- **Configuração centralizada:** códigos do IBGE, caminhos e credenciais
  ficam em `config.py` e `.env`. Incluir uma nova cultura exige mudar uma
  única linha.

## ⚠️ Limitações e cuidados na leitura

- Os dados de **2025 são preliminares** e podem ser revisados pelo IBGE.
- O **valor da produção está em reais correntes**, sem correção pela inflação.
- A **área plantada** pode ser contada mais de uma vez quando há cultivos
  sucessivos na mesma terra (ex.: milho safrinha após a soja).
- **Boa Esperança do Norte** é um município recém-criado e só possui dados
  a partir de 2025. Municípios vizinhos podem apresentar redução de área
  nesse ano por mudança de território, e não por queda de produção.

## 📚 Fonte dos dados

IBGE – Produção Agrícola Municipal (PAM), tabela 5457:
[sidra.ibge.gov.br/tabela/5457](https://sidra.ibge.gov.br/tabela/5457)

## 👤 Autor

**Onerio** – estudante de Engenharia de Software, com foco em Python, dados e back-end.
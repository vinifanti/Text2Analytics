# Text2Analytics

Consulte dados de vendas em linguagem natural. Faça uma pergunta em português e receba a resposta com base em queries SQL geradas e executadas automaticamente.

Disponível em dois modos: **aplicação web** (interface de chat no browser) e **CLI** (REPL no terminal).

## Como funciona

```
Pergunta do usuário
        │
        ▼
┌───────────────────┐
│  ContextRetriever │  ← busca tabelas relevantes via embeddings semânticos
│                   │    + exemplos de SQL similares (few-shot)
└────────┬──────────┘
         │ schema + exemplos
         ▼
┌───────────────────┐
│      Agent        │  ← ReAct (LangChain + Claude) decide quais ferramentas usar
│  (agent.py)       │
└────────┬──────────┘
         │ SQL gerado
         ▼
┌───────────────────┐
│   SqlExecutor     │  ← executa no SQLite (modo somente leitura)
│ + auto-correção   │    até 2 tentativas de correção via LLM se houver erro
└────────┬──────────┘
         │ resultado
         ▼
┌───────────────────┐
│     Memory        │  ← mantém histórico comprimido da conversa
└────────┬──────────┘
         │
         ▼
  Resposta em português
```

**Módulos principais:**

| Módulo | Responsabilidade |
|---|---|
| `app.py` | Entry point CLI + função `build_app_components()` compartilhada com o servidor |
| `server.py` | Servidor FastAPI: API REST de chat + serve o frontend estático |
| `agent.py` | Constrói o AgentExecutor ReAct (LangChain) |
| `context_retriever.py` | Embeddings semânticos para schema-linking e few-shot retrieval |
| `sql_executor.py` | Execução segura de SQL + loop de auto-correção |
| `tools.py` | Factory de ferramentas LangChain (`get_schema`, `query_database`, `clarify_question`) |
| `memory.py` | Histórico de conversa com compressão automática via LLM |
| `metadata.py` | Carrega descrições ricas de tabelas/colunas do YAML |
| `seed.py` | Cria e popula o banco SQLite de exemplo na primeira execução |

## Pré-requisitos

- Python 3.11+
- Chave de API da Anthropic (modelo padrão: `claude-haiku-4-5-20251001`)

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd Text2Analytics

# 2. Crie e ative um ambiente virtual dentro de src/
python -m venv src/.venv
source src/.venv/bin/activate  # Linux/macOS
# src\.venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install -r src/requirements.txt

# 4. Configure as variáveis de ambiente (veja seção abaixo)
```

## Configuração

Copie o arquivo de exemplo e preencha com sua chave:

```bash
cp .env.example .env
```

Edite `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

O arquivo `.env` está no `.gitignore` e nunca deve ser commitado.

## Uso

### Modo web (recomendado)

```bash
cd src
uvicorn server:app --reload
```

Acesse `http://localhost:8000` no browser. O banco de dados é criado automaticamente na primeira execução. O histórico de conversa persiste durante a sessão da aba.

### Modo CLI

```bash
# Execução padrão
python src/app.py

# Escolher outro modelo Claude
python src/app.py --model claude-sonnet-4-6

# Exibir o loop ReAct completo (debug)
python src/app.py --verbose
```

**Exemplo de sessão CLI:**

```
============================================================
  Text2Analytics
  Banco: data/vendas.db
  Modelo: claude-haiku-4-5-20251001
  Digite 'sair' ou 'exit' para encerrar
============================================================

você> Qual o total de vendas por região?
agente> Aqui estão os totais de vendas por região (pedidos entregues):

╭──────────────┬───────────────╮
│ regiao       │   total_vendas│
├──────────────┼───────────────┤
│ Sudeste      │     245.300,00│
│ Sul          │     187.450,00│
│ Nordeste     │     134.200,00│
│ Centro-Oeste │      98.750,00│
│ Norte        │      67.100,00│
╰──────────────┴───────────────╯

você> sair
Até logo!
```

## Exemplos de perguntas

- "Qual o total de vendas por região?"
- "Quais os 5 produtos mais vendidos em quantidade?"
- "Qual o faturamento total por categoria?"
- "Quais clientes compraram mais de R$ 10.000 em pedidos entregues?"
- "Quantos pedidos foram cancelados por região?"
- "Qual o ticket médio dos pedidos entregues?"
- "Quantos pedidos entregues houve por mês?"
- "Quais clientes do segmento Varejo estão em SP?"

## Estrutura de arquivos

```
Text2Analytics/
├── README.md
├── .env.example
├── frontend/
│   ├── index.html          # Interface web de chat
│   ├── style.css           # Estilos da UI
│   └── chat.js             # Lógica de chat (session, fetch, loading)
├── src/
│   ├── app.py              # Entry point CLI + build_app_components()
│   ├── server.py           # Servidor FastAPI (web)
│   ├── requirements.txt
│   ├── seed.py             # Criação e população do banco de exemplo
│   ├── sql_executor.py     # Execução de queries + loop de auto-correção
│   ├── metadata.py         # Carregamento do metadata store YAML
│   ├── context_retriever.py# Embeddings + schema-linking semântico
│   ├── tools.py            # Factory de ferramentas LangChain
│   ├── agent.py            # Construção do AgentExecutor ReAct
│   └── memory.py           # ConversationMemory com compressão
├── data/
│   └── vendas.db           # Gerado automaticamente (no .gitignore)
├── metadata/
│   └── vendas.yaml         # Descrições ricas das tabelas/colunas
└── examples/
    └── few_shot.yaml       # Pares pergunta→SQL para few-shot retrieval
```

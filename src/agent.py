from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

_SYSTEM_PROMPT = """\
Você é um assistente especialista em análise de dados. Seu trabalho é responder perguntas \
sobre dados de vendas consultando um banco de dados SQLite via ferramentas.

Regras importantes:
- Sempre comece chamando get_schema para conhecer as tabelas relevantes antes de gerar SQL.
- Se get_schema retornar "NENHUM_DADO_ENCONTRADO", informe o usuário diretamente sem chamar query_database.
- Gere apenas queries SELECT. Nunca tente INSERT, UPDATE, DELETE ou DDL.
- Responda sempre em português, contextualizando os números obtidos.
- Se precisar de esclarecimento do usuário, use clarify_question antes de prosseguir.
"""


def build_agent(llm, tools, verbose: bool = False) -> AgentExecutor:
    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=6,
        handle_parsing_errors=True,
        verbose=verbose,
    )

from langchain_core.tools import tool

from context_retriever import ContextRetriever
from sql_executor import execute_with_correction


def make_tools(llm, db_path: str, retriever: ContextRetriever) -> list:
    @tool
    def get_schema(question: str) -> str:
        """Recupera o schema das tabelas mais relevantes para a pergunta do usuário,
        incluindo exemplos de SQL similares. Retorna 'NENHUM_DADO_ENCONTRADO' se
        não houver tabelas relevantes."""
        schema = retriever.get_relevant_schema(question)
        if schema is None:
            return "NENHUM_DADO_ENCONTRADO"
        examples = retriever.get_few_shot_examples(question)
        if examples:
            return f"{schema}\n\n{examples}"
        return schema

    @tool
    def query_database(sql: str) -> str:
        """Executa uma query SQL SELECT no banco de dados e retorna o resultado
        formatado como tabela. Apenas queries de leitura são permitidas."""
        result, success = execute_with_correction(sql, db_path, llm)

        if not success:
            return f"Erro ao executar a query: {result}"

        import pandas as pd
        from tabulate import tabulate

        df: pd.DataFrame = result
        total = len(df)
        display_df = df.head(50)
        table_str = tabulate(display_df, headers="keys", tablefmt="rounded_outline", showindex=False)

        if total > 50:
            table_str += f"\n(exibindo 50 de {total} linhas)"

        return table_str

    @tool
    def clarify_question(question: str) -> str:
        """Faz uma pergunta de esclarecimento ao usuário quando a intenção é ambígua."""
        print(f"\n[Agente pergunta]: {question}")
        return input("Sua resposta: ")

    return [get_schema, query_database, clarify_question]

import re
import sqlite3
import logging

import pandas as pd
import sqlparse
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|PRAGMA)\b",
    re.IGNORECASE,
)


def get_connection(path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def execute_query(sql: str, db_path: str) -> pd.DataFrame | str:
    """Executa SQL SELECT e retorna DataFrame, ou string de erro."""
    stripped = sql.strip()
    parsed = sqlparse.parse(stripped)
    if not parsed:
        return "Erro: SQL vazio ou inválido."

    stmt_type = parsed[0].get_type()
    if stmt_type != "SELECT":
        return "Erro de segurança: apenas queries SELECT são permitidas."

    if _FORBIDDEN_KEYWORDS.search(stripped):
        return "Erro de segurança: a query contém palavras-chave proibidas."

    try:
        conn = get_connection(db_path)
        df = pd.read_sql_query(stripped, conn)
        conn.close()
        return df
    except sqlite3.OperationalError as e:
        return f"Erro SQLite: {e}"
    except Exception as e:
        logger.error("Erro inesperado em execute_query: %s", e)
        return f"Erro inesperado: {e}"


def execute_with_correction(
    sql: str, db_path: str, llm, max_retries: int = 2
) -> tuple[pd.DataFrame | str, bool]:
    """Executa SQL com loop de auto-correção. Retorna (resultado, sucesso)."""
    current_sql = sql
    last_error = ""

    for attempt in range(max_retries + 1):
        result = execute_query(current_sql, db_path)

        if isinstance(result, pd.DataFrame):
            return result, True

        last_error = result

        if attempt < max_retries:
            prompt = (
                f"O seguinte SQL retornou um erro:\n\n"
                f"SQL:\n{current_sql}\n\n"
                f"Erro:\n{last_error}\n\n"
                f"Corrija o SQL para resolver o erro. "
                f"Responda APENAS com o SQL corrigido, sem explicações, sem markdown."
            )
            try:
                response = llm.invoke([HumanMessage(content=prompt)])
                raw = response.content
                match = re.search(r"```sql\s*(.*?)\s*```", raw, re.DOTALL)
                current_sql = match.group(1).strip() if match else raw.strip()
            except Exception as e:
                logger.error("Erro ao invocar LLM para correção: %s", e)
                return f"Erro na auto-correção: {e}", False

    return last_error, False

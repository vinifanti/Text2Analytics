import logging

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class ConversationMemory:
    def __init__(self, llm, max_messages: int = 6):
        self.llm = llm
        self.max_messages = max_messages
        self.messages: list[BaseMessage] = []
        self.connected_db: str = ""

    def add_message(self, role: str, content: str) -> None:
        content = content.strip()
        if role == "human":
            self.messages.append(HumanMessage(content=content))
        elif role == "ai":
            self.messages.append(AIMessage(content=content))
        else:
            logger.warning("Role desconhecido: %s", role)
            return

        if len(self.messages) > self.max_messages:
            self._compress()

    def _compress(self) -> None:
        msgs_to_compress = self.messages[:-self.max_messages]
        recent = self.messages[-self.max_messages:]

        text = "\n".join(
            f"{'Usuário' if isinstance(m, HumanMessage) else 'Assistente'}: {m.content}"
            for m in msgs_to_compress
        )
        prompt = (
            f"Resuma em 3-5 bullets as intenções e resultados desta conversa, em português:\n\n"
            f"{text}"
        )

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            summary = response.content.strip()
        except Exception as e:
            logger.error("Erro ao comprimir histórico: %s", e)
            summary = "(resumo indisponível)"

        self.messages = [SystemMessage(content=f"Contexto anterior:\n{summary}")] + recent

    def get_langchain_messages(self) -> list[BaseMessage]:
        return list(self.messages)

    def get_session_context(self) -> str:
        return f"Banco conectado: {self.connected_db} | Mensagens no histórico: {len(self.messages)}"

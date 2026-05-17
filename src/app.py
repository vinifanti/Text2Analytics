import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

from agent import build_agent
from context_retriever import ContextRetriever
from memory import ConversationMemory
from metadata import load_metadata
from seed import init_database
from tools import make_tools

DB_PATH = Path("data/vendas.db")
METADATA_PATH = Path("metadata")
EXAMPLES_PATH = Path("examples/few_shot.yaml")


def build_app_components(model: str = "claude-haiku-4-5-20251001", verbose: bool = False) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_database(str(DB_PATH))

    metadata = load_metadata(str(DB_PATH), str(METADATA_PATH))
    llm = ChatAnthropic(model=model)

    retriever = ContextRetriever(
        metadata=metadata,
        db_path=str(DB_PATH),
        examples_path=str(EXAMPLES_PATH),
    )

    tools = make_tools(llm, str(DB_PATH), retriever)
    agent = build_agent(llm, tools, verbose=verbose)

    return {"llm": llm, "retriever": retriever, "tools": tools, "agent": agent}


def main() -> None:
    parser = argparse.ArgumentParser(description="Text2Analytics — consulte dados em linguagem natural")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="Modelo Claude a usar")
    parser.add_argument("--verbose", action="store_true", help="Exibe o loop ReAct completo")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    components = build_app_components(model=args.model, verbose=args.verbose)
    agent = components["agent"]
    llm = components["llm"]

    criado = init_database(str(DB_PATH))
    if criado:
        print("Banco de dados criado com dados de exemplo.")
    else:
        print(f"Banco de dados encontrado: {DB_PATH}")

    memory = ConversationMemory(llm)
    memory.connected_db = str(DB_PATH)

    print(f"\n{'='*60}")
    print(f"  Text2Analytics")
    print(f"  Banco: {DB_PATH}")
    print(f"  Modelo: {args.model}")
    print(f"  Digite 'sair' ou 'exit' para encerrar")
    print(f"{'='*60}\n")

    while True:
        try:
            user_input = input("você> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAté logo!")
            sys.exit(0)

        if user_input.lower() in ("sair", "exit", "quit"):
            print("Até logo!")
            sys.exit(0)

        if not user_input:
            continue

        if args.verbose:
            print(f"\n[Debug] {memory.get_session_context()}")

        try:
            result = agent.invoke({
                "input": user_input,
                "chat_history": memory.get_langchain_messages(),
            })
            output = result.get("output", "Não foi possível gerar uma resposta.")
            if isinstance(output, list):
                response = " ".join(block.get("text", "") for block in output if block.get("type") == "text").strip()
            else:
                response = output
        except Exception as e:
            logging.error("Erro ao invocar o agente: %s", e)
            response = f"Ocorreu um erro ao processar sua pergunta: {e}"

        print(f"agente> {response}\n")

        memory.add_message("human", user_input)
        memory.add_message("ai", response)


if __name__ == "__main__":
    main()

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from starlette.concurrency import run_in_threadpool

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from app import build_app_components
from memory import ConversationMemory

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="Text2Analytics")

components: dict = {}
sessions: dict[str, ConversationMemory] = {}


@app.on_event("startup")
def startup() -> None:
    global components
    components = build_app_components()
    logger.info("Componentes inicializados com sucesso.")


class ChatRequest(BaseModel):
    session_id: str
    message: str

    @field_validator("message")
    @classmethod
    def message_nao_vazia(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message não pode ser vazia")
        return v.strip()


class ChatResponse(BaseModel):
    response: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if req.session_id not in sessions:
        mem = ConversationMemory(components["llm"])
        mem.connected_db = "data/vendas.db"
        sessions[req.session_id] = mem

    memory = sessions[req.session_id]
    agent = components["agent"]

    invoke_input = {
        "input": req.message,
        "chat_history": memory.get_langchain_messages(),
    }

    try:
        result = await run_in_threadpool(agent.invoke, invoke_input)
        output = result.get("output", "Não foi possível gerar uma resposta.")
        if isinstance(output, list):
            response_text = " ".join(
                block.get("text", "") for block in output if block.get("type") == "text"
            ).strip()
        else:
            response_text = output
    except Exception as e:
        logger.error("Erro ao invocar o agente: %s", e)
        response_text = f"Ocorreu um erro ao processar sua pergunta: {e}"

    memory.add_message("human", req.message)
    memory.add_message("ai", response_text)

    return ChatResponse(response=response_text)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

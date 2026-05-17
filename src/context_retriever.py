import sqlite3
import logging
from pathlib import Path

import numpy as np
import yaml
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_THRESHOLD = 0.3


class ContextRetriever:
    def __init__(self, metadata: dict, db_path: str, examples_path: str):
        print("Carregando modelos de embedding (primeira execução pode demorar)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.metadata = metadata
        self.db_path = db_path

        self._schema_texts: list[str] = []
        self._schema_keys: list[str] = []
        self._schema_embeddings: np.ndarray = np.empty((0,))
        self._index_schema()

        self.examples: list[dict] = []
        self.examples_embeddings: np.ndarray = np.empty((0,))
        self._index_examples(examples_path)

    def _index_schema(self) -> None:
        ddl_map = self._get_ddl_map()
        for table, info in self.metadata.items():
            desc = info.get("description", "")
            cols_desc = " | ".join(
                f"{col}: {d}" for col, d in info.get("columns", {}).items()
            )
            text = f"{table}: {desc}. Colunas: {cols_desc}"
            self._schema_texts.append(text)
            self._schema_keys.append(table)

        if self._schema_texts:
            self._schema_embeddings = self.model.encode(
                self._schema_texts, convert_to_numpy=True
            )
        self._ddl_map = ddl_map

    def _index_examples(self, examples_path: str) -> None:
        path = Path(examples_path)
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return
        self.examples = data
        questions = [ex["question"] for ex in self.examples]
        self.examples_embeddings = self.model.encode(questions, convert_to_numpy=True)

    def _get_ddl_map(self) -> dict[str, str]:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        rows = cursor.fetchall()
        conn.close()
        return {name: sql for name, sql in rows if sql}

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b, axis=1, keepdims=True)
        if norm_a == 0:
            return np.zeros(len(b))
        return (b @ a) / (norm_b.squeeze() * norm_a + 1e-9)

    def get_relevant_schema(self, question: str, top_k: int = 5) -> str | None:
        if self._schema_embeddings.shape[0] == 0:
            return None

        q_emb = self.model.encode([question], convert_to_numpy=True)[0]
        scores = self._cosine_similarity(q_emb, self._schema_embeddings)

        if scores.max() < _THRESHOLD:
            return None

        top_indices = np.argsort(scores)[::-1][:top_k]
        parts: list[str] = []
        for idx in top_indices:
            if scores[idx] < _THRESHOLD:
                break
            table = self._schema_keys[idx]
            ddl = self._ddl_map.get(table, f"-- DDL não disponível para {table}")
            col_descs = self.metadata.get(table, {}).get("columns", {})
            comments = "\n".join(
                f"  -- {col}: {desc}" for col, desc in col_descs.items()
            )
            parts.append(f"{ddl}\n{comments}")

        return "\n\n".join(parts) if parts else None

    def get_few_shot_examples(self, question: str, top_k: int = 3) -> str:
        if len(self.examples) == 0 or self.examples_embeddings.shape[0] == 0:
            return ""

        q_emb = self.model.encode([question], convert_to_numpy=True)[0]
        scores = self._cosine_similarity(q_emb, self.examples_embeddings)
        top_indices = np.argsort(scores)[::-1][:top_k]

        lines: list[str] = ["Exemplos:"]
        for idx in top_indices:
            ex = self.examples[idx]
            lines.append(f"Pergunta: {ex['question']}")
            lines.append(f"SQL: {ex['sql']}")
            lines.append("")

        return "\n".join(lines).strip()

import logging
import sqlite3
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_metadata(db_path: str, metadata_dir: str = "metadata") -> dict:
    """Carrega ou gera metadata store YAML para o banco informado."""
    db_name = Path(db_path).stem
    yaml_path = Path(metadata_dir) / f"{db_name}.yaml"

    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    logger.info("Metadata YAML não encontrado. Gerando a partir do schema do banco...")
    print(
        f"Metadata não encontrado para '{db_name}'. "
        f"Gerando automaticamente a partir do schema... "
        f"(você pode enriquecer '{yaml_path}' manualmente depois)"
    )

    metadata = _generate_from_schema(db_path)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False)

    return metadata


def _generate_from_schema(db_path: str) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    metadata: dict = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        metadata[table] = {
            "description": f"Tabela {table}",
            "columns": {col[1]: f"Coluna {col[1]} ({col[2]})" for col in columns},
        }

    conn.close()
    return metadata

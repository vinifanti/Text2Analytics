import sqlite3
from pathlib import Path


def init_database(path: str) -> bool:
    """Cria e popula o banco se não existir. Retorna True se criou, False se já existia."""
    db_path = Path(path)
    already_exists = db_path.exists()

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    if already_exists:
        conn.close()
        return False

    cursor.executescript("""
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            cidade TEXT NOT NULL,
            estado TEXT NOT NULL,
            segmento TEXT NOT NULL
        );

        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER NOT NULL,
            produto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            data_pedido TEXT NOT NULL,
            status TEXT NOT NULL,
            regiao TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
    """)

    clientes = [
        (1, "Empresa Alpha Ltda", "São Paulo", "SP", "Varejo"),
        (2, "Beta Comercial", "Rio de Janeiro", "RJ", "Atacado"),
        (3, "Gamma Distribuidora", "Belo Horizonte", "MG", "Distribuidor"),
        (4, "Delta Tech", "Curitiba", "PR", "Varejo"),
        (5, "Epsilon Serviços", "Porto Alegre", "RS", "Varejo"),
        (6, "Zeta Indústria", "Fortaleza", "CE", "Indústria"),
        (7, "Eta Comércio", "Manaus", "AM", "Varejo"),
        (8, "Theta Atacado", "Salvador", "BA", "Atacado"),
        (9, "Iota Logística", "Recife", "PE", "Distribuidor"),
        (10, "Kappa Soluções", "Brasília", "DF", "Varejo"),
        (11, "Lambda Importações", "Campinas", "SP", "Atacado"),
        (12, "Mu Tecnologia", "Florianópolis", "SC", "Varejo"),
    ]

    cursor.executemany(
        "INSERT INTO clientes VALUES (?, ?, ?, ?, ?)", clientes
    )

    pedidos = [
        # Janeiro — região Sul
        (1,  1,  "Notebook Pro",       "Eletrônicos",  3500.00, 2, "2024-01-05", "entregue",   "Sul"),
        (2,  4,  "Mouse Sem Fio",      "Periféricos",   150.00, 5, "2024-01-08", "entregue",   "Sul"),
        (3,  5,  "Teclado Mecânico",   "Periféricos",   400.00, 3, "2024-01-12", "entregue",   "Sul"),
        (4,  12, "Monitor 24pol",      "Eletrônicos",  1200.00, 1, "2024-01-15", "entregue",   "Sul"),
        (5,  4,  "Cadeira Gamer",      "Móveis",        900.00, 2, "2024-01-18", "entregue",   "Sul"),
        (6,  5,  "Mesa de Escritório", "Móveis",        750.00, 1, "2024-01-22", "cancelado",  "Sul"),
        (7,  12, "Webcam HD",          "Periféricos",   250.00, 4, "2024-01-25", "entregue",   "Sul"),
        (8,  4,  "Headset Gamer",      "Periféricos",   320.00, 3, "2024-01-28", "entregue",   "Sul"),
        (9,  5,  "SSD 1TB",            "Eletrônicos",   480.00, 2, "2024-01-30", "entregue",   "Sul"),
        (10, 12, "Impressora Laser",   "Eletrônicos",  1800.00, 1, "2024-01-31", "entregue",   "Sul"),
        # Fevereiro — região Nordeste
        (11, 6,  "Smartphone Galaxy",  "Eletrônicos",  2800.00, 3, "2024-02-03", "entregue",   "Nordeste"),
        (12, 8,  "Tablet 10pol",       "Eletrônicos",  1500.00, 2, "2024-02-07", "entregue",   "Nordeste"),
        (13, 9,  "Cabo USB-C",         "Periféricos",    45.00,10, "2024-02-10", "entregue",   "Nordeste"),
        (14, 6,  "Roteador WiFi6",     "Eletrônicos",   650.00, 5, "2024-02-13", "entregue",   "Nordeste"),
        (15, 8,  "Rack Servidor",      "Móveis",       2200.00, 1, "2024-02-16", "entregue",   "Nordeste"),
        (16, 9,  "Pen Drive 64GB",     "Periféricos",    80.00, 8, "2024-02-18", "cancelado",  "Nordeste"),
        (17, 6,  "Carregador Turbo",   "Periféricos",   120.00, 6, "2024-02-20", "entregue",   "Nordeste"),
        (18, 8,  "Notebook Slim",      "Eletrônicos",  4200.00, 2, "2024-02-23", "entregue",   "Nordeste"),
        (19, 9,  "Estabilizador 1kVA", "Eletrônicos",   350.00, 3, "2024-02-26", "entregue",   "Nordeste"),
        (20, 6,  "Suporte Monitor",    "Móveis",        180.00, 4, "2024-02-28", "entregue",   "Nordeste"),
        # Março — região Sudeste
        (21, 1,  "MacBook Air",        "Eletrônicos",  8500.00, 1, "2024-03-02", "entregue",   "Sudeste"),
        (22, 2,  "iPad Pro",           "Eletrônicos",  5000.00, 2, "2024-03-05", "entregue",   "Sudeste"),
        (23, 3,  "AirPods Pro",        "Periféricos",  1800.00, 3, "2024-03-08", "entregue",   "Sudeste"),
        (24, 10, "iMac 27pol",         "Eletrônicos", 12000.00, 1, "2024-03-11", "entregue",   "Sudeste"),
        (25, 11, "Apple Watch",        "Eletrônicos",  3200.00, 2, "2024-03-14", "entregue",   "Sudeste"),
        (26, 1,  "Magic Keyboard",     "Periféricos",   900.00, 4, "2024-03-17", "cancelado",  "Sudeste"),
        (27, 2,  "HomePod Mini",       "Eletrônicos",  1200.00, 3, "2024-03-20", "entregue",   "Sudeste"),
        (28, 3,  "Mesa Gamer",         "Móveis",       1100.00, 2, "2024-03-22", "entregue",   "Sudeste"),
        (29, 10, "Poltrona Ergonomica","Móveis",       1800.00, 1, "2024-03-25", "entregue",   "Sudeste"),
        (30, 11, "NAS 4 Bay",          "Eletrônicos",  3600.00, 1, "2024-03-28", "entregue",   "Sudeste"),
        # Norte
        (31, 7,  "TV 55pol OLED",      "Eletrônicos",  6500.00, 1, "2024-03-04", "entregue",   "Norte"),
        (32, 7,  "Soundbar 2.1",       "Eletrônicos",   900.00, 2, "2024-03-09", "entregue",   "Norte"),
        (33, 7,  "Armario Office",     "Móveis",       1300.00, 1, "2024-03-15", "cancelado",  "Norte"),
    ]

    cursor.executemany(
        "INSERT INTO pedidos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", pedidos
    )

    conn.commit()
    conn.close()
    return True

"""
Módulo ETL - Automação de pipeline de dados
Extract → Transform → Load
"""

import json
import os
import random
from datetime import datetime, timedelta
from app.database import get_connection

PRODUTOS = {
    "Eletrônicos":    ["Smartphone", "Notebook", "Tablet", "Fone Bluetooth", "Smartwatch"],
    "Vestuário":      ["Camiseta", "Calça Jeans", "Tênis", "Jaqueta", "Vestido"],
    "Alimentos":      ["Café Premium", "Azeite", "Vinho", "Chocolates", "Granola"],
    "Casa & Jardim":  ["Luminária", "Tapete", "Vaso", "Ferramentas", "Almofada"],
    "Esportes":       ["Whey Protein", "Bicicleta", "Esteira", "Luvas Box", "Mochila Trilha"],
}
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
PRECOS = {
    "Smartphone": (800, 5000), "Notebook": (2000, 9000), "Tablet": (700, 3000),
    "Fone Bluetooth": (150, 800), "Smartwatch": (300, 2000),
    "Camiseta": (30, 150), "Calça Jeans": (80, 400), "Tênis": (120, 600),
    "Jaqueta": (150, 900), "Vestido": (80, 500),
    "Café Premium": (25, 100), "Azeite": (30, 120), "Vinho": (40, 300),
    "Chocolates": (15, 80), "Granola": (20, 60),
    "Luminária": (80, 500), "Tapete": (100, 800), "Vaso": (30, 250),
    "Ferramentas": (50, 400), "Almofada": (40, 200),
    "Whey Protein": (80, 300), "Bicicleta": (500, 5000), "Esteira": (1000, 8000),
    "Luvas Box": (60, 300), "Mochila Trilha": (150, 800),
}

def _extract_simulated_data(n: int = 200) -> list:
    """
    Simula extração de dados de uma fonte externa (CSV, API, etc.).
    Em produção: substituir por pd.read_csv(), requests.get(), etc.
    """
    registros = []
    hoje = datetime.now()
    for _ in range(n):
        categoria = random.choice(list(PRODUTOS.keys()))
        produto = random.choice(PRODUTOS[categoria])
        preco_min, preco_max = PRECOS.get(produto, (50, 500))
        preco = round(random.uniform(preco_min, preco_max), 2)
        qtd = random.randint(1, 10)
        dias_atras = random.randint(0, 365)
        data = (hoje - timedelta(days=dias_atras)).strftime("%Y-%m-%dT%H:%M:%S")
        registros.append({
            "produto": produto,
            "categoria": categoria,
            "quantidade": qtd,
            "preco_unitario": preco,
            "regiao": random.choice(REGIOES),
            "data": data,
        })
    return registros

def _transform(registros: list) -> list:
    """
    Aplica regras de negócio e limpeza:
    - Remove duplicatas exatas
    - Descarta registros com preço zero
    - Calcula total
    - Normaliza strings
    """
    vistos = set()
    limpos = []
    for r in registros:
        if r["preco_unitario"] <= 0 or r["quantidade"] <= 0:
            continue
        chave = (r["produto"], r["data"], r["regiao"])
        if chave in vistos:
            continue
        vistos.add(chave)
        r["produto"] = r["produto"].strip().title()
        r["total"] = round(r["quantidade"] * r["preco_unitario"], 2)
        limpos.append(r)
    return limpos

def _load(registros: list) -> int:
    """Insere registros transformados no banco de dados."""
    count = 0
    with get_connection() as conn:
        for r in registros:
            conn.execute(
                """INSERT INTO vendas (produto, categoria, quantidade, preco_unitario, total, regiao, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (r["produto"], r["categoria"], r["quantidade"],
                 r["preco_unitario"], r["total"], r["regiao"], r["data"])
            )
            count += 1
    return count

def run_etl_pipeline(n_registros: int = 100):
    """
    Executa o pipeline completo Extract → Transform → Load.
    Grava log em data/etl_log.json.
    """
    inicio = datetime.now()
    log = {"iniciado_em": inicio.isoformat(), "status": "erro", "registros_inseridos": 0}

    try:
        print(f"[ETL] Extraindo {n_registros} registros...")
        raw = _extract_simulated_data(n_registros)

        print("[ETL] Transformando dados...")
        clean = _transform(raw)

        print(f"[ETL] Carregando {len(clean)} registros no banco...")
        inseridos = _load(clean)

        duracao = (datetime.now() - inicio).total_seconds()
        log.update({
            "status": "sucesso",
            "registros_extraidos": len(raw),
            "registros_apos_limpeza": len(clean),
            "registros_inseridos": inseridos,
            "duracao_segundos": round(duracao, 2),
            "finalizado_em": datetime.now().isoformat(),
        })
        print(f"[ETL] Concluído em {duracao:.1f}s — {inseridos} registros inseridos.")

    except Exception as e:
        log["erro"] = str(e)
        print(f"[ETL] Erro: {e}")

    os.makedirs("data", exist_ok=True)
    with open("data/etl_log.json", "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    # Grava no banco também
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO etl_runs (executado_em, registros, status, detalhes)
               VALUES (?, ?, ?, ?)""",
            (log["iniciado_em"], log.get("registros_inseridos", 0),
             log["status"], json.dumps(log, ensure_ascii=False))
        )

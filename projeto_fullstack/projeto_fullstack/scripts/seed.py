"""
Script de seed - popula o banco com dados iniciais para demonstração
"""

import random
from datetime import datetime, timedelta
from app.database import get_connection

PRODUTOS = {
    "Eletrônicos":    [("Smartphone", 1200, 4500), ("Notebook", 2500, 8000),
                       ("Tablet", 800, 2500), ("Fone Bluetooth", 200, 700), ("Smartwatch", 400, 1800)],
    "Vestuário":      [("Camiseta", 40, 130), ("Calça Jeans", 90, 380),
                       ("Tênis", 130, 550), ("Jaqueta", 160, 850), ("Vestido", 90, 480)],
    "Alimentos":      [("Café Premium", 28, 95), ("Azeite", 35, 115),
                       ("Vinho", 45, 280), ("Chocolates", 18, 75), ("Granola", 22, 58)],
    "Casa & Jardim":  [("Luminária", 85, 480), ("Tapete", 110, 750),
                       ("Vaso", 35, 240), ("Ferramentas", 55, 380), ("Almofada", 45, 190)],
    "Esportes":       [("Whey Protein", 90, 280), ("Bicicleta", 600, 4800),
                       ("Esteira", 1200, 7500), ("Luvas Box", 65, 280), ("Mochila Trilha", 160, 750)],
}
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

# Pesos de sazonalidade por mês (1=jan..12=dez)
SAZONALIDADE = [0.7, 0.65, 0.8, 0.85, 0.9, 1.0, 0.95, 1.0, 0.9, 1.1, 1.3, 1.5]

# Pesos por região (Sudeste maior mercado)
PESO_REGIAO = {"Norte": 0.7, "Nordeste": 0.9, "Centro-Oeste": 0.8, "Sudeste": 1.5, "Sul": 1.1}

def seed_database(n: int = 500):
    """Insere n transações de vendas com padrões realistas."""
    hoje = datetime.now()
    registros = []

    for _ in range(n):
        categoria = random.choice(list(PRODUTOS.keys()))
        nome, pmin, pmax = random.choice(PRODUTOS[categoria])
        regiao = random.choice(REGIOES)
        dias_atras = random.randint(0, 365)
        data = hoje - timedelta(days=dias_atras)
        mes = data.month

        # Aplica sazonalidade e peso regional ao preço
        fator = SAZONALIDADE[mes - 1] * PESO_REGIAO[regiao]
        preco = round(random.uniform(pmin, pmax) * fator, 2)
        qtd = random.randint(1, 8)
        total = round(preco * qtd, 2)

        registros.append((nome, categoria, qtd, preco, total, regiao, data.strftime("%Y-%m-%dT%H:%M:%S")))

    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO vendas (produto, categoria, quantidade, preco_unitario, total, regiao, data)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            registros
        )
    print(f"[Seed] {len(registros)} vendas inseridas.")

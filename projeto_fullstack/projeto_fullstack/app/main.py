"""
Sistema de Análise de Vendas com IA
API principal - FastAPI + SQLite + ML + LLM
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
from datetime import datetime

from app.database import init_db, get_connection
from app.ml_model import predict_sales, train_model
from app.etl import run_etl_pipeline
from app.ai_analyst import analyze_with_ai

app = FastAPI(
    title="Sales Analytics API",
    description="API de análise de vendas com ML e IA integrados",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Models (Pydantic)
# ─────────────────────────────────────────

class SaleInput(BaseModel):
    produto: str
    categoria: str
    quantidade: int
    preco_unitario: float
    regiao: str
    data: Optional[str] = None  # ISO format

class PredictRequest(BaseModel):
    mes: int       # 1–12
    regiao: str
    categoria: str

class AIAnalysisRequest(BaseModel):
    pergunta: str

# ─────────────────────────────────────────
# Startup
# ─────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()
    # Popula banco com dados simulados se vazio
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0]
        if count == 0:
            from scripts.seed import seed_database
            seed_database()
    train_model()

# ─────────────────────────────────────────
# Endpoints - CRUD de Vendas
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "online", "docs": "/docs"}

@app.post("/vendas", status_code=201)
def criar_venda(sale: SaleInput):
    """Registra uma nova venda."""
    data = sale.data or datetime.now().isoformat()
    total = sale.quantidade * sale.preco_unitario
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO vendas (produto, categoria, quantidade, preco_unitario, total, regiao, data)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sale.produto, sale.categoria, sale.quantidade,
             sale.preco_unitario, total, sale.regiao, data)
        )
    return {"message": "Venda registrada", "total": total}

@app.get("/vendas")
def listar_vendas(limite: int = 50, regiao: Optional[str] = None, categoria: Optional[str] = None):
    """Lista vendas com filtros opcionais."""
    query = "SELECT * FROM vendas WHERE 1=1"
    params = []
    if regiao:
        query += " AND regiao = ?"
        params.append(regiao)
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    query += f" ORDER BY data DESC LIMIT {limite}"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]

@app.get("/vendas/resumo")
def resumo_vendas():
    """Agrega KPIs de vendas por região e categoria."""
    with get_connection() as conn:
        por_regiao = conn.execute("""
            SELECT regiao,
                   COUNT(*) as transacoes,
                   SUM(total) as receita,
                   AVG(total) as ticket_medio
            FROM vendas GROUP BY regiao ORDER BY receita DESC
        """).fetchall()
        por_categoria = conn.execute("""
            SELECT categoria,
                   COUNT(*) as transacoes,
                   SUM(total) as receita
            FROM vendas GROUP BY categoria ORDER BY receita DESC
        """).fetchall()
        mensal = conn.execute("""
            SELECT strftime('%Y-%m', data) as mes,
                   SUM(total) as receita,
                   COUNT(*) as transacoes
            FROM vendas GROUP BY mes ORDER BY mes
        """).fetchall()
    return {
        "por_regiao": [dict(r) for r in por_regiao],
        "por_categoria": [dict(r) for r in por_categoria],
        "mensal": [dict(r) for r in mensal],
    }

# ─────────────────────────────────────────
# Endpoint - Machine Learning
# ─────────────────────────────────────────

@app.post("/ml/prever")
def prever_vendas(req: PredictRequest):
    """Prevê receita usando modelo de ML treinado nos dados históricos."""
    resultado = predict_sales(req.mes, req.regiao, req.categoria)
    return resultado

@app.post("/ml/retreinar")
def retreinar_modelo(background_tasks: BackgroundTasks):
    """Retreina o modelo ML em background."""
    background_tasks.add_task(train_model)
    return {"message": "Retreinamento iniciado em background"}

# ─────────────────────────────────────────
# Endpoint - ETL / Automação
# ─────────────────────────────────────────

@app.post("/etl/executar")
def executar_etl(background_tasks: BackgroundTasks):
    """Executa pipeline ETL: extrai, transforma e carrega dados."""
    background_tasks.add_task(run_etl_pipeline)
    return {"message": "Pipeline ETL iniciado"}

@app.get("/etl/status")
def status_etl():
    """Verifica log do último ETL executado."""
    try:
        with open("data/etl_log.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"status": "nenhum ETL executado ainda"}

# ─────────────────────────────────────────
# Endpoint - IA Analista
# ─────────────────────────────────────────

@app.post("/ia/analisar")
async def analisar_com_ia(req: AIAnalysisRequest):
    """
    Envia dados de vendas + pergunta para a IA (Claude API)
    e retorna uma análise em linguagem natural.
    """
    resultado = await analyze_with_ai(req.pergunta)
    return resultado

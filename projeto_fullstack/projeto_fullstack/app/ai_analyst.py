"""
Módulo de IA - Analista de Vendas
Envia dados do banco + pergunta para Claude API
e retorna análise em linguagem natural.
"""

import httpx
import json
import os
from app.database import get_connection

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"

def _get_sales_context() -> str:
    """Coleta resumo dos dados de vendas para contexto da IA."""
    with get_connection() as conn:
        total_receita = conn.execute("SELECT SUM(total) FROM vendas").fetchone()[0] or 0
        total_transacoes = conn.execute("SELECT COUNT(*) FROM vendas").fetchone()[0] or 0
        ticket_medio = conn.execute("SELECT AVG(total) FROM vendas").fetchone()[0] or 0

        por_regiao = conn.execute("""
            SELECT regiao, COUNT(*) as qtd, SUM(total) as receita
            FROM vendas GROUP BY regiao ORDER BY receita DESC
        """).fetchall()

        por_categoria = conn.execute("""
            SELECT categoria, COUNT(*) as qtd, SUM(total) as receita
            FROM vendas GROUP BY categoria ORDER BY receita DESC
        """).fetchall()

        top_produtos = conn.execute("""
            SELECT produto, SUM(total) as receita, SUM(quantidade) as unidades
            FROM vendas GROUP BY produto ORDER BY receita DESC LIMIT 5
        """).fetchall()

        mensal = conn.execute("""
            SELECT strftime('%Y-%m', data) as mes, SUM(total) as receita
            FROM vendas GROUP BY mes ORDER BY mes DESC LIMIT 6
        """).fetchall()

    linhas = [
        f"RESUMO GERAL:",
        f"- Total de transações: {total_transacoes:,}",
        f"- Receita total: R$ {total_receita:,.2f}",
        f"- Ticket médio: R$ {ticket_medio:,.2f}",
        "",
        "RECEITA POR REGIÃO:",
    ]
    for r in por_regiao:
        linhas.append(f"  {r['regiao']}: R$ {r['receita']:,.2f} ({r['qtd']} transações)")

    linhas += ["", "RECEITA POR CATEGORIA:"]
    for c in por_categoria:
        linhas.append(f"  {c['categoria']}: R$ {c['receita']:,.2f} ({c['qtd']} transações)")

    linhas += ["", "TOP 5 PRODUTOS POR RECEITA:"]
    for p in top_produtos:
        linhas.append(f"  {p['produto']}: R$ {p['receita']:,.2f} ({p['unidades']} unidades)")

    linhas += ["", "EVOLUÇÃO MENSAL (últimos 6 meses):"]
    for m in mensal:
        linhas.append(f"  {m['mes']}: R$ {m['receita']:,.2f}")

    return "\n".join(linhas)

async def analyze_with_ai(pergunta: str) -> dict:
    """
    Envia contexto de dados + pergunta para Claude API.
    Retorna análise em linguagem natural.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {
            "erro": "ANTHROPIC_API_KEY não definida. Configure a variável de ambiente.",
            "dica": "export ANTHROPIC_API_KEY=sk-ant-..."
        }

    contexto = _get_sales_context()

    system_prompt = """Você é um analista de dados sênior especializado em vendas e varejo.
Recebe dados reais de vendas e responde perguntas de negócio com clareza e objetividade.
Sempre baseie sua análise nos dados fornecidos. Quando relevante, sugira ações práticas.
Responda em português brasileiro, de forma direta e estruturada."""

    user_message = f"""Dados de vendas atuais do sistema:

{contexto}

---
Pergunta do usuário: {pergunta}"""

    payload = {
        "model": MODEL,
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            analise = data["content"][0]["text"]

        return {
            "pergunta": pergunta,
            "analise": analise,
            "modelo": MODEL,
            "tokens_usados": data.get("usage", {})
        }

    except httpx.HTTPStatusError as e:
        return {"erro": f"Erro na API Anthropic: {e.response.status_code}", "detalhe": e.response.text}
    except Exception as e:
        return {"erro": str(e)}

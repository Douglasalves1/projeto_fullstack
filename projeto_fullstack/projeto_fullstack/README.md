# 🚀 Sales Analytics API — Stack Completa

Projeto intermediário que integra **todas as hard skills**:
Python · FastAPI · SQLite · Machine Learning · ETL/Automação · IA (Claude API)

---

## 📁 Estrutura

```
projeto_fullstack/
├── app/
│   ├── main.py          # API FastAPI (endpoints)
│   ├── database.py      # Banco SQLite + context manager
│   ├── ml_model.py      # Machine Learning (Random Forest)
│   ├── etl.py           # Pipeline ETL automatizado
│   └── ai_analyst.py    # Integração com Claude API
├── scripts/
│   └── seed.py          # Dados iniciais (500 vendas)
├── data/                # Banco .db e logs ETL (gerado em runtime)
├── models/              # Modelo ML salvo (gerado em runtime)
├── requirements.txt
└── README.md
```

---

## ⚡ Setup

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar API key da IA (opcional — só para /ia/analisar)
export ANTHROPIC_API_KEY=sk-ant-...   # Linux/Mac
set ANTHROPIC_API_KEY=sk-ant-...      # Windows

# 4. Rodar a API
uvicorn app.main:app --reload
```

Acesse: http://localhost:8000/docs

---

## 📡 Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Status da API |
| POST | `/vendas` | Registrar venda |
| GET | `/vendas` | Listar vendas (filtros: regiao, categoria) |
| GET | `/vendas/resumo` | KPIs agregados por região, categoria e mês |
| POST | `/ml/prever` | Prever receita com ML |
| POST | `/ml/retreinar` | Retreinar modelo em background |
| POST | `/etl/executar` | Executar pipeline ETL |
| GET | `/etl/status` | Ver log do último ETL |
| POST | `/ia/analisar` | Análise em linguagem natural via Claude |

---

## 🧪 Exemplos de uso

### Registrar venda
```bash
curl -X POST http://localhost:8000/vendas \
  -H "Content-Type: application/json" \
  -d '{"produto":"Notebook","categoria":"Eletrônicos","quantidade":2,"preco_unitario":4500.00,"regiao":"Sudeste"}'
```

### Prever receita com ML
```bash
curl -X POST http://localhost:8000/ml/prever \
  -H "Content-Type: application/json" \
  -d '{"mes":12,"regiao":"Sudeste","categoria":"Eletrônicos"}'
```

### Análise com IA
```bash
curl -X POST http://localhost:8000/ia/analisar \
  -H "Content-Type: application/json" \
  -d '{"pergunta":"Qual região tem maior potencial de crescimento?"}'
```

---

## 🧠 Como cada skill é usada

- **Python** — linguagem base de todo o projeto
- **FastAPI** — API REST com documentação automática (Swagger em /docs)
- **Banco de Dados** — SQLite com context manager, queries agregadas
- **Machine Learning** — Random Forest para previsão de receita
- **ETL / Automação** — pipeline Extract → Transform → Load com log
- **IA / LLM** — Claude API responde perguntas de negócio com dados reais

---

## 🔧 Próximos passos sugeridos

- Trocar SQLite por PostgreSQL (production-ready)
- Adicionar autenticação JWT
- Dockerizar a aplicação
- Criar dashboard com Streamlit ou React
- Agendar ETL com Celery + Redis

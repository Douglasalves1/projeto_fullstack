"""
Módulo de Machine Learning
Treinamento e predição de receita de vendas
usando Random Forest com sklearn
"""

import pickle
import os
import numpy as np
from datetime import datetime

MODEL_PATH = "models/sales_model.pkl"
ENCODER_PATH = "models/encoders.pkl"

# Mapeamentos para encoding
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
CATEGORIAS = ["Eletrônicos", "Vestuário", "Alimentos", "Casa & Jardim", "Esportes"]

def _encode(mes: int, regiao: str, categoria: str) -> list:
    """Converte inputs categóricos em features numéricas."""
    regiao_enc = REGIOES.index(regiao) if regiao in REGIOES else 0
    cat_enc = CATEGORIAS.index(categoria) if categoria in CATEGORIAS else 0
    # Features: mês, mês_seno (sazonalidade), mês_cosseno, regiao, categoria
    mes_sin = np.sin(2 * np.pi * mes / 12)
    mes_cos = np.cos(2 * np.pi * mes / 12)
    return [mes, mes_sin, mes_cos, regiao_enc, cat_enc]

def train_model():
    """
    Treina um modelo Random Forest com dados do banco.
    Salva o modelo em disco para uso posterior.
    """
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_absolute_error, r2_score
        from app.database import get_connection
        import json

        os.makedirs("models", exist_ok=True)

        with get_connection() as conn:
            rows = conn.execute("""
                SELECT strftime('%m', data) as mes, regiao, categoria, SUM(total) as receita
                FROM vendas
                GROUP BY mes, regiao, categoria
            """).fetchall()

        if len(rows) < 10:
            print("Dados insuficientes para treinar modelo.")
            return

        X, y = [], []
        for row in rows:
            try:
                features = _encode(int(row["mes"]), row["regiao"], row["categoria"])
                X.append(features)
                y.append(row["receita"])
            except Exception:
                continue

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)

        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)

        meta = {
            "treinado_em": datetime.now().isoformat(),
            "amostras": len(X),
            "mae": round(mae, 2),
            "r2_score": round(r2, 4),
            "features": ["mes", "mes_sin", "mes_cos", "regiao_enc", "categoria_enc"]
        }
        with open("models/meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        print(f"Modelo treinado | MAE: {mae:.2f} | R²: {r2:.4f}")

    except ImportError:
        print("sklearn não instalado — execute: pip install scikit-learn")
    except Exception as e:
        print(f"Erro no treinamento: {e}")

def predict_sales(mes: int, regiao: str, categoria: str) -> dict:
    """Carrega modelo salvo e retorna predição de receita."""
    import json

    if not os.path.exists(MODEL_PATH):
        return {"erro": "Modelo não treinado. Execute POST /ml/retreinar"}

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    features = [_encode(mes, regiao, categoria)]
    predicao = model.predict(features)[0]

    meta = {}
    if os.path.exists("models/meta.json"):
        with open("models/meta.json") as f:
            meta = json.load(f)

    return {
        "mes": mes,
        "regiao": regiao,
        "categoria": categoria,
        "receita_prevista": round(predicao, 2),
        "modelo": {
            "treinado_em": meta.get("treinado_em"),
            "r2_score": meta.get("r2_score"),
            "mae": meta.get("mae"),
        }
    }

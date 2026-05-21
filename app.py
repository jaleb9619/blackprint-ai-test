# uvicorn app:app --reload --port 8000

import json
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

app = FastAPI(title="BlackPrint avaluos API")

app.mount("/static", StaticFiles(directory="static"), name="static")

# app.mount("/static", StaticFiles(directory="static"))

DATA_PATH = "static/data.json"
_data = None

def get_data():
    global _data
    if _data is None:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            _data = json.load(f)
    return _data

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/api/stats")
def stats():
    return get_data()["stats"]

@app.get("/api/records")
def records(
    estado: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    clase: Optional[str] = Query(None),
    conservacion: Optional[str] = Query(None),
    grupo: Optional[str] = Query(None),
    valor_min: Optional[float] = Query(None),
    valor_max: Optional[float] = Query(None),
    recamaras: Optional[int] = Query(None),
    limit: int = Query(2000, le=5000),
):
    records = get_data()["records"]

    if estado:
        records = [r for r in records if r.get("estado") == estado]
    if tipo:
        records = [r for r in records if r.get("tipo") == tipo]
    if clase:
        records = [r for r in records if r.get("clase") == clase]
    if conservacion:
        records = [r for r in records if r.get("conservacion") == conservacion]
    if grupo:
        records = [r for r in records if r.get("grupo") == grupo]
    if valor_min is not None:
        records = [r for r in records if r.get("valor", 0) >= valor_min]
    if valor_max is not None:
        records = [r for r in records if r.get("valor", 0) <= valor_max]
    if recamaras is not None:
        records = [r for r in records if r.get("recamaras") == recamaras]

    # Calcular stats del subconjunto filtrado
    valores = [r["valor"] for r in records if r.get("valor")]
    m2s = [r["m2_sv"] for r in records if r.get("m2_sv")]

    subset_stats = {
        "total": len(records),
        "valor_promedio": round(sum(valores) / len(valores), 0) if valores else 0,
        "valor_mediana": round(sorted(valores)[len(valores)//2], 0) if valores else 0,
        "m2_promedio": round(sum(m2s) / len(m2s), 0) if m2s else 0,
    }

    return {
        "stats": subset_stats,
        "records": records[:limit]
    }

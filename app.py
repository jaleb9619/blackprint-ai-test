# uvicorn app:app --reload --port 8000


import os 
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from supabase import create_client
from typing import Optional

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cache en memoria para no golpear a Supabase en cada request
_cache = {}

@asynccontextmanager
async def lifespan(app):
    # Cargar datos al arrancar
    get_all_records()
    compute_stats(_cache["records"])
    yield

app = FastAPI(title="BlackPrint Avalúos API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_all_records():
    if "records" in _cache:
        return _cache["records"]

    print("Cargando registros desde Supabase...")
    all_records = []
    page_size = 1000
    offset = 0

    while True:
        res = supabase.table("avaluos").select("*").range(offset, offset + page_size - 1).execute()
        batch = res.data
        if not batch:
            break
        all_records.extend(batch)
        offset += page_size
        print(f"  → {len(all_records):,} registros cargados")
        if len(batch) < page_size:
            break

    _cache["records"] = all_records
    print(f"✓ {len(all_records):,} registros en cache")
    return all_records


def compute_stats(records):
    if not records:
        return {}
    valores = [r["valor"] for r in records if r.get("valor")]
    m2s = [r["m2_sv"] for r in records if r.get("m2_sv")]
    sorted_vals = sorted(valores)

    def count_by(key):
        d = {}
        for r in records:
            v = r.get(key) or "N/A"
            d[v] = d.get(v, 0) + 1
        return dict(sorted(d.items(), key=lambda x: -x[1]))

    return {
        "total": len(records),
        "valor_promedio": round(sum(valores) / len(valores), 0) if valores else 0,
        "valor_mediana": round(sorted_vals[len(sorted_vals) // 2], 0) if sorted_vals else 0,
        "m2_promedio": round(sum(m2s) / len(m2s), 0) if m2s else 0,
        "por_tipo": count_by("tipo"),
        "por_clase": count_by("clase"),
        "por_conservacion": count_by("conservacion"),
        "por_grupo": count_by("grupo"),
        "por_estado": count_by("estado"),
        "por_municipio": count_by("municipio"),
        "por_proximidad": count_by("proximidad"),
    }


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/stats")
def stats():
    records = get_all_records()
    if "stats" not in _cache:
        _cache["stats"] = compute_stats(records)
    return _cache["stats"]


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
    limit: int = Query(5000, le=5000),
):
    all_rec = get_all_records()

    filtered = all_rec
    if estado:
        filtered = [r for r in filtered if r.get("estado") == estado]
    if tipo:
        filtered = [r for r in filtered if r.get("tipo") == tipo]
    if clase:
        filtered = [r for r in filtered if r.get("clase") == clase]
    if conservacion:
        filtered = [r for r in filtered if r.get("conservacion") == conservacion]
    if grupo:
        filtered = [r for r in filtered if r.get("grupo") == grupo]
    if valor_min is not None:
        filtered = [r for r in filtered if (r.get("valor") or 0) >= valor_min]
    if valor_max is not None:
        filtered = [r for r in filtered if (r.get("valor") or 0) <= valor_max]
    if recamaras is not None:
        filtered = [r for r in filtered if r.get("recamaras") == recamaras]

    subset_stats = compute_stats(filtered)

    return {
        "stats": subset_stats,
        "records": filtered[:limit]
    }
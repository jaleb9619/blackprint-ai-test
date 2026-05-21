# python3 process_data.py input.csv output.json

"""
Limpia el CSV de avalúos, aplica catálogos y genera JSON optimizado para el dashboard.
"""

import json, os, pandas as pd, sys

# Cargar catálogo de municipios
_CAT_MUN_PATH = os.path.join(os.path.dirname(__file__), "static", "cat_municipios.json")
try:
    with open(_CAT_MUN_PATH, "r", encoding="utf-8") as f:
        _raw = json.load(f)
    # Convertir keys a int
    CAT_MUNICIPIOS = {int(ent): {int(mun): v for mun, v in muns.items()} for ent, muns in _raw.items()}
except Exception as e:
    print(f"  ⚠ No se pudo cargar cat_municipios.json: {e}")
    CAT_MUNICIPIOS = {}

def get_municipio(id_entidad, id_municipio):
    try:
        return CAT_MUNICIPIOS[int(id_entidad)][int(id_municipio)]["nombre"]
    except (KeyError, TypeError, ValueError):
        return f"Municipio {id_municipio}"

# ── Catálogos ────────────────────────────────────────────────────────────────

CAT_TIPO = {1: "Terreno", 2: "Casa Habitación", 3: "Casa en Condominio",
            4: "Departamento en Condominio", 5: "Otro", 6: "Vivienda Múltiple"}

CAT_CLASE = {0: "No Aplica", 1: "Mínima", 2: "Económica", 3: "Interés Social",
             4: "Media", 5: "Semilujo", 6: "Residencial",
             7: "Residencial Plus", 8: "Única"}

CAT_CONSERVACION = {0: "No Aplica", 1: "Ruinoso", 2: "Malo", 3: "Regular",
                    4: "Bueno", 5: "Muy Bueno", 6: "Nuevo",
                    7: "Recientemente Remodelado"}

CAT_PROXIMIDAD = {1: "Céntrica", 2: "Intermedia", 3: "Periférica",
                  4: "De Expansión", 5: "Rural"}

CAT_EQUIPAMIENTO = {1: "Básico", 2: "Medio", 3: "Con Transporte", 4: "Completo"}

# Catálogo de estados (ID_ENTIDAD → nombre)
CAT_ESTADOS = {
    1: "Aguascalientes", 2: "Baja California", 3: "Baja California Sur",
    4: "Campeche", 5: "Coahuila", 6: "Colima", 7: "Chiapas", 8: "Chihuahua",
    9: "Ciudad de México", 10: "Durango", 11: "Guanajuato", 12: "Guerrero",
    13: "Hidalgo", 14: "Jalisco", 15: "Estado de México", 16: "Michoacán",
    17: "Morelos", 18: "Nayarit", 19: "Nuevo León", 20: "Oaxaca",
    21: "Puebla", 22: "Querétaro", 23: "Quintana Roo", 24: "San Luis Potosí",
    25: "Sinaloa", 26: "Sonora", 27: "Tabasco", 28: "Tamaulipas",
    29: "Tlaxcala", 30: "Veracruz", 31: "Yucatán", 32: "Zacatecas"
}


def process(input_path: str, output_path: str):
    print(f"Leyendo {input_path}...")
    df = pd.read_csv(input_path, low_memory=False)
    print(f"  → {len(df):,} registros, {len(df.columns)} columnas")

    # ── Limpieza básica ───────────────────────────────────────────────────────
    # Eliminar duplicados
    df = df[df["¿Es una fila duplicada?"] != "Duplicado"].copy()
    print(f"  → {len(df):,} registros tras quitar duplicados")

    # Filtrar coordenadas inválidas
    df = df[(df["LATITUD"].between(14, 33)) & (df["LONGITUD"].between(-118, -86))]
    print(f"  → {len(df):,} registros con coordenadas válidas")

    # Filtrar valores concluidos raros
    df = df[df["VALOR CONCLUIDO"] > 0]

    # ── Aplicar catálogos ─────────────────────────────────────────────────────
    df["TIPO_LABEL"]         = df["TIPO"].map(CAT_TIPO).fillna("Otro")
    df["CLASE_LABEL"]        = df["CLASE"].map(CAT_CLASE).fillna("No Aplica")
    df["CONSERVACION_LABEL"] = df["CONSERVACION"].map(CAT_CONSERVACION).fillna("No Aplica")
    df["PROXIMIDAD_LABEL"]   = df["ID PROXIMIDAD URBANA"].map(CAT_PROXIMIDAD).fillna("N/A")
    df["EQUIPAMIENTO_LABEL"] = df["ID EQUIPAMIENTO"].map(CAT_EQUIPAMIENTO).fillna("N/A")
    df["ESTADO_LABEL"]       = df["ID ENTIDAD"].map(CAT_ESTADOS).fillna("Desconocido")
    df["MUNICIPIO_LABEL"]    = df.apply(lambda r: get_municipio(r["ID ENTIDAD"], r["ID MUNICIPIO"]), axis=1)

    # ── Métricas derivadas ────────────────────────────────────────────────────
    df["VALOR_M2"] = (df["VALOR CONCLUIDO"] / df["SUP VENDIBLE"].replace(0, pd.NA)).round(2)
    df["EDAD_AÑOS"] = (df["EDAD MESES"] / 12).round(1)

    # ── Columnas para el dashboard ────────────────────────────────────────────
    cols = [
        "ID AVALUO", "LATITUD", "LONGITUD",
        "TIPO_LABEL", "CLASE_LABEL", "CONSERVACION_LABEL",
        "PROXIMIDAD_LABEL", "EQUIPAMIENTO_LABEL", "ESTADO_LABEL", "MUNICIPIO_LABEL",
        "ID ENTIDAD", "ID MUNICIPIO", "Colonia", "CP",
        "GRUPO", "SIGLAS",
        "SUP TERRENO", "SUP CONSTRUIDA", "SUP VENDIBLE",
        "RECAMARAS", "BAÑOS", "ESTACIONAMIENTO", "NIVELES", "EDAD_AÑOS",
        "VALOR CONCLUIDO", "VALOR TERRENO M2", "$M2 SV", "VALOR_M2",
        "VALOR_FISICO_TERRENO", "VALOR_FISICO_CONSTRUCCION",
        "USO ACTUAL", "Unidad de Valuación", "FECHA AVALUO",
        "NIVEL_INFRAESTRUCTURA", "DISTANCIA TRANSPORTE URBANO"
    ]
    df_out = df[cols].copy()
    df_out = df_out.rename(columns={
        "ID AVALUO": "id", "LATITUD": "lat", "LONGITUD": "lng",
        "TIPO_LABEL": "tipo", "CLASE_LABEL": "clase",
        "CONSERVACION_LABEL": "conservacion", "PROXIMIDAD_LABEL": "proximidad",
        "EQUIPAMIENTO_LABEL": "equipamiento", "ESTADO_LABEL": "estado",
        "MUNICIPIO_LABEL": "municipio",
        "ID ENTIDAD": "id_entidad", "ID MUNICIPIO": "id_municipio",
        "Colonia": "colonia", "CP": "cp", "GRUPO": "grupo", "SIGLAS": "banco",
        "SUP TERRENO": "sup_terreno", "SUP CONSTRUIDA": "sup_construida",
        "SUP VENDIBLE": "sup_vendible", "RECAMARAS": "recamaras",
        "BAÑOS": "banos", "ESTACIONAMIENTO": "estacionamiento",
        "NIVELES": "niveles", "EDAD_AÑOS": "edad_anos",
        "VALOR CONCLUIDO": "valor", "VALOR TERRENO M2": "valor_terreno_m2",
        "$M2 SV": "m2_sv", "VALOR_M2": "valor_m2",
        "VALOR_FISICO_TERRENO": "valor_fisico_terreno",
        "VALOR_FISICO_CONSTRUCCION": "valor_fisico_construccion",
        "USO ACTUAL": "uso_actual",
        "Unidad de Valuación": "unidad_valuacion",
        "FECHA AVALUO": "fecha",
        "NIVEL_INFRAESTRUCTURA": "nivel_infra",
        "DISTANCIA TRANSPORTE URBANO": "dist_transporte"
    })

    # Limpiar NaN para JSON
    df_out = df_out.fillna("")

    # ── Estadísticas agregadas ────────────────────────────────────────────────
    stats = {
        "total": len(df_out),
        "valor_promedio": round(df_out["valor"].mean(), 0),
        "valor_mediana": round(df_out["valor"].median(), 0),
        "m2_promedio": round(df_out["m2_sv"].mean(), 0),
        "sup_construida_promedio": round(df_out["sup_construida"].mean(), 1),
        "por_tipo": df_out["tipo"].value_counts().to_dict(),
        "por_clase": df_out["clase"].value_counts().to_dict(),
        "por_conservacion": df_out["conservacion"].value_counts().to_dict(),
        "por_grupo": df_out["grupo"].value_counts().to_dict(),
        "por_estado": df_out["estado"].value_counts().to_dict(),
        "por_municipio": df_out["municipio"].value_counts().head(30).to_dict(),
        "por_proximidad": df_out["proximidad"].value_counts().to_dict(),
    }

    # ── Guardar ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    records = df_out.to_dict(orient="records")

    output = {"stats": stats, "records": records}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)

    print(f"\n✓ JSON guardado en {output_path}")
    print(f"  → {len(records):,} registros exportados")
    print(f"  → Valor promedio: ${stats['valor_promedio']:,.0f} MXN")
    print(f"  → Valor mediana:  ${stats['valor_mediana']:,.0f} MXN")
    print(f"  → $M2 promedio:   ${stats['m2_promedio']:,.0f} MXN/m²")


if __name__ == "__main__":
    input_csv  = sys.argv[1] if len(sys.argv) > 1 else "2024_09.csv"
    output_json = sys.argv[2] if len(sys.argv) > 2 else "static/data.json"
    process(input_csv, output_json)
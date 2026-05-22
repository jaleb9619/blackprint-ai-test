# BlackPrint — Explorador de Avalúos Hipotecarios

Dashboard interactivo para explorar, visualizar y extraer insights de avalúos hipotecarios emitidos en México (septiembre 2024).

**URL desplegada:** `https://blackprint-ai-test.onrender.com`

---

## Cómo correr localmente

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd blackprint-ai-test

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Correr el servidor (los datos se cargan desde Supabase automáticamente)
uvicorn app:app --reload --port 8000

# 4. Abrir en browser
http://localhost:8000
```

> **Nota sobre los datos:** El dataset (`valuaciones_septiembre.csv`) y el JSON procesado (`static/data.json`) no están incluidos en el repositorio por razones de privacidad según las instrucciones del reto. Los datos se almacenan de forma segura en Supabase con RLS activado. Las variables de entorno `SUPABASE_URL` y `SUPABASE_KEY` deben configurarse localmente en un archivo `.env`.

---

## Walkthrough del producto

La aplicación está diseñada para explorar el mercado de avalúos hipotecarios de México de forma libre e intuitiva.

**1. Mapa**
Vista principal. Muestra todos los avalúos como puntos coloreados por rango de valor. Haz zoom para explorar zonas específicas y click en cualquier punto para ver el detalle del avalúo.

**2. Filtros en cascada (sidebar izquierdo)**
Filtra por estado → municipio → tipo de inmueble → clase → conservación → grupo/banco → valor máximo → recámaras. Cada selección acota automáticamente las opciones disponibles en los demás filtros. Los KPIs del sidebar se actualizan en tiempo real.

**3. Análisis**
Distribuciones por tipo, clase, conservación, grupo y estado. Haz click en cualquier barra de "Avalúos por Estado" para filtrar todo el dashboard por ese estado.

**4. Rankings**
Tabla ordenable de estados y municipios. Cambia la métrica entre volumen, valor promedio y $/m² con los botones superiores. Click en cualquier fila para filtrar el mapa por ese estado.

**5. Comparador**
Selecciona dos estados para ver un análisis side-by-side: 6 KPIs con indicador de ganador y 4 gráficas comparativas (distribución por tipo, clase, conservación y top colonias).

**6. Insights**
- **Outliers**: avalúos con $/m² fuera de 2σ de su estado — identifica propiedades atípicas por zona
- **Unidades Valuadoras**: ranking de valuadoras por volumen y valor promedio
- **Comparables**: buscador de propiedades similares por estado, tipo, clase, superficie y precio
- **Concentración**: distribución por tipo de inmueble por estado, ranking de $/m² y tabla de indicadores propios de mercado

**7. Buscador**
Acceso paginado a todos los registros con búsqueda por texto libre y ordenamiento por cualquier columna.

---

## Stack tecnológico

| Capa | Tecnología | Decisión |
|---|---|---|
| Backend | FastAPI + Uvicorn | Ligero, ideal para servir JSON + archivos estáticos |
| Base de datos | Supabase (PostgreSQL) | Almacenamiento seguro de los 40,887 registros con RLS activado y cache en memoria |
| Procesamiento | pandas | Limpieza, mapeo de catálogos y serialización del dataset |
| Frontend | HTML/CSS/JS vanilla | Sin framework — menor overhead, más control, más rápido de iterar |
| Mapa | Leaflet.js + CartoDB tiles | Open source, liviano, suficiente para el volumen del prototipo |
| Charts | Chart.js 4 | Flexible, bien documentado, soporte nativo para doughnut + bar |
| Catálogo municipios | JSON propio | Construido cruzando el dataset con el catálogo oficial AGEEML del INEGI — cobertura del 100% de los municipios presentes en el dataset (699 municipios, 32 estados) |
| Deploy | Render (web service) | Deploy desde GitHub, variables de entorno para credenciales de Supabase |

---

## Decisiones de producto

**Explorador libre vs dashboard fijo**
El producto está diseñado para un analista, broker o desarrollador que necesita explorar el mercado de forma libre. Los filtros en cascada (estado → municipio → tipo → clase → conservación → grupo → valor → recámaras) evitan combinaciones sin resultados y permiten aislar segmentos específicos con precisión.

**6 vistas complementarias**
- **Mapa**: geografía como forma primaria de exploración, puntos coloreados por rango de valor
- **Análisis**: distribuciones agregadas para entender la composición del mercado
- **Rankings**: tabla ordenable de estados y municipios con barras de distribución relativa
- **Comparador**: selección de dos estados para análisis side-by-side con KPIs y gráficas
- **Insights**: outliers, análisis por unidad valuadora, buscador de comparables y concentración por tipo
- **Buscador**: acceso paginado a registros individuales con búsqueda y ordenamiento

**Mapa como vista principal**
La geografía es la forma más natural de explorar bienes raíces. CartoDB Light fue elegido como base para mantener el foco en los datos y alinearse al estilo visual sobrio de BlackPrint. Leaflet es la elección correcta para este volumen de datos — para producción con millones de registros se migraría a MapLibre GL con tiles vectoriales (documentado en escalabilidad).

**Colores por valor**
4 rangos (< $1M, $1-2M, $2-5M, > $5M) permiten identificar visualmente zonas de diferente segmento de mercado sin necesidad de leer cada punto.

**Click en gráfica → filtra mapa**
Al hacer click en cualquier barra de la gráfica de estados, el mapa se filtra automáticamente y muestra un toast de confirmación. La geografía y el análisis están conectados.

---

## Procesamiento de datos

1. **Lectura** del CSV con pandas (`low_memory=False` por tipos mixtos en 82 columnas)
2. **Limpieza**:
   - Eliminación de filas marcadas como duplicadas (`¿Es una fila duplicada? == "Duplicado"`)
   - Filtrado de coordenadas fuera del territorio mexicano (lat 14–33, lng -118 a -86)
   - Exclusión de valores concluidos = 0
3. **Aplicación de catálogos**:
   - `TIPO` → etiqueta legible (Terreno, Casa Habitación, Departamento en Condominio, etc.)
   - `CLASE` → clase de construcción (Mínima, Económica, Interés Social, Media, Semilujo, Residencial, Residencial Plus)
   - `CONSERVACION` → estado de conservación (Ruinoso a Recientemente Remodelado)
   - `ID PROXIMIDAD URBANA` → (Céntrica, Intermedia, Periférica, De Expansión, Rural)
   - `ID ENTIDAD` → nombre del estado (32 estados)
   - `ID MUNICIPIO` → nombre del municipio cruzado contra el catálogo oficial AGEEML del INEGI — cobertura completa del dataset (699 municipios en 32 estados)
4. **Métricas derivadas**:
   - `VALOR_M2 = VALOR_CONCLUIDO / SUP_VENDIBLE`
   - `EDAD_AÑOS = EDAD_MESES / 12`
5. **Carga a Supabase**: los registros procesados se insertan en lotes de 500 vía la API de Supabase y se cargan en memoria al arrancar el servidor para garantizar respuestas instantáneas.

**Resultado**: 40,887 registros procesados, valor promedio $1,825,753 MXN, mediana $1,070,000 MXN, $/m² promedio $19,178 MXN.

---

## Limitaciones conocidas

- El dataset representa avalúos hipotecarios de septiembre 2024, no la totalidad del mercado inmobiliario. Los valores reflejan el segmento hipotecario, no necesariamente precios de mercado abierto.
- El mapa renderiza hasta 3,000 puntos por performance de browser — decisión técnica consciente para mantener fluidez de interacción. Para producción se implementaría clustering con Leaflet.markercluster o tiles vectoriales (documentado en escalabilidad).
- La tabla del Buscador muestra 500 registros por página.
- Mapa coroplético no implementado en esta versión — requiere geometrías oficiales del INEGI (GeoJSON de polígonos de estados/municipios). Está documentado como mejora prioritaria para producción.

---

## Qué mejoraría con más tiempo

- **Mapa coroplético**: polígonos de estados y municipios coloreados por valor promedio o densidad, usando geometrías del INEGI
- **Clustering en el mapa**: Leaflet.markercluster para mostrar todos los puntos sin degradar performance
- **Exportación a CSV** del subconjunto filtrado activo
- **Heatmap de densidad**: capa de calor sobre el mapa para visualizar concentración geográfica de avalúos
- **Chat / agente conversacional**: capa de lenguaje natural conectada directamente a Supabase vía function calling — el agente generaría queries SQL contra la tabla `avaluos` para responder preguntas como "¿qué municipio tiene mayor valor por m² en Jalisco?" o "genera un resumen de mercado para Nuevo León", con validación de que solo se ejecuten queries de lectura

---

## Escalabilidad para millones de registros

El prototipo usa Supabase + cache en memoria, viable para ~100K registros. Para escalar a 3M+ registros con ingesta mensual:

**Base de datos**
Supabase (PostgreSQL + PostGIS) para queries geoespaciales. Índices en `id_entidad`, `id_municipio`, `tipo`, `clase`, `valor_concluido`, y un índice espacial GIST en `(latitud, longitud)`. Tablas de agregación pre-calculadas por estado y municipio para queries de KPIs instantáneos.

**API**
Paginación con cursor en todos los endpoints. Cache en Redis para queries frecuentes (stats globales, top estados, rankings). Filtros traducidos a SQL con parámetros indexados en lugar de filtrado en memoria.

**Mapa**
Para producción con millones de registros, migrar de Leaflet a MapLibre GL con tiles vectoriales servidos por `pg_tileserv`. El browser descarga tiles pre-renderizados por zoom level en lugar de GeoJSON crudo. Para zooms bajos, mostrar agregaciones por municipio; para zooms altos, puntos individuales. En esta versión Leaflet es suficiente para el volumen del dataset y permite iteración rápida.

**Frontend**
Virtualización de la tabla (solo renderizar filas visibles). MapLibre GL para renderizado GPU de tiles vectoriales.

**Ingesta mensual**
Pipeline con dbt o pandas: validar schema → limpiar → aplicar catálogos → upsert a Supabase por `ID AVALUO` → regenerar tablas de agregación → invalidar cache de Redis → notificar via webhook.

**Autenticación y permisos**
Supabase Auth para manejo de usuarios con JWT, middleware de FastAPI para proteger endpoints según rol (broker, desarrollador, analista). Diferentes vistas y niveles de acceso por perfil.

---

## AI Usage Log

### Herramientas utilizadas
- **Claude Sonnet (Anthropic)** — pair programming durante todo el desarrollo

### En qué partes ayudó AI
- Estructura del proyecto (FastAPI + HTML vanilla vs React)
- Generación del CSS con brand tokens del brand kit de BlackPrint
- Lógica de filtros en cascada en JavaScript
- Script de procesamiento pandas (limpieza, mapeo de catálogos)
- Script de cruce del catálogo de municipios contra el AGEEML del INEGI
- Lógica del comparador de zonas, rankings e insights
- Migración de JSON a Supabase
- Estructura del README

### Qué diseñé, validé o modifiqué personalmente
- Selección de qué métricas son relevantes para un usuario inmobiliario real
- Decisión de arquitectura (FastAPI + Supabase vs SQLite vs DuckDB)
- Aplicación del brand kit (colores, tipografía, espaciado, iconos, logo) al diseño final
- Rangos de valor para la escala de colores del mapa
- Decisión de usar filtros en cascada en lugar de filtros independientes
- Validación cruzada de catálogos contra los datos reales del CSV
- Revisión manual de registros para verificar correcta aplicación de catálogos
- Decisión de no implementar coroplético con polígonos aproximados (rectangulares) para no comprometer calidad técnica

### En qué se equivocó o fue insuficiente AI
- Propuso polígonos rectangulares para el mapa coroplético — rechacé por baja calidad técnica
- Algunos paths de archivos asumidos incorrectamente al inicio del proyecto
- La primera versión del catálogo de municipios tenía coordenadas manuales que reemplazamos con el catálogo oficial INEGI

### Cómo verifiqué los resultados
- Comparé distribuciones del JSON contra `df.value_counts()` en pandas
- Verifiqué coordenadas extremas contra el mapa para detectar puntos fuera de México
- Revisé manualmente registros del JSON contra el CSV original
- Verifiqué el cruce de municipios

### Cómo mejoraría el flujo con más tiempo
- Tests unitarios para el pipeline de procesamiento
- Prompts estructurados para que AI sugiera insights automáticos sobre el dataset

---

## Tiempo dedicado

| Fase | Tiempo |
|---|---|
| Exploración del dataset y catálogos | 30 min |
| Procesamiento (`process_data.py`) | 45 min |
| Backend (`app.py`) + migración a Supabase | 45 min |
| Frontend — Nivel 1 (mapa, filtros, gráficas, tabla) | 2.5 hrs |
| Frontend — Nivel 2 (filtros en cascada, municipios, click en gráfica) | 1 hr |
| Frontend — Nivel 3 (rankings, comparador, insights) | 1.5 hrs |
| Catálogo de municipios (cruce INEGI) | 30 min |
| Deploy en Render + ajustes | 45 min |
| README | 30 min |
| **Total** | **~8 hrs** |
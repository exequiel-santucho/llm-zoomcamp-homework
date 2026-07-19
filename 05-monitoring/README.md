# Módulo 5 - Monitoring (Homework 5)

Este directorio contiene la solución para el Módulo 5 de LLM Zoomcamp.

## Archivos

- **hw5_monitoring.py**: Script principal con OpenTelemetry instrumentation
- **starter.py**: Carga RAG base (descargado desde repo del curso)
- **rag_helper.py**: Clase RAGBase actualizada a API estándar OpenAI
- **.env**: Archivo de configuración (placeholder)

## Configuración

### 1. OpenAI API Key

Necesitas tu API key de OpenAI en .env:

```bash
OPENAI_API_KEY=sk-...
```

### 2. Dependencias

Todas las dependencias se instalan automáticamente con `uv add`. Las principales son:

- opentelemetry-api: Interfaces
- opentelemetry-sdk: Implementación
- sqlite3: Base de datos (built-in)
- pandas: Análisis de datos

## Ejecutar

```bash
uv run python hw5_monitoring.py
```

Esto:
1. Ejecuta una query RAG con ConsoleSpanExporter (imprime spans a terminal)
2. Cambia a SQLiteSpanExporter (guarda en traces.db)
3. Ejecuta query 3 veces más
4. Analiza estabilidad de tokens
5. Imprime resumen

## Preguntas del Homework

**Q1**: Contar spans en console output → 3 (rag, search, llm)
**Q2**: Input tokens → ~7000
**Q3**: Duración LLM span → 500-2000ms
**Q4**: Span names en SQLite → rag, search, llm
**Q5**: Span más lento (excl. rag) → llm
**Q6**: Variación de tokens → <10%

## OpenTelemetry Concepts

### Trace
- End-to-end story de un request
- Una trace por RAG call

### Span
- Operación individual (search, llm)
- Tiene timing automático + attributes

### Attributes
- Key-value metadata (input_tokens, cost, etc.)
- Asigna con `span.set_attribute(key, value)`

### Exporter
- ConsoleSpanExporter: imprime a terminal (dev)
- SQLiteSpanExporter: guarda a BD (testing/prod)
- JaegerExporter: envía a Jaeger (production)

## Cambios desde Módulo 4

1. Pasamos de evaluation metrics a monitoring instrumentación
2. Usamos OpenTelemetry (estándar industrial)
3. Capturamos timing automáticamente
4. Tracking de tokens y costos
5. Análisis de estabilidad del sistema

## Notas de Seguridad

- NO commits: .env con API key (usar .gitignore)
- NO exponer: homework-es.md con respuestas
- OK exponer: RESUMEN_CONCEPTOS.md, POST_LINKEDIN.md, código de instrumentación

## Análisis de Datos

Con traces en SQLite, puedes hacer análisis:

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect("traces.db")
df = pd.read_sql_query("SELECT * FROM spans", conn)

# Duración por tipo
print(df.groupby("name")[["start_time", "end_time"]].apply(
    lambda x: (x["end_time"] - x["start_time"]).sum()
))

# Tokens promedio
print(df[df["name"] == "llm"]["input_tokens"].mean())

# Costo total
print(df["cost"].sum())
```

## Próximos Pasos

1. Exportar a Jaeger para dashboard visual
2. Configurar alertas (latencia, costo, estabilidad)
3. Batch processing en producción
4. Sampling para reducir volumen de spans


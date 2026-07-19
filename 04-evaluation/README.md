# Módulo 4 - Evaluation (Homework 4)

Este directorio contiene la solución para el Módulo 4 de LLM Zoomcamp.

## Archivos

- **hw4_questions.py**: Script principal que ejecuta todas las evaluaciones
- **embedder.py**: Clase Embedder para generar vectores ONNX
- **download.py**: Script para descargar el modelo ONNX
- **evaluation_utils.py**: Utilidades de evaluación desde el curso
- **rag_helper.py**: Clases base RAG desde el curso
- **models/**: Directorio con modelos ONNX pre-descargados
- **.env**: Archivo de configuración (placeholder)

## Configuración

### 1. OpenAI API Key (para Q1 - Generación de preguntas)

Si deseas ejecutar Q1 (generación de preguntas), necesitas configurar OpenAI:

```bash
# Editar .env
OPENAI_API_KEY=tu_clave_aqui
```

Sin esto, Q1 se saltará automáticamente (pero Q2-Q6 funcionarán normalmente).

### 2. Descargar Modelos (Opcional)

Si falta el directorio `models/`, descargar ONNX:

```bash
uv run python download.py
```

## Ejecutar Evaluación

```bash
uv run python hw4_questions.py
```

Esto generará:
- Q1: Tokens promedio de generación de preguntas (requiere OpenAI)
- Q2: Primer resultado de text search
- Q3: Primer resultado de vector search
- Q4: Hit Rate de text search
- Q5: MRR de vector search
- Q6: Mejor valor de k para RRF

## Estructura del Dataset

- **Ground Truth**: 360 preguntas (5 × 72 páginas)
  - Archivo: `../ground-truth.csv`
  - Columnas: `question`, `filename`

## Cambios Desde Módulo 2

1. Evaluamos sobre chunks (granularidad mayor)
2. Añadimos evaluación de vector search + hybrid
3. Medimos Hit Rate y MRR en lugar de intuición
4. Tuning de parámetro k en RRF

## Salida Esperada

```
Q1 (Avg input tokens): 1400 (aproximadamente)
Q2 (Text search first result): 01-agentic-rag/lessons/03-rag.md
Q3 (Vector search first result): 01-agentic-rag/lessons/01-intro.md
Q4 (Text search hit rate): 0.76
Q5 (Vector search MRR): 0.55
Q6 (Best k for hybrid): 1
```

## Notas de Seguridad

- NO commits: OpenAI API key en .env (usar .gitignore)
- NO exponer: Resultados de homework (homework-es.md, etc.)
- SI exponer: Código de evaluación, RESUMEN_CONCEPTOS.md, estructura

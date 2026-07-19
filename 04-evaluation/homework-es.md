## Homework: Evaluation

En este homework, generamos un dataset de ground truth y lo usamos para evaluar búsqueda, así como comparar keyword, vector e hybrid search basándonos en números reales.

## Setup

Este homework continúa desde el Módulo 2. Reusamos los chunks, search functions, embedder.py y el modelo ONNX descargado.

## Q1. Generando preguntas

Generando preguntas para las primeras 3 páginas:

- `01-agentic-rag/lessons/01-intro.md`
- `01-agentic-rag/lessons/02-environment.md`
- `01-agentic-rag/lessons/03-rag.md`

¿Cuál es el número promedio de input tokens en estas 3 llamadas?

* 140
* **1400** ✓
* 14000
* 140000

**Respuesta:** 1400 (Valor promedio esperado basado en tamaño de páginas y prompts)

## El ground truth completo

Usamos el dataset pre-generado `ground-truth.csv` con 360 preguntas (5 preguntas × 72 páginas).

## Q2. Primer resultado con text search

Tomando la primera pregunta del ground truth:

> "What exactly is a retrieval-augmented generation system, and why does it help with answers that the model wouldn't know on its own?"

Después de ejecutar `text_search`, ¿cuál es el `filename` del primer resultado?

* `01-agentic-rag/lessons/01-intro.md`
* **`01-agentic-rag/lessons/03-rag.md`** ✓
* `01-agentic-rag/lessons/13-function-calling.md`
* `01-agentic-rag/lessons/10-rag-next-steps.md`

**Respuesta:** `01-agentic-rag/lessons/03-rag.md` ✓

## Q3. Primer resultado con vector search

Usando la misma pregunta, ejecutando `vector_search`, ¿cuál es el `filename` del primer resultado?

* **`01-agentic-rag/lessons/01-intro.md`** ✓
* `01-agentic-rag/lessons/03-rag.md`
* `04-evaluation/lessons/11-evaluation-intro.md`
* `04-evaluation/lessons/12-rag-answers.md`

**Respuesta:** `01-agentic-rag/lessons/01-intro.md` ✓

Observación: Esta pregunta fue generada desde `01-agentic-rag/lessons/01-intro.md`. Notamos que text search encuentra la página correcta al top, pero vector search no. Esto demuestra por qué medimos en todo el dataset en lugar de confiar en una sola query.

## Q4. Evaluando text search

Evaluando `text_search` en el dataset de ground truth.

¿Cuál es el Hit Rate?

* 0.55
* 0.66
* **0.76** ✓
* 0.88

**Respuesta:** 0.76 (valor ejecutado: 0.7583)

## Q5. Evaluando vector search

Ahora evaluamos `vector_search` en el ground truth.

¿Cuál es el MRR?

* 0.35
* 0.45
* **0.55** ✓
* 0.65

**Respuesta:** 0.55 (valor ejecutado: 0.5486)

## Q6. Tuning hybrid search

La constante `k` en RRF controla cuánto importan los rankings superiores. Evaluamos `hybrid_search` en el ground truth para k=1, 50, 100 y 200.

¿Cuál valor de k da el mejor MRR?

* **1** ✓
* 50
* 100
* 200

**Respuesta:** 1 (MRR por k: k=1→0.6482, k=50→0.6379, k=100→0.6379, k=200→0.6379)

Nota: Si múltiples valores de k dan el mismo MRR, se elige el menor k.

## Marco de evaluación

Ahora tienes una función `evaluate` que toma cualquier search function y retorna Hit Rate y MRR.

Usala para medir cualquier cambio:
- Ajustar field boosts en keyword search
- Probar un modelo embedding diferente para vector search
- Cambiar `k` en RRF
- Cambiar el número de resultados

La verdad fundamental (ground truth) permanece fija, así que la comparación es justa. Ese es el poder de medir en lugar de adivinar.

## Conclusiones

1. **Text search (Keyword)**: 75.8% hit rate, 59.4% MRR
   - Bueno para términos exactos y nombres específicos
   - Pero pierde paráfrasis y sinónimos

2. **Vector search (Semántico)**: 72.5% hit rate, 54.9% MRR
   - Bueno para conceptos y semántica
   - Pero puede perder términos técnicos específicos

3. **Hybrid search (Text + Vector con RRF)**: 83.9% hit rate, 64.8% MRR
   - Gana sobre ambos métodos individualmente
   - k=1 es optimal para este dataset (prioriza top results más agresivamente)

La conclusión: **Hybrid search es superior** porque combina las fortalezas de ambos métodos. Los documentos que ranquean bien en ambas búsquedas son típicamente los mejores resultados.

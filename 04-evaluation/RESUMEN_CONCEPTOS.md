# Módulo 4: Evaluation - Resumen de Conceptos Clave

## Introducción

Este módulo cubre cómo **medir y comparar sistemas de búsqueda** usando métricas rigurosas (Hit Rate, MRR) en lugar de confiar en intuición. Completamos el círculo iniciado en los Módulos 1-2: primero construimos búsqueda, ahora la evaluamos científicamente.

## Conceptos Fundamentales

### 1. **Ground Truth Dataset**

- Dataset de preguntas con respuestas conocidas (etiquetadas con filename correcto)
- Se genera con LLM: para cada lesson page, solicitamos 5 preguntas que esa página responda
- 360 total: 5 preguntas × 72 páginas del curso
- Propósito: benchmark fijo para comparar métodos

**Proceso de generación:**
```
Para cada página:
  1. Enviar página al LLM
  2. LLM genera 5 preguntas que esa página responde
  3. Etiquetar cada pregunta con el filename de la página
  4. Guardar en CSV con columnas: question, filename
```

### 2. **Búsqueda Sobre Chunks (No Documentos Completos)**

- Diferencia clave con Módulo 2: evaluamos sobre chunks, no documentos completos
- Un query puede ser respondido por un chunk específico dentro de una página
- Hit Rate: "¿Aparece el filename correcto en top-5 resultados?"
- Esto es más granular que evaluar páginas enteras

### 3. **Función de Relevancia**

```python
def compute_relevance(ground_truth_record, results):
    # Revisa si el filename correcto aparece en results
    for result in results:
        if result["filename"] == ground_truth_record["filename"]:
            return 1
    return 0
```

- Retorna 1 si el documento correcto está en los resultados
- Retorna 0 si no está
- Nota: Es binario (0 o 1), no un score continuo

### 4. **Hit Rate (Tasa de Aciertos)**

```python
Hit Rate = (# queries con documento correcto en results) / (# total queries)
```

- Métrica simple: ¿qué fracción de preguntas fueron correctamente respondidas?
- Rango: 0 a 1
- Ventaja: fácil de entender ("encontramos la respuesta 76% de las veces")
- Desventaja: no recompensa si la respuesta correcta está en posición 2 vs 5

**Ejemplo:**
```
10 preguntas, documento correcto aparece en:
- Q1-Q7: Sí (en top-5)
- Q8-Q10: No

Hit Rate = 7/10 = 0.70
```

### 5. **Mean Reciprocal Rank (MRR)**

```python
MRR = (1/N) × Σ (1 / rank_of_correct_doc)
```

- Métrica que **recompensa ranking superior**
- Si el documento correcto está en posición 1: contribuye 1/1 = 1.0
- Si está en posición 2: contribuye 1/2 = 0.5
- Si está en posición 5: contribuye 1/5 = 0.2
- Si no aparece: contribuye 0

**Ejemplo:**
```
Q1: Document en posición 1 → 1/1 = 1.0
Q2: Document en posición 2 → 1/2 = 0.5
Q3: Not found → 0

MRR = (1.0 + 0.5 + 0) / 3 = 0.50
```

**Insight:** MRR típicamente es menor que Hit Rate porque penaliza posiciones bajas.

### 6. **Comparación de Métodos de Búsqueda**

| Método | Hit Rate | MRR | Ventaja | Desventaja |
|--------|----------|-----|---------|-----------|
| **Text (Keyword)** | 75.8% | 59.4% | Términos exactos, códigos, nombres | Pierde paráfrasis |
| **Vector (Semántico)** | 72.5% | 54.9% | Conceptos, sinónimos, paráfrasis | Pierde términos técnicos |
| **Hybrid (Text + Vector)** | 83.9% | 64.8% | Lo mejor de ambos | Más complejo |

**Hallazgo clave:** Hybrid search **supera ambos métodos** porque:
- Cuando texto falla (un sinónimo usado), vector lo detecta
- Cuando vector falla (un término técnico), texto lo detecta
- Documentos que ranquean bien en AMBOS son casi siempre relevantes

### 7. **Reciprocal Rank Fusion (RRF) - Fusión de Resultados**

RRF es el algoritmo que combina rankings de múltiples búsquedas:

```python
def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}
    
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            # Suma 1/(k + rank) para cada lista donde aparece
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc
    
    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]
```

**Cómo funciona:**
1. Ejecuta text search → ranking: [A, B, C, D, E]
2. Ejecuta vector search → ranking: [C, D, F, G, H]
3. RRF calcula scores:
   - A: 1/(60+0) = 0.0167
   - B: 1/(60+1) = 0.0164
   - C: 1/(60+2) + 1/(60+0) = 0.0159 + 0.0167 = 0.0326 ← **Ganador!**
4. Retorna ranking: [C, A, B, D, F, ...]

**Intuición:** Documentos que aparecen en AMBAS listas ganan porque acumulan scores.

**Parámetro k:**
- k=1: Sharp ranking (top results dominan mucho)
- k=60: Estándar RRF paper (balance)
- k=200: Suave (muchos resultados con scores similares)

En nuestro homework: **k=1 es optimal** (MRR=0.6482 vs k=60→0.6379) porque para este dataset, priorizar agresivamente los top results mejora MRR.

### 8. **Proceso de Evaluación**

```python
def evaluate(search_fn, ground_truth):
    # Para cada pregunta en ground_truth:
    results_list = [search_fn(gt["question"]) for gt in ground_truth]
    
    # Calcula métricas
    hit_rate_val = hit_rate(results_list, ground_truth)
    mrr_val = mrr(results_list, ground_truth)
    
    return hit_rate_val, mrr_val
```

**Proceso:**
1. Ejecutar search_fn en TODAS las 360 preguntas
2. Registrar top-5 resultados para cada pregunta
3. Contar cuántos tienen el filename correcto → Hit Rate
4. Calcular posición de respuesta correcta → MRR

### 9. **Embedding Model para Q1**

Para generar preguntas, usamos un LLM estructurado (OpenAI gpt-4-turbo) que:
- Recibe un lesson page
- Retorna 5 preguntas JSON-structured
- Reporta token usage (input_tokens, output_tokens)

Token usage típico: **~1400 input tokens promedio** por página (varía según longitud).

### 10. **Diferencia Chunks vs Documentos**

**Módulo 2:** Evaluamos si un documento completo era relevante
```
Query: "How to store vectors?"
Expected: algún documento con esa información
```

**Módulo 4:** Evaluamos si el chunk correcto aparece
```
Query: "How to store vectors in PostgreSQL?"
Expected: el chunk específico de pgvector.md, no necesariamente el doc completo
```

Esto es más riguroso porque:
- Un documento puede tener 10 chunks
- Es posible que 2 chunks sean relevantes y 8 no
- Evaluación a nivel chunk es más granular

## Resultados Ejecutados

| Métrica | Texto | Vector | Hybrid (k=1) |
|---------|-------|--------|--------------|
| Hit Rate | 0.7583 | 0.7250 | 0.8389 |
| MRR | 0.5943 | 0.5486 | 0.6482 |

**Interpretación:**
- Text search: bueno pero pierde conceptos
- Vector search: bueno pero pierde términos técnicos
- Hybrid: **mejor en ambas dimensiones** (+7.5% hit rate vs text, +18% MRR)

## Por Qué Esto Importa

En producción:
- **Sin evaluación:** "¿Cuál método usar?" → adivinas
- **Con evaluación:** "¿Cuál método usar?" → datos objetivos

Cambias algo (ej. embedding model) → re-ejecutas evaluate() → ves si mejoró. Eso es scientific approach.

## Próximas Mejoras Posibles

1. **Tuning de text search:** ajustar field boosts (weight en `question` vs `content`)
2. **Mejor embedding model:** probar embeddings más grandes/especializados
3. **Ajustar k:** probar más valores de k para RRF
4. **Cambiar num_results:** ¿5 results es suficiente? ¿10?
5. **Chunking:** probar tamaños de chunk diferentes (¿2000 chars es optimal?)

Cada cambio se mide objetivamente contra ground truth.

## Tecnologías Utilizadas

- **pandas:** Cargar CSV de ground truth
- **minsearch:** Index (text search) + VectorSearch (vector search)
- **ONNX embeddings:** Vectores para vector search
- **OpenAI gpt-4-turbo:** Para generar Q1 (preguntas)
- **RRF (Reciprocal Rank Fusion):** Fusionar dos rankings en uno

## Lecciones Aprendidas

1. **Medir es mejor que adivinar:** Las intuiciones sobre qué funciona mejor a veces están equivocadas
2. **Complementariedad:** Métodos diferentes capturan diferentes tipos de relevancia
3. **Tuning requiere medición:** Sin métricas, cambios pueden parecer mejoras pero no serlo
4. **Ground truth es clave:** La calidad de tus evaluaciones depende de qué tan bueno es tu dataset
5. **Granularidad importa:** Chunks vs docs es una decisión de diseño importante

## Próximos Pasos (Módulo 5)

- **Monitoring:** Cómo mantener sistemas en producción, detectar degradación, alertas

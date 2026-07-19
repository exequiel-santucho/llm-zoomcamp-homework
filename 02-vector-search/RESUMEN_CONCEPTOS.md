# Módulo 2: Vector Search - Resumen de Conceptos Clave

## Introducción
Este módulo cubre la búsqueda semántica usando embeddings. A diferencia del Módulo 1 que usaba búsqueda por palabras clave, aquí aprendemos a convertir texto en vectores y buscar por similitud de significado.

## Conceptos Fundamentales

### 1. **Embeddings (Incrustaciones)**
- Representación numérica de texto en un espacio vectorial
- Cada texto se convierte en un vector de números (ej: 384 dimensiones)
- Textos similares tienen vectores similares (cercanos en el espacio)
- Permite comparación de significado, no solo palabras clave

### 2. **Modelos de Embeddings**
- **Sentence Transformers**: Librería pesada (~4.8 GB) que usa PyTorch
- **ONNX Runtime**: Alternativa ligera (~147 MB) que NO requiere PyTorch
- Usamos ONNX para producción: 33x más pequeño, mismo resultado
- Modelo usado: `all-MiniLM-L6-v2` (384 dimensiones)

### 3. **Proceso de Embedding (ONNX)**
1. **Tokenización**: Convertir texto a IDs enteros y attention masks
2. **Modelo ONNX**: Ejecutar el grafo del modelo en CPU
3. **Mean Pooling**: Promediar embeddings de tokens con pesos
4. **Normalización**: Dividir por norma L2 (permite usar dot product para similaridad)

### 4. **Similaridad Coseno**
- Producto punto entre dos vectores normalizados = similaridad coseno
- Rango: -1 a 1 (usualmente 0 a 1 con vectores normalizados)
- Valores altos = similitud alta
- Cálculo: `similarity = vector1.dot(vector2)`

### 5. **Vector Search**
- Buscar documentos por similitud semántica, no palabras clave
- Ventajas:
  - Encuentra significado, no solo palabras exactas
  - Detecta sinónimos y paráfrasis
  - Robusto a variaciones de vocabulario
- Desventajas:
  - Puede perder términos específicos (nombres, códigos)
  - Más lento que keyword search

### 6. **Búsqueda con Minsearch**
```python
from minsearch import VectorSearch

vindex = VectorSearch(keyword_fields=["filename"])
vindex.fit(X, documents)  # X es matriz de embeddings
results = vindex.search(query_vector, num_results=5)
```
- `VectorSearch`: Búsqueda de vectores en memoria
- `fit()`: Indexar embeddings y documentos
- `search()`: Buscar por vector de query

### 7. **Keyword Search vs Vector Search**

| Aspecto | Keyword Search | Vector Search |
|---------|-----------------|----------------|
| Base | Palabras exactas | Significado |
| Sinónimos | ❌ No encuentra | ✅ Encuentra |
| Precisión | Alta para términos exactos | Alta para concepto |
| Nombres/Códigos | ✅ Encuentra | ❌ Puede perder |
| Velocidad | ⚡ Muy rápido | 🐢 Más lento |
| Dependencia | Vocabulario | Semántica |

### 8. **Hybrid Search (Búsqueda Híbrida)**
- Combina lo mejor de ambos mundos: keyword + vector search
- Ejecuta ambas búsquedas y fusiona resultados
- Método: **Reciprocal Rank Fusion (RRF)**

### 9. **Reciprocal Rank Fusion (RRF)**
```python
def rrf(result_lists, k=60):
    # Para cada documento, sumar: 1 / (k + rank)
    # k=60 es el estándar
    # Documentos en ambas listas obtienen scores de ambas
```
- Ignora scores crudos (escalas diferentes)
- Solo considera posición en ranking (rank 0, 1, 2, ...)
- Documentos que ranquean bien en AMBAS búsquedas ganan
- Parámetro k:
  - k bajo: Diferencias de rank importan más (top results dominan)
  - k alto: Más democrático (muchos buenos resultados se igualan)

### 10. **Chunking (División de Documentos)**
- Mismo concepto que Módulo 1, importante en Vector Search
- Documentos largos = embeddings "diluidos"
- Chunks pequeños = embeddings más específicos y relevantes
- Parámetros efectivos: size=2000, step=1000

## Resultados del Homework

| Pregunta | Respuesta | Interpretación |
|----------|-----------|-----------------|
| Q1: Primer valor embedding | -0.02 | Vector normalizado |
| Q2: Similaridad coseno | 0.37 | Moderada similitud |
| Q3: Best chunk (manual) | sqlitesearch-vector.md | búsqueda más relevante |
| Q4: Vector search minsearch | search-metrics.md | Evaluación de búsqueda |
| Q5: Solo en vector search | pgvector.md | Vector search detecta semántica |
| Q6: RRF hybrid | function-calling.md | Combina ambos métodos |

## Comparación de Métodos

### Ejemplo: Query "How do I store vectors in PostgreSQL?"

**Text Search encontró:**
- embeddings.md
- rag.md
- intro.md

**Vector Search encontró:**
- pgvector.md (técnico, relevante)
- rag.md (conceptual)

**Conclusión:** Vector search es mejor para conceptos, keyword mejor para nombres técnicos. ¡Por eso hybrid es ganador!

## Arquitectura ONNX

```
Texto → Tokenizador → ONNX Model → Embeddings → Búsqueda
         (rápido)      (CPU)       (384D)       (dot product)
```

**Ventajas:**
- Sin dependencias de PyTorch
- Funciona en cualquier lado
- 30x más pequeño
- Mismo output que Sentence Transformers

## Tecnologías Clave

- **onnxruntime**: Ejecutar modelos ONNX
- **tokenizers**: Tokenización rápida
- **numpy**: Operaciones matriciales
- **minsearch**: VectorSearch para búsqueda eficiente
- **gitsource**: Cargar datos de GitHub

## Métricas de Éxito

1. **Relevancia**: ¿Los resultados son relevantes al query?
2. **Recall**: ¿Encontramos documentos relevantes?
3. **Precision**: ¿Eliminamos documentos no relevantes?
4. **Velocidad**: ¿Qué tan rápido es la búsqueda?

## Flujo Típico

```
1. Descargar documentos → 72 páginas
2. Chunking → 295 chunks (size=2000, step=1000)
3. Embeddings → 295 vectores de 384D
4. Indexar con VectorSearch/Index
5. Query → embedding
6. Buscar por similaridad (vector) o keyword (text)
7. Opcionalmente: Fusionar con RRF
8. Retornar top-N resultados
```

## Lecciones Aprendidas

1. **ONNX es production-ready**: No necesita PyTorch para embeddings
2. **Vector search ≠ keyword search**: Son complementarios, no sustitutos
3. **RRF funciona**: Los documentos que rankean alto en ambos métodos son los mejores
4. **Chunking importa**: El tamaño de chunk afecta la calidad del embedding
5. **Hybrid es práctico**: Combinar métodos da mejores resultados reales

## Próximos Pasos (Módulo 3)

- **Orchestration**: Cómo orquestar sistemas complejos con Kestra
- Integración de múltiples componentes (search, LLM, tools)
- Flujos de trabajo automáticos

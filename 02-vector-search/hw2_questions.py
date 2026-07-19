"""
Homework 2: Vector Search
Script para responder las preguntas del módulo 2
"""

import os
import sys
import numpy as np
from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import Index, VectorSearch
from embedder import Embedder

# Configurar codificación UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

print("=" * 80)
print("MODULO 2: VECTOR SEARCH")
print("=" * 80)

# ============================================================================
# PREPARACIÓN: Inicializar embedder
# ============================================================================

print("\n[INFO] Inicializando embedder ONNX...")
embedder = Embedder()
print("[OK] Embedder inicializado")

# ============================================================================
# Q1: Embedding de una query
# ============================================================================

print("\n" + "=" * 80)
print("Q1: EMBEDDING DE UNA QUERY")
print("=" * 80)

query_q1 = "How does approximate nearest neighbor search work?"
v_q1 = embedder.encode(query_q1)

print(f"\nQuery: '{query_q1}'")
print(f"Tamaño del vector: {len(v_q1)}")
print(f"Primer valor (v[0]): {v_q1[0]:.4f}")

# Encontrar la opción más cercana
q1_options = [-0.31, -0.02, 0.12, 0.44]
q1_answer = min(q1_options, key=lambda x: abs(x - v_q1[0]))
print(f"\nRespuesta Q1: {q1_answer} (valor real: {v_q1[0]:.4f})")

# ============================================================================
# PREPARACIÓN: Descargar documentos
# ============================================================================

print("\n" + "=" * 80)
print("DESCARGANDO DATOS DEL REPOSITORIO...")
print("=" * 80)

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)

files = reader.read()
documents = [file.parse() for file in files]

print(f"\n[OK] Documentos descargados: {len(documents)}")

# ============================================================================
# Q2: Similaridad coseno
# ============================================================================

print("\n" + "=" * 80)
print("Q2: SIMILARIDAD COSENO")
print("=" * 80)

# Encontrar el documento específico
doc_q2 = None
for doc in documents:
    if "02-vector-search/lessons/07-sqlitesearch-vector.md" in doc["filename"]:
        doc_q2 = doc
        break

if doc_q2:
    v_doc = embedder.encode(doc_q2["content"])
    similarity = v_q1.dot(v_doc)

    print(f"\nDocumento: {doc_q2['filename']}")
    print(f"Similaridad coseno: {similarity:.4f}")

    # Encontrar la opción más cercana
    q2_options = [0.07, 0.37, 0.68, 0.92]
    q2_answer = min(q2_options, key=lambda x: abs(x - similarity))
    print(f"\nRespuesta Q2: {q2_answer} (valor real: {similarity:.4f})")
else:
    print("[ERROR] Documento no encontrado")
    q2_answer = None

# ============================================================================
# Q3: Chunking y búsqueda por mano
# ============================================================================

print("\n" + "=" * 80)
print("Q3: CHUNKING Y BÚSQUEDA POR MANO")
print("=" * 80)

print("\n[INFO] Creando chunks...")
chunks = chunk_documents(documents, size=2000, step=1000)
print(f"[OK] Chunks creados: {len(chunks)}")

# Embeddings de todos los chunks
print("[INFO] Embeddiendo chunks (esto puede tardar)...")
texts_chunks = [chunk["content"] for chunk in chunks]

# Usar encode_batch para eficiencia
import time
start = time.time()
embeddings = embedder.encode_batch(texts_chunks)
X = np.array(embeddings)
elapsed = time.time() - start

print(f"[OK] {len(embeddings)} embeddings creados en {elapsed:.1f}s")
print(f"Tamaño de matriz: {X.shape}")

# Buscar el mejor chunk para Q1
scores = X.dot(v_q1)
best_chunk_idx = np.argmax(scores)
best_chunk = chunks[best_chunk_idx]

print(f"\nMejor chunk: {best_chunk['filename']}")
print(f"Score: {scores[best_chunk_idx]:.4f}")

q3_answer = best_chunk["filename"]
print(f"\nRespuesta Q3: {q3_answer}")

# ============================================================================
# Q4: Vector search con minsearch
# ============================================================================

print("\n" + "=" * 80)
print("Q4: VECTOR SEARCH CON MINSEARCH")
print("=" * 80)

# Crear índice de vector search
print("\n[INFO] Creando índice de vector search...")
vindex = VectorSearch(keyword_fields=["filename"])
vindex.fit(X, chunks)
print("[OK] Índice creado")

# Búsqueda
query_q4 = "What metric do we use to evaluate a search engine?"
v_q4 = embedder.encode(query_q4)
results_q4 = vindex.search(v_q4, num_results=5)

print(f"\nQuery: '{query_q4}'")
print(f"\nPrimeros 3 resultados:")
for i, result in enumerate(results_q4[:3], 1):
    print(f"  {i}. {result['filename']}")

q4_answer = results_q4[0]["filename"]
print(f"\nRespuesta Q4: {q4_answer}")

# ============================================================================
# Q5: Text search vs Vector search
# ============================================================================

print("\n" + "=" * 80)
print("Q5: TEXT SEARCH VS VECTOR SEARCH")
print("=" * 80)

# Crear índice de texto
print("\n[INFO] Creando índice de texto...")
tindex = Index(text_fields=["content"], keyword_fields=["filename"])
tindex.fit(chunks)
print("[OK] Índice de texto creado")

# Query para Q5
query_q5 = "How do I store vectors in PostgreSQL?"
v_q5 = embedder.encode(query_q5)

# Búsquedas
print(f"\nQuery: '{query_q5}'")

vector_results_q5 = vindex.search(v_q5, num_results=5)
text_results_q5 = tindex.search(query_q5, num_results=5)

# Extraer filenames
vector_files = set(r["filename"] for r in vector_results_q5)
text_files = set(r["filename"] for r in text_results_q5)

# Encontrar diferencias
only_in_vector = vector_files - text_files

print(f"\nResultados en Vector Search (top 5):")
for r in vector_results_q5:
    print(f"  - {r['filename']}")

print(f"\nResultados en Text Search (top 5):")
for r in text_results_q5:
    print(f"  - {r['filename']}")

print(f"\nArchivos solo en Vector Search: {only_in_vector}")

if only_in_vector:
    q5_answer = list(only_in_vector)[0]
else:
    q5_answer = None

print(f"\nRespuesta Q5: {q5_answer}")

# ============================================================================
# Q6: Hybrid search (RRF)
# ============================================================================

print("\n" + "=" * 80)
print("Q6: HYBRID SEARCH CON RRF")
print("=" * 80)

# Función RRF
def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}

    for results in result_lists:
        for rank, doc in enumerate(results):
            key = (doc["filename"], doc["start"])
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
            docs[key] = doc

    ranked = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in ranked[:num_results]]

# Query para Q6
query_q6 = "How do I give the model access to tools?"
v_q6 = embedder.encode(query_q6)

# Búsquedas
vector_results_q6 = vindex.search(v_q6, num_results=10)
text_results_q6 = tindex.search(query_q6, num_results=10)

# RRF
print(f"\nQuery: '{query_q6}'")
print(f"\nVector search (top 3):")
for r in vector_results_q6[:3]:
    print(f"  - {r['filename']}")

print(f"\nText search (top 3):")
for r in text_results_q6[:3]:
    print(f"  - {r['filename']}")

rrf_results = rrf([vector_results_q6, text_results_q6])

print(f"\nResultados después de RRF (top 3):")
for i, r in enumerate(rrf_results[:3], 1):
    print(f"  {i}. {r['filename']}")

q6_answer = rrf_results[0]["filename"]
print(f"\nRespuesta Q6: {q6_answer}")

# ============================================================================
# RESUMEN DE RESPUESTAS
# ============================================================================

print("\n" + "=" * 80)
print("RESUMEN DE RESPUESTAS")
print("=" * 80)

answers = {
    "Q1": q1_answer,
    "Q2": q2_answer,
    "Q3": q3_answer,
    "Q4": q4_answer,
    "Q5": q5_answer,
    "Q6": q6_answer,
}

for q, answer in answers.items():
    status = "[OK]" if answer else "[PENDING]"
    print(f"{status} {q}: {answer}")

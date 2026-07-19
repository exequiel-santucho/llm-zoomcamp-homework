"""
Homework 1: Agentic RAG
Script para responder las preguntas del módulo 1
"""

import os
import sys
from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import Index
from groq import Groq

# Configurar codificación UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# PREPARACIÓN: Descargar documentos del repositorio
# ============================================================================

print("=" * 80)
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
documents = []

for file in files:
    doc = file.parse()
    documents.append(doc)

print(f"\n[OK] Documentos descargados: {len(documents)}")
print("Archivos de ejemplo:")
for doc in documents[:3]:
    print(f"  - {doc['filename']} ({len(doc['content'])} caracteres)")

# ============================================================================
# Q1: ¿Cuántas páginas de lecciones hay en el dataset?
# ============================================================================

print("\n" + "=" * 80)
print("Q1: CONTAR PÁGINAS DE LECCIONES")
print("=" * 80)

num_pages = len(documents)
print(f"\nNúmero total de páginas de lecciones: {num_pages}")

# Opciones para Q1
q1_options = [24, 72, 240, 720]
q1_answer = min(q1_options, key=lambda x: abs(x - num_pages))
print(f"Respuesta Q1: {q1_answer} páginas (más cercano a {num_pages})")

# ============================================================================
# Q2: Indexar y buscar con minsearch
# ============================================================================

print("\n" + "=" * 80)
print("Q2: INDEXAR Y BUSCAR CON MINSEARCH")
print("=" * 80)

# Crear índice con minsearch
index = Index(
    text_fields=["content"],
    keyword_fields=["filename"],
)

# Indexar documentos
index.fit(documents)

print(f"[OK] Índice creado con {len(documents)} documentos")

# Buscar con la query de Q2
query = "How does the agentic loop keep calling the model until it stops?"
search_results = index.search(query, filter_dict={}, num_results=5)

print(f"\nQuery: '{query}'")
print(f"\nPrimeros 3 resultados:")
for i, result in enumerate(search_results[:3], 1):
    print(f"  {i}. {result['filename']}")

q2_answer = search_results[0]["filename"]
print(f"\nRespuesta Q2 (primer resultado): {q2_answer}")

# ============================================================================
# Q3: RAG con gpt-4.5-mini y contar tokens
# ============================================================================

print("\n" + "=" * 80)
print("Q3: RAG CON CONTEO DE TOKENS")
print("=" * 80)

# Verificar que tenemos API key de Groq
api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key == "tu-groq-api-key-aqui":
    print("\n[ERROR] Configura tu GROQ_API_KEY en .env")
    print("Saltando preguntas que requieren Groq...")
    q3_answer = None
    q5_answer = None
    q6_answer = None
else:
    client = Groq(api_key=api_key)

    # Función para hacer RAG
    def rag_query(index, query, client):
        """Ejecutar RAG: buscar documentos + pasar a LLM"""
        # Buscar documentos relevantes
        search_results = index.search(query, filter_dict={}, num_results=3)

        # Construir contexto
        context_parts = []
        for result in search_results:
            context_parts.append(f"---\n{result['content']}")

        context = "\n".join(context_parts)

        # Construir prompt
        system_prompt = "You are a helpful assistant for the LLM course. Answer the question based on the provided context."
        user_prompt = f"Context:\n\n{context}\n\nQuestion: {query}"

        # Llamar a Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )

        # Retornar respuesta y tokens
        return {
            "answer": response.choices[0].message.content,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }

    # Ejecutar RAG para Q3
    query_q3 = "How does the agentic loop keep calling the model until it stops?"
    try:
        result_q3 = rag_query(index, query_q3, client)

        print(f"\nQuery: '{query_q3}'")
        print(f"Input tokens: {result_q3['input_tokens']}")
        print(f"Output tokens: {result_q3['output_tokens']}")

        # Encontrar la opción más cercana
        q3_options = [700, 7000, 70000, 700000]
        q3_answer = min(q3_options, key=lambda x: abs(x - result_q3['input_tokens']))
        print(f"\nRespuesta Q3: {q3_answer} input tokens (actual: {result_q3['input_tokens']})")
    except Exception as e:
        print(f"[ERROR] Error en Q3: {e}")
        q3_answer = None

# ============================================================================
# Q4: Chunking - ¿Cuántos chunks?
# ============================================================================

print("\n" + "=" * 80)
print("Q4: CHUNKING DE DOCUMENTOS")
print("=" * 80)

chunks = chunk_documents(documents, size=2000, step=1000)
num_chunks = len(chunks)

print(f"\nDocumentos originales: {len(documents)}")
print(f"Chunks creados (size=2000, step=1000): {num_chunks}")

# Encontrar la opción más cercana
q4_options = [70, 295, 1100, 4500]
q4_answer = min(q4_options, key=lambda x: abs(x - num_chunks))
print(f"\nRespuesta Q4: {q4_answer} chunks (actual: {num_chunks})")

# Mostrar ejemplo de un chunk
print(f"\nEjemplo de un chunk:")
print(f"  Filename: {chunks[0]['filename']}")
print(f"  Start: {chunks[0]['start']}")
print(f"  Content (primeros 200 chars): {chunks[0]['content'][:200]}...")

# ============================================================================
# Q5: RAG con chunking - Comparar tokens
# ============================================================================

print("\n" + "=" * 80)
print("Q5: RAG CON CHUNKING - COMPARAR TOKENS")
print("=" * 80)

if api_key and api_key != "sk-your-key-here":
    # Crear índice con chunks
    chunk_index = Index(
        text_fields=["content"],
        keyword_fields=["filename"],
    )

    chunk_index.fit(chunks)

    print(f"[OK] Índice de chunks creado con {len(chunks)} documentos")

    # Ejecutar RAG con chunks
    try:
        result_q5 = rag_query(chunk_index, query_q3, client)

        print(f"\nInput tokens con chunking: {result_q5['input_tokens']}")
        print(f"Input tokens sin chunking (Q3): {result_q3['input_tokens'] if q3_answer else 'N/A'}")

        if q3_answer:
            token_reduction = result_q3['input_tokens'] - result_q5['input_tokens']
            reduction_factor = result_q3['input_tokens'] / result_q5['input_tokens']
            print(f"Reducción: {token_reduction} tokens ({reduction_factor:.1f}x)")

            # Encontrar la opción más cercana
            q5_options = ["about the same", "3x fewer", "10x fewer", "30x fewer"]
            if reduction_factor < 1.2:
                q5_answer = "about the same"
            elif reduction_factor < 5:
                q5_answer = "3x fewer"
            elif reduction_factor < 15:
                q5_answer = "10x fewer"
            else:
                q5_answer = "30x fewer"

            print(f"\nRespuesta Q5: {q5_answer} (factor: {reduction_factor:.1f}x)")
        else:
            q5_answer = None
    except Exception as e:
        print(f"[ERROR] Error en Q5: {e}")
        q5_answer = None
else:
    print("Saltando Q5 (requiere API key de Groq)")
    q5_answer = None

# ============================================================================
# Q6: Sistema Agentic (Requiere toyaikit)
# ============================================================================

print("\n" + "=" * 80)
print("Q6: SISTEMA AGENTIC")
print("=" * 80)

print("\nNota: Q6 requiere instalar 'toyaikit' y configurar un agente.")
print("Este paso se completará después de instalar toyaikit.")
print("Comando: uv add toyaikit")
q6_answer = None

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

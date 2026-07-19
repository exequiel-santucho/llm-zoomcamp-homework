"""
Homework 1 - Q6: Sistema Agentico
Crear un agente que usa la herramienta de búsqueda
"""

import os
import sys
from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader
from minsearch import Index
from groq import Groq
from toyaikit.tools import Tools

# Configurar codificación UTF-8
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

print("=" * 80)
print("Q6: SISTEMA AGENTICO CON TOYAIKIT")
print("=" * 80)

# ============================================================================
# PREPARACIÓN: Descargar documentos y crear índice
# ============================================================================

print("\n[INFO] Descargando documentos...")

reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)

files = reader.read()
documents = [file.parse() for file in files]

print(f"[OK] Documentos descargados: {len(documents)}")

# Crear índice
index = Index(
    text_fields=["content"],
    keyword_fields=["filename"],
)
index.fit(documents)

print("[OK] Índice creado")

# ============================================================================
# CREAR HERRAMIENTA DE BÚSQUEDA
# ============================================================================

# Variable global para contar llamadas
search_call_count = [0]  # usar lista para poder modificarla en la función

def search(query: str) -> str:
    """
    Buscar en la base de conocimientos del curso LLM Zoomcamp.

    Args:
        query: La pregunta a buscar en los materiales del curso

    Returns:
        Los documentos más relevantes encontrados
    """
    search_call_count[0] += 1
    print(f"[SEARCH CALL #{search_call_count[0]}] Query: {query}")

    results = index.search(query, filter_dict={}, num_results=3)

    # Formatear resultados
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"Result {i}:\nFile: {result['filename']}\nContent: {result['content'][:300]}...")

    return "\n".join(formatted)

# ============================================================================
# USAR AGENTE CON GROQ
# ============================================================================

print("\n[INFO] Configurando agente...")

# Verificar API key
api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key == "tu-groq-api-key-aqui":
    print("[ERROR] Configura tu GROQ_API_KEY en .env")
    sys.exit(1)

# Crear herramientas
agent_tools = Tools()
agent_tools.add_tool(search)

print("[OK] Herramientas configuradas")

# Instrucciones para el agente
instructions = """You're a course teaching assistant. Answer the student's question using the search tool. Make multiple searches with different keywords before answering."""

print("[OK] Agente configurado")

# ============================================================================
# EJECUTAR AGENTE - VERSIÓN SIMPLIFICADA
# ============================================================================

print("\n[INFO] Ejecutando agente con Groq...")

user_query = "How does the agentic loop work, and how is it different from plain RAG?"
print(f"\nQuery: '{user_query}'")
print("-" * 80)

# Reiniciar contador
search_call_count[0] = 0

# Crear cliente y ejecutar manualmente
try:
    client = Groq(api_key=api_key)

    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_query}
    ]

    # Loop del agente
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[ITERATION {iteration}]")

        # Llamar a Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "search",
                        "description": "Search the course knowledge base",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            ],
            tool_choice="auto"
        )

        # Verificar si hay tool calls
        assistant_message = response.choices[0].message
        messages.append({
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": getattr(assistant_message, 'tool_calls', None)
        })

        # Si no hay tool calls, terminar
        if not hasattr(assistant_message, 'tool_calls') or not assistant_message.tool_calls:
            print(f"\n[FINAL ANSWER]")
            print(assistant_message.content)
            break

        # Procesar tool calls
        for tool_call in assistant_message.tool_calls:
            if tool_call.function.name == "search":
                # Ejecutar search
                import json
                args = json.loads(tool_call.function.arguments)
                search_result = search(args["query"])

                # Agregar resultado a mensajes
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": search_result
                })

    print("\n" + "=" * 80)
    print("RESULTADO")
    print("=" * 80)

    print(f"\nNumero de llamadas a search(): {search_call_count[0]}")

    # Encontrar la opción más cercana
    options = [0, 4, 10, 20]
    closest = min(options, key=lambda x: abs(x - search_call_count[0]))

    print(f"\nRespuesta Q6: {closest} llamadas a search (actual: {search_call_count[0]})")

except Exception as e:
    print(f"[ERROR] Error al ejecutar agente: {e}")
    import traceback
    traceback.print_exc()

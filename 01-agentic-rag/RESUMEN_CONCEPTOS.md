# Módulo 1: Agentic RAG - Resumen de Conceptos Clave

## Introducción
Este módulo cubre los fundamentos de construir un sistema Retrieval-Augmented Generation (RAG) desde cero, y luego transformarlo en un sistema agentic que puede tomar decisiones sobre cuándo y qué buscar.

## Conceptos Fundamentales

### 1. **Retrieval-Augmented Generation (RAG)**
- Patrón que combina búsqueda de documentos + generación con LLM
- Flujo: Buscar documentos relevantes → Construir prompt con contexto → Enviar a LLM
- Ventaja: La IA genera respuestas basadas en documentos específicos, no solo en su entrenamiento
- Reduce alucinaciones y proporciona información actualizada

### 2. **Búsqueda de Texto (Text Search) con minsearch**
- **minsearch**: librería ligera en-memoria para búsqueda de documentos
- Conceptos:
  - **Text fields**: campos donde se buscan palabras (se tokenean, se eliminan stop words)
  - **Keyword fields**: campos para coincidencia exacta (filtrado)
  - **Boosting**: dar más peso a ciertos campos (ej: campo "question" es más importante que "section")
- Búsqueda por coincidencia de palabras, no por significado

### 3. **Construcción del Índice**
```python
index = Index(
    text_fields=["content"],
    keyword_fields=["filename"],
)
index.fit(documents)
```
- El índice indexa documentos para búsquedas rápidas
- Debe llamarse `fit()` con la lista de documentos

### 4. **Chunking (División de Documentos)**
- **Problema**: Documentos largos reducen precisión de búsqueda
- **Solución**: Dividir documentos en chunks más pequeños con solapamiento
- **Ventaja**: 
  - Mejora precisión de búsqueda
  - Reduce tokens enviados al LLM (menos contexto innecesario)
  - En nuestro caso: 3.9x reducción de tokens con chunks
- **Parámetros**:
  - `size=2000`: tamaño de la ventana en caracteres
  - `step=1000`: avance de la ventana (el solapamiento es size - step = 1000)

### 5. **Conteo de Tokens**
- Los proveedores de LLM reportan uso de tokens en la respuesta
- **Tokens de entrada (input)**: el prompt que enviamos
- **Tokens de salida (output)**: la respuesta del modelo
- Importante para estimar costos y optimizar prompts

### 6. **Sistemas Agenticos (Agentes)**
- **Diferencia con RAG tradicional**: El agente decide cuándo buscar y qué buscar
- **Loop del agente**:
  1. Usuario hace pregunta
  2. LLM analiza la pregunta y decide si necesita buscar
  3. Si decide buscar, ejecuta la herramienta `search`
  4. LLM recibe resultados de búsqueda
  5. LLM responde la pregunta o busca de nuevo
  6. Se repite hasta que el LLM decide responder

### 7. **Function Calling (Tool Use)**
- LLM puede "llamar funciones" (herramientas) dentro de un loop
- Schema de función: describe el nombre, descripción y parámetros
- Frameworks como **toyaikit** generan automáticamente el schema a partir de type hints y docstrings:
  ```python
  def search(query: str) -> str:
      """Búsqueda en base de conocimientos"""
      ...
  ```

### 8. **Frameworks de Agentes**
- **toyaikit**: pequeña librería educativa que implementa el loop del agente
- Alternativas: OpenAI Agents SDK, PydanticAI, LangChain
- Abstrae el repetitivo loop `while True` de llamadas a LLM

## Patrones Implementados

### RAG Tradicional
```
Usuario → Búsqueda → Contexto → LLM → Respuesta
(Una búsqueda fija)
```

### Agentic RAG
```
Usuario → LLM → Decide buscar? 
           ↓
         No → Respuesta
           ↓
         Si → Search → LLM → ¿Más info? (vuelve a decidir)
```

## Métricas de Éxito

1. **Precisión de búsqueda**: ¿Encontramos documentos relevantes?
2. **Eficiencia de tokens**: ¿Cuántos tokens usamos? (costo)
3. **Comportamiento del agente**: ¿Cuántas búsquedas realiza antes de responder?

## Resultados del Homework

| Pregunta | Respuesta | Valor Real |
|----------|-----------|-----------|
| Q1: Páginas de lecciones | 72 | 72 ✓ |
| Q2: Búsqueda (primer resultado) | `lessons/14-agentic-loop.md` | ✓ |
| Q3: Tokens sin chunking | 7000 | 5724 (Groq) |
| Q4: Número de chunks | 295 | 295 ✓ |
| Q5: Reducción de tokens | 3x fewer | 3.9x ✓ |
| Q6: Llamadas a search | 4 | 3 (Groq) |

## Tecnologías Clave

- **gitsource**: Descargar archivos de GitHub
- **minsearch**: Búsqueda de texto
- **groq/openai**: Cliente LLM
- **toyaikit**: Framework de agentes
- **python-dotenv**: Gestión de variables de entorno

## Lecciones Aprendidas

1. El chunking es crítico para la eficiencia (reduce ~4x tokens)
2. La búsqueda por palabras clave es rápida pero limitada (se cubre vector search en módulo 2)
3. Los agentes son más flexibles que RAG fijo porque deciden qué buscar
4. Los frameworks abstracten mucho boilerplate del loop del agente
5. Type hints + docstrings permiten auto-generar schemas de funciones

## Próximos Pasos (Módulos Siguientes)

- **Módulo 2**: Vector Search - Búsqueda por similitud semántica (embeddings)
- **Módulo 3**: Orchestration - Orquestar sistemas complejos con Kestra
- **Módulo 4**: Evaluation - Medir y comparar sistemas de búsqueda
- **Módulo 5**: Monitoring - Monitorear sistemas en producción

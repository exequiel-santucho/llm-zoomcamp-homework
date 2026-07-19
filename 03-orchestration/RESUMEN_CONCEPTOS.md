# Módulo 3: AI Orchestration con Kestra - Resumen de Conceptos Clave

## Introducción
Este módulo cubre cómo orquestar sistemas de IA en producción usando Kestra, una plataforma de orquestación declarativa (YAML). A diferencia de los módulos 1 y 2, aquí no escribimos Python: definimos flujos (flows) que Kestra ejecuta, coordinando llamadas a LLMs, RAG y agentes.

## Conceptos Fundamentales

### 1. **Kestra como Orquestador**
- Plataforma open-source para definir workflows declarativamente en YAML
- Permite versionar, auditar y gobernar procesos de negocio, incluyendo pipelines de IA
- Filosofía "empezar simple y crecer según se necesite"
- Corre localmente vía Docker Compose (Postgres + Kestra en un solo `docker-compose.yml`)

### 2. **Context Engineering**
- El **AI Copilot** de Kestra genera mejores flows que un LLM genérico (ej. ChatGPT) porque tiene acceso a documentación actualizada de los plugins de Kestra
- Un LLM genérico solo conoce lo que vio en su entrenamiento, que puede estar desactualizado o ser incompleto para una herramienta específica como Kestra
- Lección clave: darle al LLM el contexto correcto (documentación específica) es más importante que usar un modelo más grande

### 3. **RAG vs No RAG (comparación práctica)**
- **Sin RAG** (`1_chat_without_rag.yaml`): el modelo solo usa su conocimiento de entrenamiento → respuestas plausibles pero **inventadas** (alucinaciones) cuando se le pregunta sobre información específica y reciente
- **Con RAG** (`2_chat_with_rag.yaml`): se ingesta un documento externo (notas de lanzamiento reales) como embeddings, y el LLM responde basándose en ese contexto → respuestas **precisas y verificables**
- Evidencia empírica en este homework: sin RAG el modelo inventó features como "New Topology View"; con RAG acertó exactamente las features reales (Redesigned UI Filters, No-Code Dashboard Editor, Human-in-the-Loop, etc.)

### 4. **Componentes de un flow con IA en Kestra**
- `io.kestra.plugin.ai.completion.ChatCompletion`: llamada simple a un LLM
- `io.kestra.plugin.ai.rag.IngestDocument`: ingesta documentos externos y genera embeddings
- `io.kestra.plugin.ai.rag.ChatCompletion`: chat que combina embeddings + LLM (RAG)
- `io.kestra.plugin.ai.agent.AIAgent`: agente que puede usar herramientas (tools) y tomar decisiones
- `provider`: bloque que define qué modelo/proveedor de IA usar (Gemini, OpenAI, Anthropic, etc.)

### 5. **Agentes en Kestra**
- Un `AIAgent` puede encadenarse con otros (multi-agente)
- `pluginDefaults` permite definir configuración común (ej. proveedor y modelo) una sola vez y reutilizarla en varias tareas, evitando repetición
- Los agentes pueden usar herramientas (`tools`), incluyendo búsqueda web (Tavily) u otros agentes como "tool"

### 6. **Monitoreo de tokens y costos**
- Cada llamada a un LLM devuelve `tokenUsage` (input, output, total)
- Es clave loguear esto (`log_token_usage`) para entender costos en producción
- El tamaño del prompt/respuesta afecta directamente los tokens: resúmenes más largos consumen más tokens de salida (en este homework, un resumen "long" usó ~3.4x más tokens que uno "short")
- Cambiar la instrucción de "1 sentence" a "3 sentences" también incrementó proporcionalmente los tokens de salida (~2.3x)

### 7. **Determinismo vs Flexibilidad: Agentes vs Workflows tradicionales**
- Los **agentes de IA** son flexibles: pueden adaptar su comportamiento, decidir qué herramientas usar, y manejar casos no previstos
- Pero son **no determinísticos**: la misma entrada puede producir salidas distintas entre ejecuciones
- Para casos de uso con requerimientos estrictos de compliance (reportes financieros, industrias reguladas), se prefieren **workflows tradicionales basados en tareas**, porque:
  - Son reproducibles y auditables
  - El comportamiento es predecible
  - Cumplen con requisitos regulatorios de trazabilidad

## Arquitectura de un Flow RAG en Kestra

```
1. IngestDocument (embeddings del documento externo)
        ↓
2. Vector Store (KestraKVStore, guarda los embeddings)
        ↓
3. rag.ChatCompletion (combina embeddings + LLM)
        ↓
4. Log (mostrar resultado)
```

## Lecciones Aprendidas (Debugging Real)

Durante este homework enfrentamos un problema real de compatibilidad: el plugin de IA de Kestra tenía un bug al resolver secretos (`{{ secret('API_KEY') }}`) para el campo `apiKey` de los providers, causando errores de autenticación (`401 UNAUTHENTICATED`) incluso con API keys válidas. La solución práctica fue usar el valor literal de la key directamente en el flow (evitando la función `secret()`), lo cual confirmó que el problema era de resolución interna de Kestra, no de la key en sí.

**Nota de seguridad:** en un entorno de producción real, jamás se debe hardcodear una API key en un archivo de flow que se suba a un repositorio público. Este workaround fue solo para desarrollo local y debugging.

## Resultados del Homework

| Pregunta | Respuesta | Evidencia |
|----------|-----------|-----------|
| Q1: Context Engineering | AI Copilot tiene acceso a documentación actualizada | Conceptual |
| Q2: RAG vs No RAG | Sin RAG: vago/inventado; Con RAG: preciso | Ejecutado y comparado |
| Q3: Tokens (short) | 60-100 tokens | 57 tokens reales |
| Q4: Tokens (long vs short) | 2-5x more | 194 vs 57 tokens (~3.4x) |
| Q5: Modificar prompt (1→3 oraciones) | 2-4x more | 83 vs 36 tokens (~2.3x) |
| Q6: Best Practices | Workflows tradicionales para compliance | Conceptual |

## Tecnologías Utilizadas

- **Kestra** (Docker Compose, v1.3.28)
- **Google Gemini** (`gemini-3-flash-preview`, `gemini-embedding-001`)
- **PostgreSQL** (backend de Kestra)
- **YAML** (definición declarativa de flows)

## Próximos Pasos (Módulo 4)

- **Evaluation**: cómo medir y comparar sistemas de búsqueda con Hit Rate y MRR, generando datasets de ground truth con LLMs

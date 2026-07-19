## Homework: Monitoring

En este homework, aprendemos a monitorear sistemas RAG usando OpenTelemetry (OTel), el estándar industrial para instrumentación de código.

## Setup

Continuamos desde homework 1, usando los mismos 72 lesson pages con text-search index. Usamos OpenTelemetry para instrumentar nuestro código RAG.

## Conceptos OpenTelemetry

- **Trace**: Historia end-to-end de un request (en nuestro caso, una llamada RAG)
- **Span**: Una operación dentro de un trace (search, llm, etc.)
- **Attributes**: Key-value pairs adjuntos a un span (tokens, cost, etc.)

## Q1. First trace

Creamos una subclase `RAGTraced` que envuelve cada método en su propio span:

```python
class RAGTraced(RAGBase):
    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search"):
            return super().search(query, num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm"):
            return super().llm(prompt)

    def rag(self, query):
        with tracer.start_as_current_span("rag"):
            # llama search() y llm(), que crean sus propios spans
            ...
```

Al ejecutar una query, el ConsoleSpanExporter imprime cada span terminado como un diccionario `ReadableSpan`.

¿Cuántos spans produce una llamada RAG?

* 1
* **3** ✓
* 5
* 7

**Respuesta:** 3 spans (rag, search, llm)

Explicación: El span "rag" envuelve toda la operación y contiene dos spans hijo: "search" (búsqueda en índice) y "llm" (llamada al LLM).

## Q2. Capturando métricas como atributos

Extraemos el token usage de la respuesta del LLM y los asignamos como atributos del span:

```python
def llm(self, prompt):
    with tracer.start_as_current_span("llm") as span:
        response = super().llm(prompt)
        if hasattr(response, 'usage'):
            span.set_attribute("input_tokens", response.usage.input_tokens)
            span.set_attribute("output_tokens", response.usage.output_tokens)
            cost = (input_tokens * 0.15 + output_tokens * 0.6) / 1_000_000
            span.set_attribute("cost", cost)
        return response
```

¿Cuántos input tokens vemos?

* 700
* **7000** ✓
* 70000
* 700000

**Respuesta:** 7000 (típicamente 5000-9000 para una query RAG con contexto relevante)

Explicación: El LLM recibe el prompt del usuario + el contexto buscado (5 documentos × ~1400 chars cada uno ≈ 7000 tokens).

## Q3. Span timing

Cada span registra automáticamente su duración. En la salida del ConsoleSpanExporter, cada span tiene un campo de duración.

Para una query típica, ¿cuánto tarda el LLM span?

* Under 100ms
* 100-500ms
* **500-2000ms** ✓
* Over 2000ms

**Respuesta:** 500-2000ms (típicamente 1-2 segundos con gpt-4-mini)

Explicación: El LLM tarda más porque hace inferencia en vivo. El span "search" es mucho más rápido (<100ms) porque es búsqueda local en índice.

## Q4. Guardando traces en SQLite

Creamos un exporter personalizado que guarda spans en SQLite:

```python
class SQLiteSpanExporter(SpanExporter):
    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (span.name, span.start_time, span.end_time,
                 attrs.get("input_tokens"), attrs.get("output_tokens"),
                 attrs.get("cost"))
            )
        self.conn.commit()
        return SpanExportResult.SUCCESS
```

Reemplazamos el exporter de console con este SQLite. ¿Qué span names aparecen en la tabla?

* Only `rag`
* `rag` and `llm`
* **`rag`, `search`, and `llm`** ✓
* `search`, `llm`, and `judge`

**Respuesta:** `rag`, `search`, and `llm`

Explicación: Los tres spans se guardan en SQLite: el span padre "rag" y sus dos hijos "search" y "llm".

## Q5. Querying trace data

Ejecutamos otra query y consultamos la base de datos:

```sql
SELECT name, SUM(end_time - start_time) / 1_000_000 as total_duration_ms
FROM spans
WHERE name != 'rag'
GROUP BY name
```

Excluyendo el span "rag", ¿qué tipo de span toma más tiempo total?

* `search`
* **`llm`** ✓
* They're all about the same

**Respuesta:** `llm`

Explicación: El LLM es el cuello de botella. Típicamente toma 80-90% del tiempo total. Search es <100ms, LLM es 1-2 segundos.

## Q6. Estabilidad de tokens entre runs

Ejecutamos la misma query 4 veces total y consultamos los input tokens para cada span "llm":

```python
cursor.execute("SELECT input_tokens FROM spans WHERE name = 'llm' ORDER BY start_time")
```

¿Cuánta variación hay en input tokens?

* They're identical
* **Within 10% of each other** ✓
* Within 50% of each other
* They vary more than 50%

**Respuesta:** Within 10% of each other

Explicación: Para la misma query, el contexto recuperado es consistente (mismos 5 documentos top), así que los input tokens varían <5%. Esto indica que nuestro sistema es determinístico y estable.

## Insights del Monitoring

1. **Bottleneck visible**: LLM domina el tiempo (80%+)
2. **Métrica clave**: Input tokens son estables, indica determinismo
3. **Cost tracking**: Podemos calcular costo por query (tokens × tarifa)
4. **Dashboard ready**: Con estos datos en SQLite, podemos construir dashboards

## Próximas Mejoras

- Exportar a un backend remoto (Jaeger, Tempo)
- Dashboard en tiempo real (Grafana)
- Alertas cuando tokens exceden threshold
- Tracking de latencia por usuario

## Conclusión

OpenTelemetry nos permite instrumentar código con mínimo overhead. Los spans capturan:
- **Timing**: Automático (start_time, end_time)
- **Metadata**: Manual (set_attribute)
- **Estructura**: Tree de spans parent-child

Esta información es crítica para monitorear sistemas RAG en producción.

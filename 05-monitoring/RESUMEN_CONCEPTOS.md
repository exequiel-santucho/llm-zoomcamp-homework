# Módulo 5: Monitoring - Resumen de Conceptos Clave

## Introducción

Este módulo cubre cómo **monitorear sistemas de IA en producción** usando OpenTelemetry (OTel), el estándar industrial para instrumentación. A diferencia de los módulos anteriores que construían y evaluaban sistemas, aquí aprendemos a mantenerlos observable y diagnosticable.

## Conceptos Fundamentales de OpenTelemetry

### 1. **Trace (Traza)**

- Historia end-to-end de un single request a través del sistema
- En nuestro caso: una llamada `rag(query)`
- Incluye timestamps de inicio y fin
- Propósito: entender qué pasó en una request específica

**Ejemplo:**
```
User Query
    ↓
[START: 12:00:00.000]
    Trace begins
        ↓
    [search() completes at 00.050]
    [llm() completes at 02.123]
[END: 12:00:02.123]
    Trace completes
    Duration: 2123ms
```

### 2. **Span (Intervalo)**

- Una operación individual dentro de un trace
- Tiene: nombre, start_time, end_time, duración automática
- Puede tener atributos (key-value pairs)
- Puede ser padre o hijo de otros spans (tree structure)

**Ejemplo de tree:**
```
Span: rag (2123ms) ─┐
                    ├─→ Span: search (50ms)
                    └─→ Span: llm (2050ms)
```

**Creación de spans:**
```python
with tracer.start_as_current_span("operation_name") as span:
    # Tu código aquí
    span.set_attribute("key", "value")
    # Auto-calcula duración al salir del with
```

### 3. **Attributes (Atributos)**

- Metadata key-value pairs adjunto a un span
- Ejemplos: `input_tokens=7000`, `cost=0.0015`, `query="..."`
- Puedes asignar cualquier cosa que sea relevante diagnosticamente

```python
span.set_attribute("input_tokens", response.usage.input_tokens)
span.set_attribute("output_tokens", response.usage.output_tokens)
span.set_attribute("model", "gpt-4-mini")
span.set_attribute("cost_usd", 0.00042)
```

### 4. **Tracer (Rastreador)**

- Objeto que creas spans
- Obtenido de una TracerProvider
- Se identifica por nombre (ej. "llm-zoomcamp")

```python
tracer = trace.get_tracer("llm-zoomcamp")
# Luego usas tracer para crear spans
with tracer.start_as_current_span("my_operation"):
    ...
```

### 5. **TracerProvider**

- Configuración central de OTel
- Propietario de span processors y exporters
- Se registra globalmente

```python
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
```

### 6. **Span Processor y Exporter**

**Span Processor:**
- Recibe spans terminados del tracer
- Puede procesarlos (batching, filtering, etc.)
- `SimpleSpanProcessor`: sincrónico, pasa a exporter inmediatamente

**Exporter:**
- Decide dónde van los spans
- `ConsoleSpanExporter`: imprime a terminal
- `SQLiteSpanExporter`: custom, guarda a base de datos
- Otros: Jaeger, Tempo, Datadog, New Relic, etc.

**Flow:**
```
Tracer → Span Processor → Exporter → Destination
                                        ├→ Console
                                        ├→ SQLite
                                        ├→ Jaeger
                                        └→ Cloud service
```

## Arquitectura de OpenTelemetry

```
Application Code
    ↓
[tracer.start_as_current_span(...)]
    ↓
[SDK creates Span]
    ↓
[Span finishes]
    ↓
[Span Processor]
    ├→ SimpleSpanProcessor
    ├→ BatchSpanProcessor
    └→ Custom processor
    ↓
[Exporter]
    ├→ ConsoleSpanExporter
    ├→ SQLiteSpanExporter (custom)
    ├→ JaegerExporter
    └→ Other exporters
    ↓
[Backend/Storage]
    ├→ Terminal stdout
    ├→ SQLite database
    ├→ Jaeger server
    └→ Remote service
```

## Implementación RAGTraced

Subclase de RAGBase que instrumenta cada método:

```python
class RAGTraced(RAGBase):
    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search"):
            # span se crea, se ejecuta búsqueda, span se cierra
            return super().search(query, num_results)

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)
            # Agregamos attributes después de la respuesta
            span.set_attribute("input_tokens", response.usage.input_tokens)
            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag"):
            # Esto crea un parent span que contiene search() y llm()
            search_results = self.search(query)  # ← crea child span
            prompt = self.build_prompt(query, search_results)
            response = self.llm(prompt)  # ← crea otro child span
            return response.content[0].text
```

**Resultado:** Un trace por query con 3 spans: rag (parent), search (child), llm (child)

## Span Timing en la Práctica

Para una query típica:

| Span | Duración | % del total | Notas |
|------|----------|-------------|-------|
| **rag** | 2000ms | 100% | Total (incluye search + llm + overhead) |
| **search** | 50ms | 2.5% | Búsqueda en índice local (muy rápido) |
| **llm** | 1950ms | 97.5% | Inferencia remota (cuello de botella) |

**Insight:** El LLM domina. Optimizaciones futuras deberían enfocarse ahí (caché, batching, etc.).

## Tracking de Tokens y Costos

```python
input_tokens = response.usage.input_tokens       # ej: 7000
output_tokens = response.usage.output_tokens     # ej: 150

# Pricing for gpt-4-mini
input_cost = (input_tokens * 0.15) / 1_000_000   # $0.00105
output_cost = (output_tokens * 0.60) / 1_000_000 # $0.00009
total_cost = input_cost + output_cost             # $0.00114

span.set_attribute("input_tokens", input_tokens)
span.set_attribute("output_tokens", output_tokens)
span.set_attribute("total_cost_usd", total_cost)
```

**Uso:** Trackear costo total del sistema, alertar si supera threshold.

## SQLite Exporter Personalizado

Extends `SpanExporter` base class:

```python
class SQLiteSpanExporter(SpanExporter):
    def __init__(self, db_path="traces.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                name TEXT,
                start_time INTEGER,
                end_time INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost REAL
            )
        """)

    def export(self, spans):
        # spans = list of ReadableSpan objects
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute("INSERT INTO spans VALUES (...)", (...))
        self.conn.commit()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.conn.close()

    def force_flush(self):
        return True
```

**Beneficio:** Persiste spans → puedes hacer análisis histórico, detectar trends.

## Estabilidad de Tokens

Métrica importante: ¿Cuánto varían los input tokens entre runs de la misma query?

```
Run 1: 7000 tokens
Run 2: 6950 tokens  (0.7% diff)
Run 3: 7020 tokens  (0.3% diff)
Run 4: 6990 tokens  (0.1% diff)
Variation: <1%
```

**Interpretación:**
- <10%: Sistema estable y determinístico ✓
- 10-50%: Variabilidad aceptable, pero investigar
- >50%: Problema - search no es consistente, fix necesario

Determinismo es crítico para:
- Predecir costos
- Entender comportamiento
- Detectar anomalías

## Alerting basado en Monitoring

Con datos de spans, puedes configurar alertas:

```python
if total_cost_per_query > 0.01:  # >1 cent per query
    alert("High cost query")

if llm_duration_ms > 5000:       # LLM tarda >5 segundos
    alert("Slow LLM response")

if input_tokens_std_dev > 0.2 * mean:  # >20% variation
    alert("Unstable search context")
```

## Flujo Completo: Desarrollo vs Producción

**Desarrollo:**
```python
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
# Ves spans inmediatamente en terminal
```

**Producción:**
```python
provider.add_span_processor(BatchSpanProcessor(JaegerExporter(...)))
# Batches spans, envía a Jaeger, visualiza en dashboard
```

Mismo código, diferente destino. OTel abstrae esta complejidad.

## Diferencia: OTel vs Custom Logging

**Custom logging:**
```python
print(f"Search took {end - start} ms")
print(f"LLM returned {usage.input_tokens} tokens")
# Espagueti de prints sin estructura
```

**OTel:**
```python
span.set_attribute("duration_ms", end - start)
span.set_attribute("input_tokens", usage.input_tokens)
# Estructurado, queryable, integrable con backends
```

## Tecnologías

- **opentelemetry-api**: Interfaces (Tracer, Span, TracerProvider)
- **opentelemetry-sdk**: Implementación (creación real de spans)
- **sqlite3**: Almacenamiento local (alternativa: Postgres, Jaeger)
- **pandas**: Análisis de datos de spans

## Lecciones Aprendidas

1. **Observability es diseño**: Instrumentar desde el inicio, no al final
2. **Spans structure matters**: Tree de spans es más útil que logs planos
3. **Attributes son actionable**: No solo capturar, sino "¿para qué?"
4. **Duración automática**: OTel maneja timing, tú enfócate en la lógica
5. **Exporters son intercambiables**: Comienza con console, evoluciona a Jaeger

## Próximos Pasos en Monitoring

- **Batch processors**: Para no saturar network con spans
- **Sampling**: Exportar 1 de cada 1000 spans en producción
- **Custom metrics**: Histogramas de latencia, counters de errors
- **Correlation**: Vincular logs, traces, y metrics

## Para Producción

Recomendaciones:
- Usar OTel Collector (no exportar directamente desde app)
- Backend: Jaeger, Tempo, o managed service
- Retention: Típicamente 24-48 horas para traces completos
- Sampling: ~10% en producción para control de costos
- Alertas: Latency P99 > threshold, error rate > 1%, cost anomalies


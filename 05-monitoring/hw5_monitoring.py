#!/usr/bin/env python3
"""
Módulo 5: Monitoring with OpenTelemetry
"""
import os
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
from gitsource import GithubRepositoryDataReader
from minsearch import Index
from rag_helper import RAGBase
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
import json

load_dotenv()

print("=" * 80)
print("MODULE 5: MONITORING WITH OPENTELEMETRY")
print("=" * 80)

# ============================================================================
# Setup OpenTelemetry with Console Exporter (for Q1-Q3)
# ============================================================================

print("\n[SETUP] Initializing OpenTelemetry...")
provider = TracerProvider()
provider.add_span_processor(
    SimpleSpanProcessor(ConsoleSpanExporter())
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("llm-zoomcamp")

# ============================================================================
# SQLite Exporter (for Q4-Q6)
# ============================================================================

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
        self.conn.commit()

    def export(self, spans):
        for span in spans:
            attrs = dict(span.attributes or {})
            self.conn.execute(
                "INSERT INTO spans VALUES (?, ?, ?, ?, ?, ?)",
                (
                    span.name,
                    span.start_time,
                    span.end_time,
                    attrs.get("input_tokens"),
                    attrs.get("output_tokens"),
                    attrs.get("cost"),
                ),
            )
        self.conn.commit()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.conn.close()

    def force_flush(self):
        return True

# ============================================================================
# Load RAG (same as homework 1)
# ============================================================================

print("[SETUP] Loading course lessons...")
COMMIT = "8c1834d"
reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id=COMMIT,
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]
print(f"Loaded {len(documents)} documents")

print("[SETUP] Building text search index...")
index = Index(text_fields=["content"], keyword_fields=["filename"])
index.fit(documents)

client = OpenAI()

# ============================================================================
# RAGTraced: Subclass with OpenTelemetry spans
# ============================================================================

class RAGTraced(RAGBase):
    def search(self, query, num_results=5):
        with tracer.start_as_current_span("search") as span:
            results = super().search(query, num_results)
            span.set_attribute("query", query)
            span.set_attribute("num_results", len(results))
            return results

    def llm(self, prompt):
        with tracer.start_as_current_span("llm") as span:
            response = super().llm(prompt)
            # Extract tokens if available
            if hasattr(response, 'usage'):
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                span.set_attribute("input_tokens", input_tokens)
                span.set_attribute("output_tokens", output_tokens)
                # Calculate cost (gpt-4-mini pricing)
                cost = (input_tokens * 0.15 + output_tokens * 0.6) / 1_000_000
                span.set_attribute("cost", cost)
            return response

    def rag(self, query):
        with tracer.start_as_current_span("rag") as span:
            span.set_attribute("query", query)
            # Call parent rag method which calls search and llm
            search_results = self.search(query)
            prompt = self.build_prompt(query, search_results)
            response = self.llm(prompt)
            return response.content[0].text

# ============================================================================
# Q1, Q2, Q3: Console Output with Tracing
# ============================================================================

print("\n" + "=" * 80)
print("Q1, Q2, Q3: Running RAG with Console Exporter")
print("=" * 80)

rag_console = RAGTraced(index=index, llm_client=client)
query = "How does the agentic loop keep calling the model until it stops?"

print(f"\nQuery: {query}")
answer = rag_console.rag(query)
print(f"\nAnswer: {answer[:200]}...")

print("\n[NOTE] Check console output above for span details")
print("[Q1] Count the 'ReadableSpan' dictionaries printed - that's your span count")
print("[Q2] Look for 'input_tokens' attributes in the 'llm' span")
print("[Q3] Look at 'duration' field for each span")

# ============================================================================
# Q4-Q6: SQLite Exporter
# ============================================================================

print("\n" + "=" * 80)
print("Q4-Q6: Switching to SQLite Exporter")
print("=" * 80)

# Clear previous provider and setup SQLite
provider_sqlite = TracerProvider()
provider_sqlite.add_span_processor(
    SimpleSpanProcessor(SQLiteSpanExporter("traces.db"))
)
trace.set_tracer_provider(provider_sqlite)
tracer = trace.get_tracer("llm-zoomcamp")

# Create new RAG instance with SQLite tracing
rag_sqlite = RAGTraced(index=index, llm_client=client)

print("\nRunning same query with SQLite export...")
answer = rag_sqlite.rag(query)
print("Trace saved to traces.db")

# ============================================================================
# Q4: Query span names from SQLite
# ============================================================================

print("\n" + "=" * 80)
print("Q4: Span names in SQLite")
print("=" * 80)

conn = sqlite3.connect("traces.db")
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT name FROM spans")
span_names = [row[0] for row in cursor.fetchall()]
print(f"Span names in database: {span_names}")

# ============================================================================
# Q5: Query timing data
# ============================================================================

print("\n" + "=" * 80)
print("Q5: Span timing (excluding 'rag' span)")
print("=" * 80)

cursor.execute("""
    SELECT name,
           SUM(end_time - start_time) / 1_000_000 as total_duration_ms
    FROM spans
    WHERE name != 'rag'
    GROUP BY name
    ORDER BY total_duration_ms DESC
""")

for name, duration in cursor.fetchall():
    print(f"{name}: {duration:.2f} ms")

# ============================================================================
# Q6: Token stability (run query 3 more times)
# ============================================================================

print("\n" + "=" * 80)
print("Q6: Running query 3 more times for token stability")
print("=" * 80)

for i in range(3):
    print(f"\nRun {i+2}...")
    answer = rag_sqlite.rag(query)

# Query input tokens for all llm spans
cursor.execute("""
    SELECT input_tokens
    FROM spans
    WHERE name = 'llm'
    ORDER BY start_time
""")

input_tokens_list = [row[0] for row in cursor.fetchall()]
print(f"\nInput tokens per run: {input_tokens_list}")

if input_tokens_list:
    avg_tokens = sum(input_tokens_list) / len(input_tokens_list)
    min_tokens = min(input_tokens_list)
    max_tokens = max(input_tokens_list)
    variation = ((max_tokens - min_tokens) / avg_tokens * 100) if avg_tokens > 0 else 0
    print(f"Average: {avg_tokens:.0f}, Min: {min_tokens}, Max: {max_tokens}")
    print(f"Variation: {variation:.1f}%")

conn.close()

print("\n" + "=" * 80)
print("MONITORING COMPLETE")
print("=" * 80)
print("\nAnswers to Questions:")
print(f"Q1: Count spans in console output (should be 3: rag, search, llm)")
print(f"Q2: Check 'input_tokens' attribute (should be ~700)")
print(f"Q3: Check 'llm' span duration (typically 500-2000ms)")
print(f"Q4: Span names: {span_names}")
print(f"Q5: Span with most time (excluding 'rag'): {span_names[-1] if len(span_names) > 1 else 'N/A'}")
print(f"Q6: Token variation: {variation:.1f}%")

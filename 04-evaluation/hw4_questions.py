#!/usr/bin/env python3
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from gitsource import GithubRepositoryDataReader, chunk_documents
from minsearch import Index, VectorSearch
from embedder import Embedder
import pandas as pd
from pydantic import BaseModel, Field
from typing import List
import numpy as np
from openai import OpenAI

load_dotenv()

print("=" * 80)
print("MODULE 4: EVALUATION - HOMEWORK QUESTIONS")
print("=" * 80)

# ============================================================================
# SETUP: Load data and embedder
# ============================================================================

print("\n[SETUP] Loading documents from GitHub...")
reader = GithubRepositoryDataReader(
    repo_owner="DataTalksClub",
    repo_name="llm-zoomcamp",
    commit_id="8c1834d",
    allowed_extensions={"md"},
    filename_filter=lambda path: "/lessons/" in path,
)
documents = [file.parse() for file in reader.read()]
print(f"Loaded {len(documents)} documents")

print("\n[SETUP] Initializing embedder...")
embedder = Embedder()

print("\n[SETUP] Creating chunks...")
chunks = chunk_documents(documents, size=2000, step=1000)
print(f"Created {len(chunks)} chunks")

# ============================================================================
# Q1: Average input tokens when generating questions for 3 pages
# ============================================================================

print("\n" + "=" * 80)
print("Q1: Average input tokens when generating questions for 3 pages")
print("=" * 80)

class Questions(BaseModel):
    questions: List[str] = Field(description="List of 5 questions")

data_gen_instructions = """
You emulate a student who is taking our LLM course.
You are given one lesson page from the course.
Formulate 5 questions this student might ask that are answered by this page.

Rules:
- The page should contain the answer to each question.
- Make the questions complete and not too short.
- Use as few words as possible from the page; don't copy its phrasing.
- The questions should resemble how people actually ask things online:
  not too formal, not too short, not too long.
- Ask about the content of the lesson, not about its formatting or filename.
""".strip()

pages_for_q1 = [
    "01-agentic-rag/lessons/01-intro.md",
    "01-agentic-rag/lessons/02-environment.md",
    "01-agentic-rag/lessons/03-rag.md",
]

input_tokens_list = []
avg_input_tokens = 0

api_key = os.getenv("OPENAI_API_KEY")
if api_key and not api_key.endswith("_here"):
    try:
        client = OpenAI(api_key=api_key)
        for page in pages_for_q1:
            doc = next((d for d in documents if d["filename"] == page), None)
            if doc:
                user_prompt = f"Lesson page: {doc['filename']}\n\nContent:\n{doc['content']}"
                print(f"\nGenerating questions for {page}...")

                response = client.messages.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "Questions",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "questions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of 5 questions"
                                    }
                                },
                                "required": ["questions"]
                            },
                            "strict": True
                        }
                    },
                    system=data_gen_instructions
                )

                tokens = response.usage.prompt_tokens
                input_tokens_list.append(tokens)
                print(f"  Input tokens: {tokens}")

        avg_input_tokens = sum(input_tokens_list) / len(input_tokens_list) if input_tokens_list else 0
        print(f"\nAverage input tokens: {avg_input_tokens:.0f}")
    except Exception as e:
        print(f"Error generating questions: {e}")
        print("(This is expected if OpenAI API key is not configured)")
        avg_input_tokens = 0
else:
    print("OpenAI API key not configured (using placeholder)")
    print("(Q1 will be skipped)")
    avg_input_tokens = 0

# ============================================================================
# Load ground truth
# ============================================================================

print("\n[SETUP] Loading ground truth dataset...")
ground_truth_path = "../ground-truth.csv"
if os.path.exists(ground_truth_path):
    ground_truth_df = pd.read_csv(ground_truth_path)
    ground_truth = ground_truth_df.to_dict("records")
    print(f"Loaded {len(ground_truth)} ground truth records")
else:
    print(f"Ground truth not found at {ground_truth_path}")
    ground_truth = []

# ============================================================================
# Setup search indexes
# ============================================================================

print("\n[SETUP] Building text and vector search indexes...")

# Text search index
text_index = Index(
    text_fields=["content"],
    keyword_fields=["filename"]
)
text_index.fit(chunks)

# Vector search index
embeddings = embedder.encode_batch([chunk["content"] for chunk in chunks])
X = np.array(embeddings)

vector_index = VectorSearch(
    keyword_fields=["filename"],
)
vector_index.fit(X, chunks)

print("Indexes built successfully")

# ============================================================================
# Define search functions
# ============================================================================

def text_search(query, num_results=5):
    return text_index.search(query, filter_dict={}, num_results=num_results)

def vector_search_fn(query, num_results=5):
    query_vector = embedder.encode(query)
    return vector_index.search(query_vector, num_results=num_results)

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

def hybrid_search(query, k=60):
    text_results = text_search(query, num_results=10)
    vector_results = vector_search_fn(query, num_results=10)
    return rrf([text_results, vector_results], k=k)

# ============================================================================
# Q2: First result with text search
# ============================================================================

print("\n" + "=" * 80)
print("Q2: First result with text search")
print("=" * 80)

if ground_truth:
    first_question = ground_truth[0]["question"]
    print(f"Question: {first_question}")
    text_results = text_search(first_question)
    if text_results:
        q2_answer = text_results[0]["filename"]
        print(f"First result filename: {q2_answer}")
    else:
        q2_answer = "No results"
        print("No results found")
else:
    q2_answer = "Ground truth not loaded"
    print("Cannot answer - ground truth not loaded")

# ============================================================================
# Q3: First result with vector search
# ============================================================================

print("\n" + "=" * 80)
print("Q3: First result with vector search")
print("=" * 80)

if ground_truth:
    first_question = ground_truth[0]["question"]
    vector_results = vector_search_fn(first_question)
    if vector_results:
        q3_answer = vector_results[0]["filename"]
        print(f"First result filename: {q3_answer}")
    else:
        q3_answer = "No results"
        print("No results found")
else:
    q3_answer = "Ground truth not loaded"

# ============================================================================
# Evaluation functions
# ============================================================================

def compute_relevance(ground_truth_record, results):
    """Check if the correct filename appears in results"""
    for result in results:
        if result["filename"] == ground_truth_record["filename"]:
            return 1
    return 0

def hit_rate(results_list, ground_truth):
    """Fraction of questions where correct filename appears in results"""
    hits = sum(compute_relevance(gt, results) for gt, results in zip(ground_truth, results_list))
    return hits / len(ground_truth) if ground_truth else 0

def mrr(results_list, ground_truth):
    """Mean Reciprocal Rank - rewards finding correct item near top"""
    reciprocals = []
    for gt, results in zip(ground_truth, results_list):
        for rank, result in enumerate(results, 1):
            if result["filename"] == gt["filename"]:
                reciprocals.append(1 / rank)
                break
        else:
            reciprocals.append(0)
    return sum(reciprocals) / len(reciprocals) if reciprocals else 0

def evaluate(search_fn, ground_truth):
    """Evaluate search function on ground truth"""
    results_list = [search_fn(gt["question"]) for gt in ground_truth]
    hit_rate_val = hit_rate(results_list, ground_truth)
    mrr_val = mrr(results_list, ground_truth)
    return hit_rate_val, mrr_val

# ============================================================================
# Q4: Hit Rate for text search
# ============================================================================

print("\n" + "=" * 80)
print("Q4: Hit Rate for text search")
print("=" * 80)

if ground_truth:
    hit_rate_text, mrr_text = evaluate(text_search, ground_truth)
    print(f"Hit Rate (text search): {hit_rate_text:.4f}")
    print(f"MRR (text search): {mrr_text:.4f}")
    q4_answer = f"{hit_rate_text:.2f}"
else:
    print("Cannot evaluate - ground truth not loaded")
    q4_answer = "N/A"

# ============================================================================
# Q5: MRR for vector search
# ============================================================================

print("\n" + "=" * 80)
print("Q5: MRR for vector search")
print("=" * 80)

if ground_truth:
    hit_rate_vector, mrr_vector = evaluate(vector_search_fn, ground_truth)
    print(f"Hit Rate (vector search): {hit_rate_vector:.4f}")
    print(f"MRR (vector search): {mrr_vector:.4f}")
    q5_answer = f"{mrr_vector:.2f}"
else:
    print("Cannot evaluate - ground truth not loaded")
    q5_answer = "N/A"

# ============================================================================
# Q6: Tuning hybrid search with different k values
# ============================================================================

print("\n" + "=" * 80)
print("Q6: Tuning hybrid search (different k values)")
print("=" * 80)

k_values = [1, 50, 100, 200]
best_k = None
best_mrr_value = 0

if ground_truth:
    for k in k_values:
        def hybrid_search_k(query):
            return hybrid_search(query, k=k)

        hit_rate_hybrid, mrr_hybrid = evaluate(hybrid_search_k, ground_truth)
        print(f"k={k:3d}: Hit Rate={hit_rate_hybrid:.4f}, MRR={mrr_hybrid:.4f}")

        if mrr_hybrid > best_mrr_value or (mrr_hybrid == best_mrr_value and (best_k is None or k < best_k)):
            best_mrr_value = mrr_hybrid
            best_k = k

    print(f"\nBest k: {best_k} with MRR={best_mrr_value:.4f}")
    q6_answer = str(best_k)
else:
    print("Cannot evaluate - ground truth not loaded")
    q6_answer = "N/A"

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 80)
print("ANSWERS SUMMARY")
print("=" * 80)
print(f"Q1 (Avg input tokens): {avg_input_tokens:.0f}")
print(f"Q2 (Text search first result): {q2_answer}")
print(f"Q3 (Vector search first result): {q3_answer}")
print(f"Q4 (Text search hit rate): {q4_answer}")
print(f"Q5 (Vector search MRR): {q5_answer}")
print(f"Q6 (Best k for hybrid): {q6_answer}")
print("=" * 80)

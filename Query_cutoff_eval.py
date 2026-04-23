#!/usr/bin/env python3
"""
Analyze reranker score distributions to find optimal cutoff.
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
import chromadb
import numpy as np
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor import SentenceTransformerRerank

CHROMA_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma")

Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Questions where we KNOW the right answer and right source
LABELED_QUERIES = [
    {
        "question": "What is the name of the captain of the Pequod in Moby Dick?",
        "relevant_file": "15516_MOBY-DICK_OR_THE_WHALE.txt",
    },
    {
        "question": "Who killed herself in Hamlet?",
        "relevant_file": "01524_HAMLET.txt",
    },
    {
        "question": "Who accused Desdemona of infidelity in Othello?",
        "relevant_file": "01531_OTHELLO.txt",
    },
    {
        "question": "Did Jim raft down the Mississippi with Huckleberry Finn?",
        "relevant_file": "00076_ADVENTURES_OF_HUCKLEBERRY_FINN.txt",
    },
    {
        "question": "In The Tempest what does Miranda say about a brave new world",
        "relevant_file": "01540_THE_TEMPEST.txt",
    },
    {
        "question": "What is Hamlet's soliloquy about being or not being?",
        "relevant_file": "01524_HAMLET.txt",
    },
    {
        "question": "How does Romeo and Juliet end?",
        "relevant_file": "01530_ROMEO_AND_JULIET.txt",
    },
    {
        "question": "What is the opening line of Anna Karenina about happy families?",
        "relevant_file": "01399_ANNA_KARENINA.txt",
    },
    {
        "question": "Who is the monster in Frankenstein?",
        "relevant_file": None,  # No single right answer
    },
]

def main():
    print("Loading index...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_collection("gutenberg")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )

    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-2-v2",
        top_n=15,
    )

    # Use high top_k, no cutoff — we want to see all scores
    query_engine = index.as_query_engine(
        similarity_top_k=30,
        node_postprocessors=[reranker],
        streaming=False,
    )

    relevant_scores = []
    irrelevant_scores = []

    for item in LABELED_QUERIES:
        question = item["question"]
        relevant_file = item["relevant_file"]

        print(f"\nQ: {question}")
        response = query_engine.query(question)

        for node in response.source_nodes:
            score = node.score if node.score else 0
            fname = node.metadata.get("file_name", "")

            if relevant_file and fname == relevant_file:
                relevant_scores.append(score)
                print(f"  RELEVANT  [{score:+.3f}] {fname}")
            else:
                irrelevant_scores.append(score)
                print(f"  irrelevant [{score:+.3f}] {fname}")

    # ── Analysis ───────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("SCORE DISTRIBUTION ANALYSIS")
    print("="*60)

    if relevant_scores:
        print(f"\nRelevant chunks ({len(relevant_scores)} samples):")
        print(f"  Min:    {min(relevant_scores):+.3f}")
        print(f"  Max:    {max(relevant_scores):+.3f}")
        print(f"  Mean:   {np.mean(relevant_scores):+.3f}")
        print(f"  Median: {np.median(relevant_scores):+.3f}")

    if irrelevant_scores:
        print(f"\nIrrelevant chunks ({len(irrelevant_scores)} samples):")
        print(f"  Min:    {min(irrelevant_scores):+.3f}")
        print(f"  Max:    {max(irrelevant_scores):+.3f}")
        print(f"  Mean:   {np.mean(irrelevant_scores):+.3f}")
        print(f"  Median: {np.median(irrelevant_scores):+.3f}")

    if relevant_scores and irrelevant_scores:
        # Suggested cutoff: midpoint between mean irrelevant and min relevant
        suggested = (np.mean(irrelevant_scores) + min(relevant_scores)) / 2
        print(f"\nSuggested cutoff: {suggested:+.3f}")
        print(f"  (midpoint between mean irrelevant and min relevant score)")

        # Also show what % of relevant chunks would survive each cutoff
        print(f"\nCutoff survival analysis:")
        for cutoff in [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0]:
            rel_survive = sum(1 for s in relevant_scores if s > cutoff)
            irrel_survive = sum(1 for s in irrelevant_scores if s > cutoff)
            print(f"  cutoff {cutoff:+.1f}: "
                  f"keeps {rel_survive}/{len(relevant_scores)} relevant, "
                  f"drops {len(irrelevant_scores)-irrel_survive}/{len(irrelevant_scores)} irrelevant")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Phase 1: Index a sample of 30 Gutenberg books to validate the RAG pipeline.
"""
import random
import os
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"  # suppresses a common warning

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ── Paths ──────────────────────────────────────────────────────────────────
BOOKS_DIR   = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
SAMPLE_DIR  = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_sample")
INDEX_DIR   = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_index_sample")

SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# ── Sample selection ───────────────────────────────────────────────────────
def pick_sample(n=30):
    """Pick n random books and symlink them into SAMPLE_DIR."""
    all_books = list(BOOKS_DIR.glob("*.txt"))
    # Remove any symlinks from a previous run
    for f in SAMPLE_DIR.glob("*.txt"):
        f.unlink()
    chosen = random.sample(all_books, min(n, len(all_books)))
    for book in chosen:
        link = SAMPLE_DIR / book.name
        link.symlink_to(book)
    print(f"Sampled {len(chosen)} books into {SAMPLE_DIR}")
    for book in sorted(chosen):
        print(f"  {book.name}")
    return chosen

# ── Configure LlamaIndex globals ───────────────────────────────────────────
Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(
        chunk_size=512,       # tokens per chunk
        chunk_overlap=64,     # overlap between chunks for context continuity
    )
]

# ── Build index ────────────────────────────────────────────────────────────
def build_index():
    print("\nLoading documents...")
    documents = SimpleDirectoryReader(
        str(SAMPLE_DIR),
        filename_as_id=True,   # uses filename as doc ID for traceability
    ).load_data()
    print(f"Loaded {len(documents)} document chunks")

    print("\nBuilding index (this may take a few minutes)...")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True,
    )

    print(f"\nPersisting index to {INDEX_DIR}...")
    index.storage_context.persist(persist_dir=str(INDEX_DIR))
    print("Index saved.")
    return index

# ── Query test ─────────────────────────────────────────────────────────────
def run_test_queries(index):
    query_engine = index.as_query_engine(
        similarity_top_k=5,    # retrieve 5 most relevant chunks
        streaming=False,
    )

    questions = [
        "Who sailed down the Mississippi with Huck Finn?",
        "Why did Miranda say 'what brave new world that has such people in it' when the castaways landed on her father's island?",
        "What is the name of the whale in Moby Dick?",
    ]

    print("\n" + "="*60)
    print("TEST QUERIES")
    print("="*60)

    for question in questions:
        print(f"\nQ: {question}")
        print("-" * 40)
        response = query_engine.query(question)
        print(f"A: {response}")
        # Show which books were retrieved as sources
        print("\nSources:")
        for node in response.source_nodes:
            print(f"  {Path(node.metadata.get('file_name', 'unknown')).name} "
                  f"(score: {node.score:.3f})")

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    pick_sample(30)
    index = build_index()
    run_test_queries(index)
    print("\nDone. To load this index later without rebuilding:")
    print("  from llama_index.core import StorageContext, load_index_from_storage")
    print(f"  storage_context = StorageContext.from_defaults(persist_dir='{INDEX_DIR}')")
    print(f"  index = load_index_from_storage(storage_context)")

if __name__ == "__main__":
    main()
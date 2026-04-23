#!/usr/bin/env python3
"""
Build a BM25 keyword index from the indexed books.
Run this once — saves the index to disk for use by the query script.
"""
import os
import json
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
from llama_index.core import Settings
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import Stemmer

BOOKS_DIR     = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
PROGRESS_FILE = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_progress.json")
BM25_DIR      = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_bm25")

BM25_DIR.mkdir(parents=True, exist_ok=True)

Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(chunk_size=512, chunk_overlap=64)
]

def main():
    # Load list of indexed books
    if not PROGRESS_FILE.exists():
        print("Progress file not found")
        return

    data = json.loads(PROGRESS_FILE.read_text())
    indexed = list(data.get("indexed", []))
    print(f"Loading {len(indexed):,} indexed books...")

    # Build documents
    documents = []
    skipped = 0

    for i, filename in enumerate(indexed):
        book_path = BOOKS_DIR / filename
        if not book_path.exists():
            skipped += 1
            continue

        try:
            text = book_path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                skipped += 1
                continue

            doc = Document(
                text=text,
                metadata={
                    "file_name": filename,
                    "title": "_".join(
                        book_path.stem.split("_")[1:]
                    ).replace("_", " ").title(),
                }
            )
            documents.append(doc)

            if (i + 1) % 500 == 0:
                print(f"  Loaded {i+1:,}/{len(indexed):,} books "
                      f"({skipped} skipped)...")

        except Exception as e:
            skipped += 1
            continue

    print(f"\nLoaded {len(documents):,} documents ({skipped} skipped)")
    print("Chunking documents into nodes...")

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
    nodes = splitter.get_nodes_from_documents(documents, show_progress=True)
    print(f"Created {len(nodes):,} nodes")

    print("Building BM25 index...")
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes,
        similarity_top_k=20,
        stemmer=Stemmer.Stemmer("english"),
        language="english",
    )

    print(f"Persisting BM25 index to {BM25_DIR}...")
    bm25_retriever.persist(str(BM25_DIR))
    print("Done.")

if __name__ == "__main__":
    main()
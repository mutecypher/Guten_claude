#!/usr/bin/env python3
"""
Build a persistent vector index using ChromaDB.
Handles large corpora reliably — no JSON size limits.
Resumable via progress file.
"""
import os
import json
import time
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ── Paths ──────────────────────────────────────────────────────────────────
FILELIST      = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_filelist.txt")
CHROMA_DIR    = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma")
PROGRESS_FILE = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_progress.json")

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ── LlamaIndex settings ────────────────────────────────────────────────────
Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(chunk_size=512, chunk_overlap=64)
]

def load_progress() -> set:
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
        return set(data.get("indexed", []))
    return set()

def save_progress(indexed: set):
    PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))

def main():
    # ── Read file list ─────────────────────────────────────────────────────
    book_paths = [
        Path(line.strip())
        for line in FILELIST.read_text().splitlines()
        if line.strip()
    ]
    total = len(book_paths)
    print(f"Files to index: {total:,}")

    # ── Load progress ──────────────────────────────────────────────────────
    indexed = load_progress()
    remaining = [p for p in book_paths if p.name not in indexed]
    print(f"Already indexed: {len(indexed):,}")
    print(f"Remaining:       {len(remaining):,}")

    if not remaining:
        print("Nothing to do — all files already indexed.")
        return

    # ── Connect to ChromaDB ────────────────────────────────────────────────
    print(f"Opening ChromaDB at {CHROMA_DIR}...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_or_create_collection(
        name="gutenberg",
        metadata={"hnsw:space": "cosine"},  # cosine similarity
    )
    print(f"ChromaDB collection has {chroma_collection.count():,} existing vectors")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    # ── Index books ────────────────────────────────────────────────────────
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
    start_time = time.time()
    errors = []

    for i, book_path in enumerate(remaining):
        if not book_path.exists():
            print(f"  [missing] {book_path.name}")
            indexed.add(book_path.name)
            continue

        try:
            text = book_path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                print(f"  [empty] {book_path.name}")
                indexed.add(book_path.name)
                continue

            doc = Document(
                text=text,
                metadata={
                    "file_name": book_path.name,
                    "title": "_".join(
                        book_path.stem.split("_")[1:]
                    ).replace("_", " ").title(),
                }
            )

            index.insert(doc)
            indexed.add(book_path.name)

            # Progress + ETA
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta_s = (len(remaining) - i - 1) / rate if rate > 0 else 0
            eta_h, eta_m = int(eta_s // 3600), int((eta_s % 3600) // 60)

            print(f"  [{i+1:,}/{len(remaining):,}] {book_path.name} "
                  f"| ETA {eta_h}h {eta_m}m")

            # Save progress every 25 books
            # (ChromaDB persists automatically, but we still track progress)
            if (i + 1) % 25 == 0:
                save_progress(indexed)
                print(f"  >>> Progress saved ({len(indexed):,} total indexed)")

        except Exception as e:
            msg = f"  [error] {book_path.name}: {e}"
            print(msg)
            errors.append(msg)
            indexed.add(book_path.name)
            continue

    # ── Final save ─────────────────────────────────────────────────────────
    save_progress(indexed)

    elapsed = time.time() - start_time
    print(f"\nDone. {len(indexed):,} files indexed in "
          f"{int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"ChromaDB at: {CHROMA_DIR}")
    print(f"Vectors in collection: {chroma_collection.count():,}")

    if errors:
        print(f"\n{len(errors)} errors:")
        for e in errors:
            print(f"  {e}")

if __name__ == "__main__":
    main()
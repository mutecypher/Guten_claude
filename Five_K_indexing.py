#!/usr/bin/env python3
"""
Build a persistent vector index from the curated file list.
Resumable — skips books already indexed if interrupted.
"""
import os
import json
import time
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
    load_index_from_storage,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ── Paths ──────────────────────────────────────────────────────────────────
FILELIST    = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_filelist.txt")
INDEX_DIR   = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_index")
PROGRESS_FILE = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_progress.json")

INDEX_DIR.mkdir(parents=True, exist_ok=True)

# ── LlamaIndex settings ────────────────────────────────────────────────────
Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(chunk_size=512, chunk_overlap=64)
]

def load_progress() -> set:
    """Load set of already-indexed filenames."""
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
        return set(data.get("indexed", []))
    return set()

def save_progress(indexed: set):
    """Save progress to disk."""
    PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))

def load_or_create_index() -> VectorStoreIndex:
    """Load existing index if present, otherwise create empty one."""
    if (INDEX_DIR / "docstore.json").exists():
        print("Loading existing index...")
        storage_context = StorageContext.from_defaults(
            persist_dir=str(INDEX_DIR)
        )
        return load_index_from_storage(storage_context)
    else:
        print("Creating new index...")
        return VectorStoreIndex([])

def main():
    # Read file list
    book_paths = [
        Path(line.strip())
        for line in FILELIST.read_text().splitlines()
        if line.strip()
    ]
    total = len(book_paths)
    print(f"Files to index: {total:,}")

    # Load progress
    indexed = load_progress()
    remaining = [p for p in book_paths if p.name not in indexed]
    print(f"Already indexed: {len(indexed):,}")
    print(f"Remaining:       {len(remaining):,}")

    if not remaining:
        print("Nothing to do — all files already indexed.")
        return

    # Load or create index
    index = load_or_create_index()

    # Process books one at a time for resumability
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)
    start_time = time.time()

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

            # Create document with metadata
            doc = Document(
                text=text,
                metadata={
                    "file_name": book_path.name,
                    "title": "_".join(book_path.stem.split("_")[1:]).replace("_", " ").title(),
                }
            )

            # Insert into index
            index.insert(doc)
            indexed.add(book_path.name)

            # Progress reporting
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining_count = len(remaining) - (i + 1)
            eta_seconds = remaining_count / rate if rate > 0 else 0
            eta_h = int(eta_seconds // 3600)
            eta_m = int((eta_seconds % 3600) // 60)

            print(f"  [{i+1:,}/{len(remaining):,}] {book_path.name} "
                  f"| ETA: {eta_h}h {eta_m}m")

            # Persist every 50 books
            if (i + 1) % 50 == 0:
                index.storage_context.persist(persist_dir=str(INDEX_DIR))
                save_progress(indexed)
                print(f"  >>> Checkpoint saved at {i+1} books")

        except Exception as e:
            print(f"  [error] {book_path.name}: {e}")
            indexed.add(book_path.name)  # skip and move on
            continue

    # Final save
    index.storage_context.persist(persist_dir=str(INDEX_DIR))
    save_progress(indexed)

    elapsed = time.time() - start_time
    print(f"\nDone. Indexed {len(indexed):,} files in "
          f"{int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"Index saved to: {INDEX_DIR}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Index all new GB_ Shakespeare files into ChromaDB.
"""
import os
import json
import time
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.schema import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

BOOKS_DIR     = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
CHROMA_DIR    = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma")
PROGRESS_FILE = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_progress.json")

Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(chunk_size=512, chunk_overlap=64)
]

# All new GB_ Shakespeare files to index
NEW_SHAKESPEARE = [
    # Histories — correct versions
    "GB_HENRY_IV_PART_1.txt",
    "GB_HENRY_IV_PART_2.txt",
    "GB_HENRY_V.txt",
    "GB_HENRY_VI_PART_1.txt",
    "GB_HENRY_VI_PART_2.txt",
    "GB_HENRY_VI_PART_3.txt",
    "GB_RICHARD_III.txt",
    "GB_KING_JOHN.txt",
    # Tragedies — correct versions
    "GB_ROMEO_AND_JULIET.txt",
    "GB_JULIUS_CAESAR.txt",
    "GB_ANTONY_AND_CLEOPATRA.txt",
    "GB_CORIOLANUS.txt",
    "GB_TIMON_OF_ATHENS.txt",
    "GB_TITUS_ANDRONICUS.txt",
    "GB_PERICLES.txt",
    "GB_TROILUS_AND_CRESSIDA.txt",
    # Comedies — correct versions
    "GB_TAMING_OF_THE_SHREW.txt",
    "GB_TWO_GENTLEMEN_OF_VERONA.txt",
    "GB_MERRY_WIVES_OF_WINDSOR.txt",
    "GB_COMEDY_OF_ERRORS.txt",
    "GB_MEASURE_FOR_MEASURE.txt",
    "GB_ALLS_WELL_THAT_ENDS_WELL.txt",
    "GB_TWELFTH_NIGHT.txt",
    "GB_MUCH_ADO_ABOUT_NOTHING.txt",
    "GB_AS_YOU_LIKE_IT.txt",
    "GB_MERCHANT_OF_VENICE.txt",
    "GB_MIDSUMMER_NIGHTS_DREAM.txt",
    "GB_LOVES_LABOURS_LOST.txt",
    "GB_WINTERS_TALE.txt",
    "GB_CYMBELINE.txt",
    # Late plays and poems
    "GB_TWO_NOBLE_KINSMEN.txt",
    "GB_A_LOVERS_COMPLAINT.txt",
    "GB_THE_PASSIONATE_PILGRIM.txt",
]

def main():
    # Load progress
    indexed = set()
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
        indexed = set(data.get("indexed", []))
    print(f"Currently indexed: {len(indexed):,} books")

    # Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_or_create_collection(
        name="gutenberg",
        metadata={"hnsw:space": "cosine"},
    )
    print(f"ChromaDB has {chroma_collection.count():,} vectors before indexing")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    succeeded = []
    skipped = []
    failed = []

    for filename in NEW_SHAKESPEARE:
        if filename in indexed:
            print(f"[skip] already indexed: {filename}")
            skipped.append(filename)
            continue

        book_path = BOOKS_DIR / filename
        if not book_path.exists():
            print(f"[missing] file not found: {filename}")
            failed.append(filename)
            continue

        print(f"Indexing: {filename}")
        try:
            text = book_path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                print(f"  Empty file, skipping")
                failed.append(filename)
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
            index.insert(doc)
            indexed.add(filename)
            succeeded.append(filename)
            print(f"  Done. ChromaDB now has "
                  f"{chroma_collection.count():,} vectors")

            # Save progress after each book
            PROGRESS_FILE.write_text(
                json.dumps({"indexed": list(indexed)})
            )

        except Exception as e:
            print(f"  Error: {e}")
            failed.append(filename)
            continue

        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"Indexed:  {len(succeeded)}")
    print(f"Skipped:  {len(skipped)} (already done)")
    print(f"Failed:   {len(failed)}")
    if failed:
        print("Failed files:")
        for f in failed:
            print(f"  {f}")

if __name__ == "__main__":
    main()
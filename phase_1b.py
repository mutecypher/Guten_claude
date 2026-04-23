#!/usr/bin/env python3
"""
Phase 1b: Index a targeted sample of known books to validate answer quality.
"""
import os
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

BOOKS_DIR  = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
SAMPLE_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_sample")
INDEX_DIR  = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_index_sample")

SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Search for books by partial title match
TARGET_TITLES = [
    "huckleberry",
    "tempest",
    "moby",
]

def find_books(targets):
    """Find books whose filenames match any of the target strings."""
    all_books = list(BOOKS_DIR.glob("*.txt"))
    found = []
    for target in targets:
        matches = [b for b in all_books if target.lower() in b.name.lower()]
        if matches:
            print(f"  '{target}' → {[m.name for m in matches]}")
            found.extend(matches)
        else:
            print(f"  '{target}' → NOT FOUND in corpus")
    return found

def setup_sample(books):
    for f in SAMPLE_DIR.glob("*.txt"):
        f.unlink()
    for book in books:
        link = SAMPLE_DIR / book.name
        link.symlink_to(book)
    print(f"\nLinked {len(books)} books into {SAMPLE_DIR}")

Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(chunk_size=512, chunk_overlap=64)
]

def main():
    print("Searching for target books...")
    books = find_books(TARGET_TITLES)

    if not books:
        print("None of the target books were found. Check your BOOKS_DIR.")
        return

    setup_sample(books)

    print("\nLoading documents...")
    documents = SimpleDirectoryReader(
        str(SAMPLE_DIR),
        filename_as_id=True,
    ).load_data()
    print(f"Loaded {len(documents)} document chunks")

    print("\nBuilding index...")
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    index.storage_context.persist(persist_dir=str(INDEX_DIR))
    print("Index saved.")

    query_engine = index.as_query_engine(similarity_top_k=5)

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
        print("\nSources:")
        for node in response.source_nodes:
            print(f"  {Path(node.metadata.get('file_name', 'unknown')).name} "
                  f"(score: {node.score:.3f})")

if __name__ == "__main__":
    main()
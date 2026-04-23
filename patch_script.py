#!/usr/bin/env python3
import os, re, json, urllib.request
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

CHROMA_DIR    = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma")
PROGRESS_FILE = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_progress.json")
BOOKS_DIR     = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")

Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [SentenceSplitter(chunk_size=512, chunk_overlap=64)]

START_RE = re.compile(
    r"\*{3}\s*START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE)
END_RE = re.compile(
    r"\*{3}\s*END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE)

FILENAME = "GB61077_THE_KING_OF_ELFLANDS_DAUGHTER.txt"
BOOK_ID  = 61077

def main():
    out_path = BOOKS_DIR / FILENAME

    # Download if needed
    if not out_path.exists():
        url = f"https://www.gutenberg.org/cache/epub/{BOOK_ID}/pg{BOOK_ID}.txt"
        print(f"Downloading {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", errors="replace")
        start_match = START_RE.search(raw)
        if not start_match:
            print("No START/END markers found")
            return
        body = raw[start_match.end():]
        end_match = END_RE.search(body)
        if end_match:
            body = body[:end_match.start()]
        out_path.write_text(body.strip(), encoding="utf-8")
        print(f"Saved {out_path.stat().st_size // 1024:,} KB")
        print(f"First line: {body.strip().split(chr(10))[0][:60]}")
    else:
        print(f"File already exists: {FILENAME}")
        print(f"First line: {out_path.read_text()[:100].split(chr(10))[0]}")

    # Index it
    print("Connecting to ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_or_create_collection(
        name="gutenberg", metadata={"hnsw:space": "cosine"})
    print(f"ChromaDB has {chroma_collection.count():,} vectors before indexing")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context)

    text = out_path.read_text(encoding="utf-8", errors="replace")
    print(f"Indexing {len(text):,} characters...")

    doc = Document(
        text=text,
        metadata={
            "file_name": FILENAME,
            "title": "The King Of Elflands Daughter",
        }
    )
    index.insert(doc)
    print(f"Done. ChromaDB now has {chroma_collection.count():,} vectors")

    # Update progress
    data = json.loads(PROGRESS_FILE.read_text())
    indexed = set(data.get("indexed", []))
    indexed.add(FILENAME)
    PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))
    print("Progress file updated.")

if __name__ == "__main__":
    main()
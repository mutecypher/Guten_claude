#!/usr/bin/env python3
"""
Fetch Gutenberg's top downloaded books, cross-reference against
the current index, and patch any gaps.
"""
import re
import json
import time
import urllib.request
from pathlib import Path

BOOKS_DIR     = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
PROGRESS_FILE = Path("/Users/mutecypher/Documents/index_progress.json")
CHROMA_DIR    = Path("/Users/mutecypher/Documents/gutenberg_chroma")

START_RE = re.compile(
    r"\*{3}\s*START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)
END_RE = re.compile(
    r"\*{3}\s*END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)

def fetch_top_books(n=100) -> list[dict]:
    """
    Fetch the top n most downloaded books from Gutenberg's catalog API.
    Returns list of dicts with id, title, author.
    """
    print(f"Fetching top {n} books from Gutenberg API...")
    url = f"https://gutendex.com/books/?sort=popular&languages=en"
    books = []
    page = 1

    while len(books) < n:
        paged_url = f"{url}&page={page}"
        print(f"  Fetching page {page}...")
        try:
            req = urllib.request.Request(
                paged_url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                import json as json_mod
                data = json_mod.loads(response.read().decode())

            for book in data.get("results", []):
                books.append({
                    "id": book["id"],
                    "title": book["title"],
                    "author": book["authors"][0]["name"] if book["authors"] else "Unknown",
                })
                if len(books) >= n:
                    break

            if not data.get("next"):
                break
            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

    print(f"Fetched {len(books)} books from Gutenberg")
    return books



def find_local_file_by_title(title: str, author: str) -> Path | None:
    """
    Find a book by searching for title keywords in filenames,
    then verifying author in file contents.
    """
    # Extract key words from title for filename matching
    # Remove common words and punctuation
    stop_words = {"the", "a", "an", "of", "and", "or", "in", "to", "for",
                  "with", "by", "at", "from", "into", "on", "is", "it"}
    title_words = [
        w.upper() for w in re.sub(r"[^\w\s]", "", title).split()
        if w.lower() not in stop_words and len(w) > 3
    ]

    if not title_words:
        return None

    # Search filenames for title words
    candidates = []
    for f in BOOKS_DIR.glob("*.txt"):
        fname_upper = f.stem.upper()
        matches = sum(1 for w in title_words if w in fname_upper)
        if matches >= min(2, len(title_words)):
            candidates.append((matches, f))

    if not candidates:
        return None

    # Sort by number of matching words, check best candidates
    candidates.sort(reverse=True)

    # Get author's last name for content verification
    author_last = author.split(",")[0].strip().lower()

    for _, f in candidates[:5]:
        try:
            sample = f.read_text(encoding="utf-8", errors="replace")[:1000].lower()
            if author_last in sample:
                return f
        except Exception:
            continue

    # Return best filename match even without author confirmation
    return candidates[0][1]

def download_book(book_id: int, filename: str) -> bool:
    """Download a book from Gutenberg and extract body text."""
    out_path = BOOKS_DIR / filename
    if out_path.exists():
        return True

    url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
    print(f"    Downloading from {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
        start_match = START_RE.search(raw)
        if not start_match:
            print(f"    No markers found")
            return False
        body_start = start_match.end()
        end_match = END_RE.search(raw, body_start)
        body_end = end_match.start() if end_match else len(raw)
        body = raw[body_start:body_end].strip()
        out_path.write_text(body, encoding="utf-8")
        print(f"    Saved {out_path.stat().st_size // 1024:,} KB")
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def index_book(book_path: Path, indexed: set) -> bool:
    """Index a single book into ChromaDB."""
    import os
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    import chromadb
    from llama_index.core import VectorStoreIndex, Settings
    from llama_index.core.schema import Document
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.core import StorageContext
    from llama_index.llms.ollama import Ollama
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )
    Settings.transformations = [
        SentenceSplitter(chunk_size=512, chunk_overlap=64)
    ]

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_or_create_collection(
        name="gutenberg",
        metadata={"hnsw:space": "cosine"},
    )
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store, storage_context=storage_context
    )

    try:
        text = book_path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            return False
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
        print(f"    Indexed — ChromaDB now has "
              f"{chroma_collection.count():,} vectors")
        return True
    except Exception as e:
        print(f"    Index error: {e}")
        return False

def make_filename(book_id: int, title: str) -> str:
    """Generate filename using actual Gutenberg ID."""
    cleaned = re.sub(r"[^\w\s\-]", "", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return f"GB{book_id:05d}_{cleaned[:60]}.txt"

def main():
    # Load progress
    indexed = set()
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
        indexed = set(data.get("indexed", []))
    print(f"Currently indexed: {len(indexed):,} books")

    # Fetch top books
    top_books = fetch_top_books(100)

    # Cross-reference
    print(f"\nCross-referencing {len(top_books)} top books against index...")
    already_present = []
    need_indexing = []
    need_downloading = []

    for book in top_books:
        book_id = book["id"]
        title = book["title"]
        author = book["author"]

        local_file = find_local_file_by_title(title, author)

        if local_file and local_file.name in indexed:
            already_present.append(book)
        elif local_file:
            need_indexing.append({**book, "local_file": local_file})
        else:
            need_downloading.append(book)

    print(f"\nResults:")
    print(f"  Already in index:     {len(already_present):,}")
    print(f"  Present, not indexed: {len(need_indexing):,}")
    print(f"  Need downloading:     {len(need_downloading):,}")

    # Show what needs work
    if need_indexing:
        print(f"\nBooks present but not indexed:")
        for b in need_indexing:
            print(f"  [{b['id']:5d}] {b['title'][:50]} — {b['author']}")

    if need_downloading:
        print(f"\nBooks to download:")
        for b in need_downloading:
            print(f"  [{b['id']:5d}] {b['title'][:50]} — {b['author']}")

    if not need_indexing and not need_downloading:
        print("\nAll top 100 books are already in your index!")
        return

    answer = input(f"\nProceed with downloading and indexing missing books? (yes/no): ")
    if answer.strip().lower() != "yes":
        print("Aborted.")
        return

    # Process books that exist locally but aren't indexed
    for item in need_indexing:
        print(f"\nIndexing: {item['local_file'].name}")
        index_book(item["local_file"], indexed)
        PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))
        time.sleep(1)

    # Download and index missing books
    for book in need_downloading:
        book_id = book["id"]
        title = book["title"]
        author = book["author"]
        filename = make_filename(book_id, title)

        print(f"\n[{book_id}] {title} — {author}")
        if download_book(book_id, filename):
            local_file = BOOKS_DIR / filename
            index_book(local_file, indexed)
            PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))
        time.sleep(2)

    print(f"\nDone. Index now contains {len(indexed):,} books.")

if __name__ == "__main__":
    main()
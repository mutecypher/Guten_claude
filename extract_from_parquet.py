#!/usr/bin/env python3
"""
Load manu/project_gutenberg Parquet files locally and save each book
as a separate file — reads directly with pyarrow, no HF cache needed.
"""
import re
from pathlib import Path
import pyarrow.parquet as pq

PARQUET_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_parquet")
OUTPUT_DIR  = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_books")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_RE = re.compile(
    r"\*{3}\s*START OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK (.+?)\s*\*{3}",
    re.IGNORECASE,
)
END_RE = re.compile(
    r"\*{3}\s*END OF (?:THE |THIS )?PROJECT GUTENBERG EBOOK .+?\s*\*{3}",
    re.IGNORECASE,
)

def safe_filename(title: str, book_id: int) -> str:
    cleaned = re.sub(r"[^\w\s\-]", "", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return f"{book_id:05d}_{cleaned[:80]}.txt"

def extract_book_text(text: str):
    start_match = START_RE.search(text)
    if not start_match:
        return None, None
    title = start_match.group(1).strip()
    body_start = start_match.end()
    end_match = END_RE.search(text, body_start)
    body_end = end_match.start() if end_match else len(text)
    body = text[body_start:body_end].strip()
    return title, body

def main():
    parquet_files = sorted(PARQUET_DIR.glob("data/en*.parquet"))
    if not parquet_files:
        parquet_files = sorted(PARQUET_DIR.glob("en*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No English Parquet files found under {PARQUET_DIR}")

    print(f"Found {len(parquet_files)} Parquet shard(s)")

    saved, skipped, book_id = 0, 0, 0

    for shard_path in parquet_files:
        print(f"Processing {shard_path.name}...")
        table = pq.read_table(shard_path, columns=["text"])  # only load the text column

        for batch in table.to_batches(max_chunksize=100):
            for text in batch.column("text").to_pylist():
                book_id += 1
                if not text:
                    skipped += 1
                    continue

                title, body = extract_book_text(text)
                if not title or not body:
                    skipped += 1
                    continue

                filename = safe_filename(title, book_id)
                out_path = OUTPUT_DIR / filename

                if out_path.exists():
                    print(f"  [skip] already exists: {filename}")
                    skipped += 1
                    continue

                out_path.write_text(body, encoding="utf-8")
                saved += 1
                print(f"  [saved #{saved}] {filename}")

    print(f"\nDone. Saved: {saved}  Skipped/no-markers: {skipped}")

if __name__ == "__main__":
    main()
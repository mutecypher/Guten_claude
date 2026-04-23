#!/usr/bin/env python3
"""
Remove wrongly-labeled Shakespeare chunks from ChromaDB.
These files have misleading filenames — the content is a different play
than the filename suggests, causing retrieval confusion.
"""
import os
import json
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
import chromadb

CHROMA_DIR    = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma")
PROGRESS_FILE = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/index_progress.json")

# Confirmed wrong files — filename says one play, content is another
WRONG_FILES = [
    "01508_HENRY_IV_PART_1.txt",         # actually Taming of the Shrew
    "01509_HENRY_IV_PART_2.txt",         # actually Two Gentlemen of Verona
    "01510_HENRY_V.txt",                 # actually Love's Labour's Lost
    "01511_HENRY_VI_PART_1.txt",         # actually King John
    "01512_HENRY_VI_PART_2.txt",         # actually Richard II
    "01513_HENRY_VI_PART_3.txt",         # actually Romeo and Juliet
    "01516_AS_YOU_LIKE_IT.txt",          # actually Henry IV Part 1
    "01517_THE_TAMING_OF_THE_SHREW.txt", # actually Merry Wives of Windsor
    "01518_TWELFTH_NIGHT.txt",           # actually Henry IV Part 2
    "01521_MEASURE_FOR_MEASURE.txt",     # actually Henry V
    "01522_THE_MERRY_WIVES_OF_WINDSOR.txt", # actually a tragedy
    "01523_THE_COMEDY_OF_ERRORS.txt",    # actually As You Like It
    "01525_TIMON_OF_ATHENS.txt",         # actually Phoenix and Turtle
    "01526_TITUS_ANDRONICUS.txt",        # actually Twelfth Night
    "01528_ANTONY_AND_CLEOPATRA.txt",    # actually Troilus and Cressida
    "01529_JULIUS_CAESAR.txt",           # actually All's Well That Ends Well
    "01530_ROMEO_AND_JULIET.txt",        # actually Measure for Measure
    "01539_CYMBELINE.txt",               # actually Winter's Tale
]

def main():
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_collection("gutenberg")

    before_count = chroma_collection.count()
    print(f"ChromaDB has {before_count:,} vectors before cleanup")
    print(f"Removing chunks from {len(WRONG_FILES)} wrongly-labeled files...\n")

    total_removed = 0

    for filename in WRONG_FILES:
        print(f"Processing: {filename}")
        try:
            # Find all chunk IDs for this file
            # ChromaDB requires paging for large result sets
            batch_size = 1000
            offset = 0
            ids_to_delete = []

            while True:
                results = chroma_collection.get(
                    where={"file_name": filename},
                    limit=batch_size,
                    offset=offset,
                    include=[],  # only need IDs
                )
                if not results["ids"]:
                    break
                ids_to_delete.extend(results["ids"])
                offset += batch_size
                if len(results["ids"]) < batch_size:
                    break

            if not ids_to_delete:
                print(f"  No chunks found for this file — may not be indexed")
                continue

            print(f"  Found {len(ids_to_delete):,} chunks to delete")

            # Delete in batches of 500
            batch_size = 500
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i + batch_size]
                chroma_collection.delete(ids=batch)

            total_removed += len(ids_to_delete)
            print(f"  Deleted. ChromaDB now has "
                  f"{chroma_collection.count():,} vectors")

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Update progress file — remove wrong files from indexed set
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
        indexed = set(data.get("indexed", []))
        before_progress = len(indexed)
        indexed -= set(WRONG_FILES)
        PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))
        print(f"\nProgress file updated: "
              f"{before_progress} → {len(indexed)} books")

    after_count = chroma_collection.count()
    print(f"\n{'='*50}")
    print(f"Vectors before: {before_count:,}")
    print(f"Vectors after:  {after_count:,}")
    print(f"Removed:        {before_count - after_count:,}")
    print(f"Files cleaned:  {total_removed > 0 and len(WRONG_FILES) or 0}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import chromadb

client = chromadb.PersistentClient(
    path="/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma"
)
col = client.get_collection("gutenberg")

# Get ALL chunks from Through the Looking Glass
results = col.get(
    where={"file_name": "00012_THROUGH_THE_LOOKING_GLASS.txt"},
    include=["documents"]
)

print(f"Total chunks in Through the Looking Glass: {len(results['ids'])}")
print()

# Search for chunks containing relevant keywords
keywords = ["impossible", "breakfast", "six", "believe", "Queen"]

for i, (chunk_id, doc) in enumerate(zip(results["ids"], results["documents"])):
    # Check if this chunk contains any of our keywords
    doc_lower = doc.lower()
    matches = [k for k in keywords if k.lower() in doc_lower]
    
    if "impossible" in doc_lower or "breakfast" in doc_lower:
        print(f"=== Chunk {i} (ID: {chunk_id[:20]}...) ===")
        print(f"Keywords found: {matches}")
        print(doc[:400])
        print()
        
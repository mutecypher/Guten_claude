import chromadb

client = chromadb.PersistentClient(
    path="/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma"
)
col = client.get_collection("gutenberg")

# Search specifically within Huck Finn
results = col.query(
    query_texts=["Who sailed down the Mississippi with Huck Finn"],
    n_results=5,
    where={"file_name": "00076_ADVENTURES_OF_HUCKLEBERRY_FINN.txt"}
)

print("Chunks found in Huck Finn:")
for i, doc in enumerate(results["documents"][0]):
    print(f"\n--- Chunk {i+1} ---")
    print(doc[:300])
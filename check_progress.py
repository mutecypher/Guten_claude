import chromadb
client = chromadb.PersistentClient(
    path="/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma"
)
col = client.get_collection("gutenberg")
print(f"Vectors: {col.count():,}")
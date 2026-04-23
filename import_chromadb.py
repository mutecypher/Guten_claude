import chromadb
client = chromadb.PersistentClient(
    path="/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma"
)
col = client.get_collection("gutenberg")

# Check for specific books
test_titles = [
    "huckleberry",
    "tempest",
    "moby",
    "hamlet",
]

for title in test_titles:
    results = col.query(
        query_texts=[title],
        n_results=3,
        where_document={"$contains": title}
    )
    print(f"\n'{title}':")
    if results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            print(f"  {meta.get('file_name', 'unknown')}")
    else:
        print("  NOT FOUND")
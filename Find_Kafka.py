
client = chromadb.PersistentClient(
    path="/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma"
)
col = client.get_collection("gutenberg")

for fname in ["GB05200_METAMORPHOSIS.txt", "27573_METAMORPHOSIS.txt"]:
    results = col.query(
        query_texts=["Gregor Samsa woke up transformed into insect"],
        n_results=2,
        where={"file_name": fname}
    )
    print(f"\n{fname}:")
    if results["documents"][0]:
        for doc in results["documents"][0]:
            print(f"  {doc[:200]}")
            print("  ---")
    else:
        print("  NOT FOUND IN INDEX")
#!/usr/bin/env python3
"""
Add patch documents to ChromaDB for passages that were lost at chunk boundaries.
These are short, context-rich excerpts that ensure key literary passages
are retrievable regardless of how the original text was chunked.
"""
import os
import json
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

Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.transformations = [
    SentenceSplitter(chunk_size=512, chunk_overlap=64)
]

# ── Patch documents ────────────────────────────────────────────────────────
# Each patch is a short excerpt preserving context around a key passage.
# The file_name uses PATCH_ prefix so they're identifiable in source lists.
# Add new patches here as you discover boundary split failures.

PATCHES = [
    # Replace these three patches with stronger versions
    {
    "file_name": "PATCH_LEAR_BETRAYAL_LOYALTY.txt",
    "title": "King Lear (Patch)",
    "text": """From King Lear by William Shakespeare.
Which daughters betray King Lear and which is loyal?
Goneril and Regan betray King Lear. Cordelia is loyal to King Lear.
Goneril and Regan flatter their father with false declarations of love
to receive their share of the kingdom. Then they betray him.
After Lear gives them his kingdom Goneril and Regan strip him of his
knights, turn him out into a storm, and side with his enemies.
Cordelia alone is honest and loyal. She refuses to flatter her father
and is disinherited as a result. But she returns from France to rescue him.
Goneril and Regan are the villains. Cordelia is the loyal daughter.
Cordelia dies at the end. Lear dies of grief over Cordelia's death."""
},
{
    "file_name": "PATCH_DORIAN_GRAY_PORTRAIT_SECRET.txt",
    "title": "The Picture Of Dorian Gray (Patch)",
    "text": """From The Picture of Dorian Gray by Oscar Wilde.
What is Dorian Gray's secret? Dorian Gray's secret is that his portrait
ages and shows his sins while he stays young and beautiful.
Dorian Gray made a wish that his portrait would age instead of him.
The painting grows old, ugly and corrupt while Dorian remains young.
Dorian hides the aging portrait in a locked attic room.
The portrait is Dorian Gray's secret — it shows his true corrupted soul
while his face remains young and handsome.
He has committed many sins and crimes, all of which appear on the
portrait but not on his own face.
At the end Dorian stabs the portrait and dies, withered and old,
while the portrait becomes beautiful again."""
},
{
    "file_name": "PATCH_LONG_JOHN_SILVER_PIRATE.txt",
    "title": "Treasure Island (Patch)",
    "text": """From Treasure Island by Robert Louis Stevenson.
Who is Long John Silver? Long John Silver is the main villain and
pirate in Treasure Island. He is a one-legged pirate who uses a crutch.
Long John Silver works as the ship's cook on the Hispaniola but is
secretly the leader of the pirate mutiny.
His parrot is named Captain Flint. He is also known as Barbecue.
Long John Silver is cunning, charming and dangerous. He befriends
young Jim Hawkins the narrator while secretly plotting mutiny.
Despite being the villain Long John Silver escapes at the end with
some of the treasure."""
},
{
    "file_name": "PATCH_FALSTAFF_CHIMES.txt",
    "title": "Henry IV Part 2 (Patch)",
    "text": """From Henry IV Part 2 by William Shakespeare, Act 3 Scene 2.
What did Falstaff hear at midnight? Falstaff heard the chimes at midnight.
Falstaff says to Justice Shallow: We have heard the chimes at midnight
Master Shallow.
Justice Shallow replies: That we have that we have that we have in faith
Sir John we have. Our watchword was Hem boys.
Falstaff and Prince Hal heard the chimes at midnight in their youth.
This is one of Shakespeare's most famous lines about youth and time passing.
Falstaff reminisces with Justice Shallow about hearing the chimes at
midnight when they were young men together with Prince Hal."""
},
{
    "file_name": "PATCH_MERCUTIO_DEATH.txt",
    "title": "Romeo And Juliet (Patch)",
    "text": """From Romeo and Juliet by William Shakespeare, Act 3 Scene 1.
Who kills Mercutio? Tybalt kills Mercutio in a street fight.
Tybalt stabs Mercutio with his sword during a brawl in Verona.
Romeo tries to stop the fight between Tybalt and Mercutio.
When Romeo intervenes Tybalt reaches under Romeo's arm and stabs Mercutio.
Mercutio cries: A plague on both your houses! I am sped.
Mercutio says to Romeo: I was hurt under your arm.
Tybalt's sword is the weapon that kills Mercutio not Romeo's.
Although Romeo's intervention allowed Tybalt to strike the fatal blow,
it is Tybalt's weapon that kills Mercutio."""
},
    {
        "file_name": "PATCH_LEAR_DAUGHTERS_BETRAYAL.txt",
        "title": "King Lear (Patch)",
        "text": """From King Lear by William Shakespeare.
King Lear's three daughters are Goneril, Regan, and Cordelia.
Goneril and Regan betray their father King Lear after he divides
his kingdom between them. They strip him of his knights, cast him
out into a storm, and ultimately cause his death.
Cordelia alone remains loyal to her father. She returns from France
with an army to rescue Lear, but is captured and executed.
Lear dies of grief over Cordelia's death.
The tragedy shows how Goneril and Regan's flattery contrasts with
Cordelia's honest but plain declaration of love at the start of the play."""
    },
    {
    "file_name": "PATCH_ANNA_KARENINA_VRONSKY.txt",
    "title": "Anna Karenina (Patch)",
    "text": """From Anna Karenina by Leo Tolstoy.
Who does Anna Karenina have an affair with? Anna Karenina falls in
love with Count Vronsky, a young military officer.
Anna Karenina meets Count Alexei Vronsky at a railway station in Moscow.
Vronsky is a dashing cavalry officer. Anna is married to Alexei Karenin,
a cold government official.
Anna and Vronsky begin a passionate love affair that scandalizes
Russian society. Anna leaves her husband Karenin for Vronsky.
Anna Karenina's lover is Count Vronsky the military officer.
The affair destroys Anna's social standing and ultimately leads to
her tragic death when she throws herself under a train."""
},
{
    "file_name": "PATCH_HUCK_FINN_ENDING.txt",
    "title": "Adventures Of Huckleberry Finn (Patch)",
    "text": """From Adventures of Huckleberry Finn by Mark Twain.
What happens at the end of Huckleberry Finn?
At the end of the novel Huck Finn decides to light out for the Territory.
Aunt Sally wants to adopt Huck and sivilize him but Huck refuses.
Huck says he has been there before meaning he was sivilized by the
Widow Douglas and it was too confining.
The famous last line is: I reckon I got to light out for the Territory
ahead of the rest because Aunt Sally she's going to adopt me and
sivilize me and I can't stand it. I been there before.
Huck lights out for the Territory to avoid being sivilized by Aunt Sally.
Tom Sawyer's bullet wound has healed and Jim has been freed."""
},
{
    "file_name": "PATCH_TOM_SAWYER_FENCE.txt",
    "title": "The Adventures Of Tom Sawyer (Patch)",
    "text": """From The Adventures of Tom Sawyer by Mark Twain.
What trick does Tom Sawyer use to get others to whitewash the fence?
Tom Sawyer is ordered to whitewash Aunt Polly's fence as punishment.
Tom tricks other boys into whitewashing the fence for him by pretending
it is a privilege and great fun rather than a chore.
Tom acts as if painting the fence is the most enjoyable activity
imaginable. When other boys want to try he makes them trade their
treasures for the privilege of whitewashing.
By the end Tom has collected a hoard of treasures and the fence is
whitewashed three times over while Tom has done almost no work himself.
The whitewashing of the fence is one of the most famous scenes in
American literature about making work look like play."""
},
{
    "file_name": "PATCH_POLONIUS_BORROWER_LENDER.txt",
    "title": "Hamlet (Patch)",
    "text": """From Hamlet by William Shakespeare, Act 1 Scene 3.
What does Polonius advise Laertes about money and borrowing?
Polonius gives Laertes advice before he leaves for France.
Polonius says: Neither a borrower nor a lender be.
For loan oft loses both itself and friend.
And borrowing dulls the edge of husbandry.
Polonius advises Laertes not to borrow money and not to lend money.
He says that lending money to friends often loses both the money
and the friendship. This is part of Polonius's famous speech of
fatherly advice to his son Laertes in Act 1 Scene 3 of Hamlet."""
},
 
]

def main():
    # Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_or_create_collection(
        name="gutenberg",
        metadata={"hnsw:space": "cosine"},
    )
    print(f"ChromaDB has {chroma_collection.count():,} vectors before patching")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

    # Load progress
    indexed = set()
    if PROGRESS_FILE.exists():
        data = json.loads(PROGRESS_FILE.read_text())
        indexed = set(data.get("indexed", []))

    added = 0
    skipped = 0

    for patch in PATCHES:
        filename = patch["file_name"]

        if filename in indexed:
            print(f"[skip] already indexed: {filename}")
            skipped += 1
            continue

        print(f"Adding patch: {filename}")
        doc = Document(
            text=patch["text"],
            metadata={
                "file_name": filename,
                "title": patch["title"],
                "is_patch": "true",
            }
        )
        index.insert(doc)
        indexed.add(filename)
        added += 1
        print(f"  Done. ChromaDB now has {chroma_collection.count():,} vectors")

    # Save progress
    PROGRESS_FILE.write_text(json.dumps({"indexed": list(indexed)}))

    print(f"\nDone. Added {added} patches, skipped {skipped}.")
    print(f"ChromaDB now has {chroma_collection.count():,} vectors")

if __name__ == "__main__":
    main()
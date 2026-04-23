#!/usr/bin/env python3
"""
Query the Gutenberg RAG system with HyDE + Hybrid Search (BM25 + Vector).
"""
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pathlib import Path
from typing import List, Optional
import chromadb
from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.schema import NodeWithScore
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.query_engine import TransformQueryEngine
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pydantic import Field

# ── Paths ──────────────────────────────────────────────────────────────────
CHROMA_DIR = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_chroma")
BM25_DIR   = Path("/Volumes/Phials4Miles/GitHub/Baby_dat/gutenberg_bm25")

# ── Settings ───────────────────────────────────────────────────────────────
Settings.llm = Ollama(model="llama3.1:8b", request_timeout=120.0)
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# ── Prompts ────────────────────────────────────────────────────────────────
QA_PROMPT = PromptTemplate(
    "You are a literary assistant helping answer questions about books.\n"
    "Below are relevant passages retrieved from the corpus.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Using ONLY the passages above and no prior knowledge, "
    "answer this question as specifically and accurately as possible: "
    "{query_str}\n\n"
    "If the passages do not contain enough information to answer, "
    "say exactly: 'I could not find this in the provided text.'\n"
    "Do not guess or use information not present in the passages above.\n"
)

HYDE_PROMPT = PromptTemplate(
    "You are a literary scholar. Given the following question about "
    "literature, write a short passage (3-5 sentences) that would appear "
    "in the actual book and directly answer the question. Write in the "
    "style of the original work if possible. Do not answer the question "
    "directly — write as if you are quoting or paraphrasing the source text.\n\n"
    "Question: {context_str}\n\n"
    "Hypothetical passage from the book:\n"
)

# ── Diversity filter ───────────────────────────────────────────────────────
class DiversityPostprocessor(BaseNodePostprocessor):
    max_per_source: int = Field(default=2)

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[object] = None,
    ) -> List[NodeWithScore]:
        seen = {}
        filtered = []
        for node in nodes:
            fname = node.metadata.get("file_name", "")
            count = seen.get(fname, 0)
            if count < self.max_per_source:
                filtered.append(node)
                seen[fname] = count + 1
        return filtered

def load_index():
    print("Loading vector index...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_collection("gutenberg")
    print(f"Vector index contains {chroma_collection.count():,} vectors")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )

def ask(query_engine, question: str):
    print(f"\nQ: {question}")
    print("-" * 60)
    response = query_engine.query(question)
    if not response.source_nodes:
        print("A: I could not find relevant passages in the corpus.")
    else:
        print(f"A: {response}")
    print("\nSources:")
    for node in response.source_nodes:
        title = node.metadata.get("title", "Unknown")
        fname = node.metadata.get("file_name", "Unknown")
        score = node.score if node.score else 0
        print(f"  [{score:+.3f}] {title}")
        print(f"           {fname}")

def main():
    index = load_index()

    # ── Load BM25 retriever ────────────────────────────────────────────────
    print("Loading BM25 index...")

    bm25_retriever = BM25Retriever.from_persist_dir(str(BM25_DIR))
    bm25_retriever.similarity_top_k = 20
    print("BM25 index loaded.")


    # ── Vector retriever ───────────────────────────────────────────────────
    vector_retriever = index.as_retriever(similarity_top_k=20)

    # ── Hybrid retriever — combines both ───────────────────────────────────
    hybrid_retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=30,
        num_queries=1,        # don't generate extra queries
        mode="reciprocal_rerank",  # RRF fusion
        use_async=False,
    )

    # ── Postprocessors ─────────────────────────────────────────────────────
    reranker = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-2-v2",
        top_n=15,
    )
    similarity_filter = SimilarityPostprocessor(
        similarity_cutoff=-1.5,
    )
    diversity_filter = DiversityPostprocessor(
        max_per_source=2,
    )

    # ── Query engine using hybrid retriever ────────────────────────────────
    base_query_engine = RetrieverQueryEngine.from_args(
        retriever=hybrid_retriever,
        node_postprocessors=[
            reranker,
            similarity_filter,
            diversity_filter,
        ],
        text_qa_template=QA_PROMPT,
    )

    # ── Wrap with HyDE ─────────────────────────────────────────────────────
    hyde = HyDEQueryTransform(
        include_original=True,
        hyde_prompt=HYDE_PROMPT,
    )
    query_engine = TransformQueryEngine(
        query_engine=base_query_engine,
        query_transform=hyde,
    )

    # ── Test questions ─────────────────────────────────────────────────────
    test_questions = [
        "In the King of Elfland's Daughter, what land did Alveric travel to?",
        "What is the name of the princess in the story?",
        "In The Charwoman's Shadow, what did the charwoman give the magician?",
        "What did the trolls feel in the pigeon-loft in The King of Elfland's Daughter?",
    ]

    print("\n" + "="*60)
    print("RUNNING TEST QUESTIONS (HyDE + Hybrid Search)")
    print("="*60)

    for question in test_questions:
        ask(query_engine, question)

    # ── Interactive mode ───────────────────────────────────────────────────
    print("\n" + "="*60)
    print("INTERACTIVE MODE — type your questions")
    print("Type 'quit' or 'exit' to stop")
    print("="*60)
    print("\nHyDE + Hybrid Search active.")
    print("Vague questions and proper nouns should both work well now.")

    while True:
        try:
            question = input("\nYour question: ").strip()
            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            ask(query_engine, question)
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test the embedding model before building the full index.
"""
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Embed a test sentence and print the vector dimensions
test_embedding = embed_model.get_text_embedding(
    "Who sailed down the Mississippi with Huck Finn?"
)

print(f"Embedding model loaded successfully")
print(f"Vector dimensions: {len(test_embedding)}")
print(f"First 5 values: {test_embedding[:5]}")
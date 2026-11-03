import os
import sys
import time

# Set offline variables before importing torch or transformers
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

t0 = time.time()
print("Importing sentence_transformers...")
from sentence_transformers import SentenceTransformer, CrossEncoder
print(f"Imported in {time.time() - t0:.2f}s")

t1 = time.time()
print("Loading embedding model with local_files_only=True...")
emb = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
print(f"Loaded embedding model in {time.time() - t1:.2f}s")

t2 = time.time()
print("Loading cross encoder with local_files_only=True...")
ce = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", local_files_only=True)
print(f"Loaded cross encoder in {time.time() - t2:.2f}s")

print("All loaded successfully!")

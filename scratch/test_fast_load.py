import os
import sys

# Set offline environment variables BEFORE importing transformers or sentence_transformers
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import time
t0 = time.time()
print("Starting fast load test...", flush=True)

from sentence_transformers import SentenceTransformer
print(f"Imported sentence_transformers in {time.time() - t0:.2f}s", flush=True)

t1 = time.time()
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print(f"Loaded embedding model in {time.time() - t1:.2f}s", flush=True)

vec = model.encode(["test query"])
print(f"Encoded test query, shape: {vec.shape}", flush=True)
print("SUCCESS!", flush=True)

import os, sys, time

print("1. Setting env vars...", flush=True)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

print("2. Importing torch...", flush=True)
t = time.time()
try:
    import torch
    print(f"   Torch imported in {time.time()-t:.2f}s", flush=True)
except Exception as e:
    print(f"   Torch import failed: {e}", flush=True)

print("3. Importing transformers...", flush=True)
t = time.time()
try:
    import transformers
    print(f"   Transformers imported in {time.time()-t:.2f}s", flush=True)
except Exception as e:
    print(f"   Transformers import failed: {e}", flush=True)

print("4. Importing sentence_transformers...", flush=True)
t = time.time()
try:
    import sentence_transformers
    print(f"   Sentence_transformers imported in {time.time()-t:.2f}s", flush=True)
except Exception as e:
    print(f"   Sentence_transformers import failed: {e}", flush=True)

print("5. Done!", flush=True)

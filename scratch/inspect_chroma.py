import sys
from pathlib import Path
from collections import Counter
import chromadb

backend_dir = Path("backend")
db_dir = backend_dir / "chroma_db"
client = chromadb.PersistentClient(path=str(db_dir))
coll = client.get_collection("tb_guidelines")

total = coll.count()
print(f"Total chunks in collection: {total}")

# Get all metadatas to check distribution
data = coll.get(include=["metadatas"])
metadatas = data["metadatas"]

years = Counter(str(m.get("year")) for m in metadatas)
sources = Counter(str(m.get("source")) for m in metadatas)
methods = Counter(str(m.get("method")) for m in metadatas)

print("\n--- Year distribution ---")
for y, count in sorted(years.items()):
    print(f"Year {y}: {count} chunks")

print("\n--- Source document distribution ---")
for s, count in sorted(sources.items()):
    print(f"{s}: {count} chunks")

print("\n--- Extraction methods ---")
for meth, count in sorted(methods.items()):
    print(f"{meth}: {count} chunks")

print("\nSample metadata 0:", metadatas[0])

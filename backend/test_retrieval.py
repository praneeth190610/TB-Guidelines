
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

BACKEND_DIR = Path(__file__).resolve().parent
DB_DIR = BACKEND_DIR / "chroma_db"

COLLECTION_NAME = "tb_guidelines"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Connecting to existing database...")
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_collection(COLLECTION_NAME)

print("Database connected!")
print("Stored chunks:", collection.count())


def search_guidelines(query, top_k=5):

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    # Retrieve more candidates than required
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=min(30, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    candidates = []

    for i, document in enumerate(results["documents"][0]):

        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        # Remove very short, low-information chunks
        if len(document.strip()) < 120:
            continue

        # Require a reasonable amount of actual text
        alphabetic_chars = sum(c.isalpha() for c in document)

        if alphabetic_chars < 70:
            continue

        candidates.append({
            "text": document,
            "metadata": metadata,
            "distance": distance
        })

    # Sort by semantic similarity
    candidates.sort(key=lambda x: x["distance"])

    print("\nQUESTION:", query)
    print("=" * 75)

    if not candidates:
        print("No useful results found.")
        return

    for i, item in enumerate(candidates[:top_k]):

        print(f"\nRESULT {i + 1}")
        print("Year:", item["metadata"]["year"])
        print("Source:", item["metadata"]["source"])
        print("Page:", item["metadata"]["page"])
        print("Distance:", round(item["distance"], 4))
        print("Text:\n", item["text"][:1000])


questions = [
    "What are the recommendations for drug-resistant tuberculosis?",
    "What treatment regimens are recommended for MDR-TB?",
    "What are the recommendations for monitoring patients during treatment?"
]

for question in questions:
    search_guidelines(question)

print("\nIMPROVED RETRIEVAL TEST COMPLETED!")

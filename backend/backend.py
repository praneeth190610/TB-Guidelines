
from pathlib import Path
import re
import json
import hashlib

import pymupdf
import numpy as np
import cv2
from rapidocr_onnxruntime import RapidOCR
from sentence_transformers import SentenceTransformer
import chromadb


# ============================================================
# 1. PROJECT PATHS AND SETTINGS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

BACKEND_DIR = Path(__file__).resolve().parent
DB_DIR = BACKEND_DIR / "chroma_db"
OUTPUT_FILE = BACKEND_DIR / "extracted_pages.jsonl"

YEARS = ["2016", "2017", "2021", "2025"]

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
BATCH_SIZE = 32

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "tb_guidelines"


# ============================================================
# 2. INITIALIZE OCR AND EMBEDDING MODEL
# ============================================================

def initialize_models():
    print("\nLoading OCR engine...")
    ocr_engine = RapidOCR()

    print("Loading embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("Models loaded successfully.")

    return ocr_engine, embedding_model


# ============================================================
# 3. OCR FOR PAGES WITHOUT SELECTABLE TEXT
# ============================================================

def perform_ocr(page, ocr_engine):
    try:
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
            alpha=False
        )

        image = np.frombuffer(
            pix.samples,
            dtype=np.uint8
        ).reshape(pix.height, pix.width, pix.n)

        if pix.n == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        result, _ = ocr_engine(image)

        if not result:
            return ""

        extracted_lines = []

        for item in result:
            if len(item) >= 2:
                recognized_text = str(item[1]).strip()

                if recognized_text:
                    extracted_lines.append(recognized_text)

        return "\n".join(extracted_lines)

    except Exception as error:
        print(f"    OCR warning: {error}")
        return ""


# ============================================================
# 4. TEXT CLEANING
# ============================================================

def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# 5. SPLIT TEXT INTO OVERLAPPING CHUNKS
# ============================================================

def create_chunks(text):
    chunks = []

    text = clean_text(text)

    if not text:
        return chunks

    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start, end)

            if boundary > start + CHUNK_SIZE // 2:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - CHUNK_OVERLAP, start + 1)

    return chunks


# ============================================================
# 6. EXTRACT TEXT FROM ALL FOUR YEARS
# ============================================================

def extract_all_documents(ocr_engine):
    all_chunks = []
    page_records = []

    for year in YEARS:
        year_folder = DATA_DIR / year

        print("\n" + "=" * 65)
        print(f"PROCESSING YEAR: {year}")
        print("=" * 65)

        if not year_folder.exists():
            print(f"Folder not found: {year_folder}")
            continue

        pdf_files = sorted(year_folder.rglob("*.pdf"))

        if not pdf_files:
            print("No PDF files found.")
            continue

        for pdf_path in pdf_files:
            print(f"\nOpening: {pdf_path.name}")

            try:
                with pymupdf.open(pdf_path) as document:

                    total_pages = len(document)
                    print(f"Total pages: {total_pages}")

                    for page_index, page in enumerate(document):

                        page_number = page_index + 1

                        text = page.get_text("text").strip()
                        extraction_method = "PDF text"

                        if not text:
                            print(
                                f"  OCR: page {page_number}/{total_pages}"
                            )

                            text = perform_ocr(page, ocr_engine)
                            extraction_method = "OCR"

                        text = clean_text(text)

                        record = {
                            "year": year,
                            "source": pdf_path.name,
                            "page": page_number,
                            "method": extraction_method,
                            "text": text
                        }

                        page_records.append(record)

                        if not text:
                            continue

                        chunks = create_chunks(text)

                        for chunk_index, chunk in enumerate(chunks):

                            unique_string = (
                                f"{year}|{pdf_path.name}|"
                                f"{page_number}|{chunk_index}"
                            )

                            chunk_id = hashlib.sha256(
                                unique_string.encode("utf-8")
                            ).hexdigest()

                            all_chunks.append({
                                "id": chunk_id,
                                "text": chunk,
                                "metadata": {
                                    "year": year,
                                    "source": pdf_path.name,
                                    "page": page_number,
                                    "chunk_index": chunk_index,
                                    "method": extraction_method
                                }
                            })

                print(f"Completed: {pdf_path.name}")

            except Exception as error:
                print(f"ERROR processing {pdf_path.name}: {error}")

    # Save extracted page-level text for later verification
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        for record in page_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("\nPAGE EXTRACTION SUMMARY")
    print(f"Total pages processed: {len(page_records)}")
    print(f"Pages with text: {sum(bool(p['text']) for p in page_records)}")
    print(f"Pages without extracted text: {sum(not bool(p['text']) for p in page_records)}")
    print(f"Total chunks created: {len(all_chunks)}")

    return all_chunks


# ============================================================
# 7. CREATE CHROMADB VECTOR DATABASE
# ============================================================

def create_vector_database(chunks, embedding_model):

    if not chunks:
        raise RuntimeError(
            "No text chunks were created. Check PDF extraction."
        )

    print("\nCreating ChromaDB database...")

    DB_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Rebuild the collection on each full pipeline run
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "TB guideline knowledge base"}
    )

    total = len(chunks)

    for start in range(0, total, BATCH_SIZE):

        batch = chunks[start:start + BATCH_SIZE]

        texts = [item["text"] for item in batch]

        embeddings = embedding_model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        collection.add(
            ids=[item["id"] for item in batch],
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=[item["metadata"] for item in batch]
        )

        print(
            f"Stored {min(start + BATCH_SIZE, total)} / {total} chunks"
        )

    print("\nVector database created successfully.")
    print(f"Total stored chunks: {collection.count()}")

    return collection


# ============================================================
# 8. SEARCH THE GUIDELINE DATABASE
# ============================================================

def search_guidelines(query, embedding_model, top_k=5, year=None):

    client = chromadb.PersistentClient(path=str(DB_DIR))

    collection = client.get_collection(COLLECTION_NAME)

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True
    )

    filters = {"year": year} if year else None

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=min(top_k, collection.count()),
        where=filters,
        include=["documents", "metadatas", "distances"]
    )

    print("\nSEARCH RESULTS")
    print("=" * 65)

    for index, text in enumerate(results["documents"][0]):

        metadata = results["metadatas"][0][index]
        distance = results["distances"][0][index]

        print(f"\nResult {index + 1}")
        print(f"Year: {metadata['year']}")
        print(f"Document: {metadata['source']}")
        print(f"Page: {metadata['page']}")
        print(f"Distance: {distance:.4f}")
        print(f"Text: {text[:500]}...")


# ============================================================
# 9. MAIN EXECUTION
# ============================================================

def main():

    print("\n" + "=" * 65)
    print("INTELLIGENT TB GUIDELINE ANALYSIS")
    print("INTEGRATED DOCUMENT PROCESSING PIPELINE")
    print("=" * 65)

    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Data folder not found: {DATA_DIR}"
        )

    ocr_engine, embedding_model = initialize_models()

    chunks = extract_all_documents(ocr_engine)

    collection = create_vector_database(
        chunks,
        embedding_model
    )

    print("\n" + "=" * 65)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 65)

    print(f"Indexed chunks: {collection.count()}")
    print(f"Extracted text: {OUTPUT_FILE}")
    print(f"Vector database: {DB_DIR}")

    print("\nTesting the search system...")

    search_guidelines(
        "What are the recommendations for drug-resistant tuberculosis?",
        embedding_model,
        top_k=5
    )


if __name__ == "__main__":
    main()

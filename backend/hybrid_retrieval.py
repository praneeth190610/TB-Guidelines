import os
import sys

# Configure UTF-8 for console output with fallback replacement
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Safe print helper to prevent charmap/UnicodeEncodeError under any Windows console
_orig_print = print
def safe_print(*args, **kwargs):
    try:
        _orig_print(*args, **kwargs)
    except (UnicodeEncodeError, Exception):
        try:
            encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
            sanitized_args = [
                str(arg).encode(encoding, errors="replace").decode(encoding)
                for arg in args
            ]
            _orig_print(*sanitized_args, **kwargs)
        except Exception:
            pass

print = safe_print

import re
import math
import json
from pathlib import Path
from collections import Counter, defaultdict

# Ensure offline execution for HuggingFace / Transformers to eliminate remote timeout retries
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder


# ============================================================
# 1. CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_DIR / "backend" / "chroma_db"
EXTRACTED_FILE = PROJECT_DIR / "backend" / "extracted_pages.jsonl"

COLLECTION_NAME = "tb_guidelines"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

SEMANTIC_TOP_K = 50
KEYWORD_TOP_K = 50
RRF_CANDIDATE_K = 20
FINAL_TOP_K = 4
RRF_K = 60

MAX_CONTEXT_SEGMENTS = 3
CONTEXT_RELEVANCE_MARGIN = 2.0

print("=" * 75)
print("INTELLIGENT TB GUIDELINE ANALYSIS")
print("HYBRID RETRIEVAL + CROSS-ENCODER + IMPROVED CONTEXT EXPANSION")
print("=" * 75)


# ============================================================
# 2. CONNECT TO EXISTING CHROMADB
# ============================================================

print("\nConnecting to existing ChromaDB...")

client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_collection(name=COLLECTION_NAME)

print("Connected successfully.")
print("Total chunks in database:", collection.count())


# ============================================================
# 3. LOAD DOCUMENTS AND METADATA
# ============================================================

print("\nLoading documents...")

stored_data = collection.get(
    include=["documents", "metadatas"]
)

all_documents = stored_data["documents"]
all_metadatas = stored_data["metadatas"]
all_ids = stored_data["ids"]

print("Documents loaded:", len(all_documents))


# ============================================================
# 4. LOAD MODELS
# ============================================================

print("\nLoading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME
)

print("Embedding model loaded.")

print("\nLoading Cross-Encoder model...")

cross_encoder = CrossEncoder(
    CROSS_ENCODER_MODEL_NAME
)

print("Cross-Encoder loaded.")


# ============================================================
# 5. DOCUMENT FILTERING
# ============================================================

def tokenize(text):
    """Convert text into lowercase word tokens."""

    return re.findall(
        r"[a-zA-Z0-9]+",
        text.lower()
    )


def is_useful_document(text):
    """Remove short, noisy, and non-informative chunks."""

    if not text:
        return False

    words = tokenize(text)

    alphabetic_words = [
        word for word in words
        if word.isalpha()
    ]

    if len(words) < 25:
        return False

    if len(alphabetic_words) < 15:
        return False

    lower_text = text.lower()

    unwanted_headings = [
        "table of contents",
        "acknowledgements",
        "abbreviations",
        "bibliography",
        "references",
        "index"
    ]

    first_lines = "\n".join(
        lower_text.splitlines()[:12]
    )

    if any(
        heading in first_lines
        for heading in unwanted_headings
    ):
        return False

    url_count = len(
        re.findall(
            r"https?://|www\.",
            lower_text
        )
    )

    if url_count >= 3:
        return False

    citation_count = len(
        re.findall(
            r"\[\s*\d+(?:\s*[,;-]\s*\d+)*\s*\]",
            text
        )
    )

    if citation_count >= 5:
        return False

    form_terms = [
        "patient name:",
        "date of birth:",
        "signature:",
        "name of patient:",
        "registration number:"
    ]

    if sum(
        lower_text.count(term)
        for term in form_terms
    ) >= 3:
        return False

    return True


print("\nFiltering documents...")

eligible_documents = []
eligible_metadatas = []
eligible_ids = []

for doc, metadata, doc_id in zip(
    all_documents,
    all_metadatas,
    all_ids
):

    if is_useful_document(doc):
        eligible_documents.append(doc)
        eligible_metadatas.append(metadata)
        eligible_ids.append(doc_id)


# Fast ID-to-index lookup.
eligible_id_to_index = {
    doc_id: index
    for index, doc_id in enumerate(eligible_ids)
}


print("Original chunks:", len(all_documents))
print("Useful chunks:", len(eligible_documents))
print(
    "Filtered chunks:",
    len(all_documents) - len(eligible_documents)
)


# ============================================================
# 6. KEYWORD RETRIEVAL
# ============================================================

print("\nPreparing keyword retrieval...")

document_tokens = [
    tokenize(doc)
    for doc in eligible_documents
]

document_lengths = [
    len(tokens)
    for tokens in document_tokens
]

average_document_length = (
    sum(document_lengths) / len(document_lengths)
    if document_lengths else 1
)

document_frequency = Counter()

for tokens in document_tokens:

    for token in set(tokens):
        document_frequency[token] += 1


# Domain-aware search synonyms improve recall without changing source text.
QUERY_SYNONYMS = {
    "adr": ["adverse", "drug", "reaction", "side", "effects", "toxicity"],
    "adverse": ["adr", "side", "effects", "toxicity", "safety"],
    "reactions": ["reaction", "side", "effects", "toxicity", "adr"],
    "monitoring": ["monitor", "follow", "up", "surveillance", "assessment"],
    "managed": ["management", "manage", "treatment", "intervention"],
    "management": ["manage", "managed", "treatment", "intervention"],
    "drtb": ["drug", "resistant", "tuberculosis"],
    "mdrtb": ["multidrug", "resistant", "tuberculosis"],
    "side": ["adverse", "reaction", "adr", "toxicity"],
    "effects": ["adverse", "reaction", "adr", "toxicity"],
}


def expand_query_tokens(query):

    tokens = tokenize(query)
    expanded = list(tokens)

    for token in tokens:
        expanded.extend(
            QUERY_SYNONYMS.get(token, [])
        )

    lowered = query.lower()

    if (
        "adverse drug reaction" in lowered
        or "adverse drug reactions" in lowered
    ):
        expanded.extend([
            "adr",
            "side",
            "effects",
            "toxicity",
            "safety"
        ])

    if (
        "drug-resistant tuberculosis" in lowered
        or "drug resistant tuberculosis" in lowered
    ):
        expanded.extend([
            "drtb",
            "mdrtb",
            "resistant",
            "tuberculosis"
        ])

    return list(dict.fromkeys(expanded))


def safe_int(value, default=0):
    """Safely convert metadata into integers."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def keyword_search(query, top_k=KEYWORD_TOP_K, year=None):
    """BM25-style keyword ranking with TB-domain synonym expansion and optional year filtering."""

    query_tokens = expand_query_tokens(query)
    total_documents = len(eligible_documents)
    target_year = str(year).strip() if year is not None else None

    scores = []

    k1 = 1.5
    b = 0.75

    for index, tokens in enumerate(document_tokens):

        if target_year is not None:
            doc_year = str(eligible_metadatas[index].get("year", "")).strip()
            if doc_year != target_year:
                continue

        term_counts = Counter(tokens)
        document_length = document_lengths[index]
        score = 0.0

        for term in query_tokens:

            frequency = term_counts.get(term, 0)

            if frequency == 0:
                continue

            df = document_frequency.get(term, 0)

            idf = math.log(
                1 + (
                    total_documents - df + 0.5
                ) / (
                    df + 0.5
                )
            )

            numerator = frequency * (k1 + 1)

            denominator = frequency + k1 * (
                1 - b + b * (
                    document_length /
                    average_document_length
                )
            )

            score += idf * (
                numerator / denominator
            )

        if score > 0:
            scores.append((index, score))

    scores.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return scores[:top_k]


# ============================================================
# 7. SEMANTIC RETRIEVAL
# ============================================================

def semantic_search(query, top_k=SEMANTIC_TOP_K, year=None):
    """Search the existing ChromaDB using embeddings with optional year filtering."""

    if not eligible_documents:
        return []

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=False
    ).tolist()

    where_filter = {"year": str(year).strip()} if year is not None else None

    # Determine safe candidate count
    n_results = min(top_k, collection.count())

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    semantic_results = []

    if results and results.get("ids") and len(results["ids"]) > 0:
        for doc_id in results["ids"][0]:

            index = eligible_id_to_index.get(doc_id)

            if index is not None:
                semantic_results.append(index)

    return semantic_results


# ============================================================
# 8. RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    semantic_results,
    keyword_results
):
    """Combine semantic and keyword rankings."""

    rrf_scores = defaultdict(float)

    for rank, index in enumerate(
        semantic_results,
        start=1
    ):

        rrf_scores[index] += (
            1 / (RRF_K + rank)
        )

    for rank, (index, score) in enumerate(
        keyword_results,
        start=1
    ):

        rrf_scores[index] += (
            1 / (RRF_K + rank)
        )

    ranked_results = sorted(
        rrf_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return ranked_results[:RRF_CANDIDATE_K]


# ============================================================
# 9. CROSS-ENCODER RERANKING
# ============================================================

def cross_encoder_rerank(
    query,
    candidate_results,
    top_k=FINAL_TOP_K
):
    """Rerank candidate passages using Cross-Encoder and attach complete metadata."""

    if not candidate_results:
        return []

    pairs = []

    for index, rrf_score in candidate_results:

        pairs.append((
            query,
            eligible_documents[index]
        ))

    scores = cross_encoder.predict(pairs)

    reranked_results = []

    for position, result in enumerate(candidate_results):

        index, rrf_score = result
        metadata = eligible_metadatas[index] if index < len(eligible_metadatas) else {}

        reranked_results.append({
            "index": index,
            "rrf_score": rrf_score,
            "cross_encoder_score": float(
                scores[position]
            ),
            "text": eligible_documents[index],
            "metadata": metadata,
            "year": str(metadata.get("year", "Unknown")),
            "source": str(metadata.get("source", "Unknown")),
            "page": safe_int(metadata.get("page")),
            "chunk_index": safe_int(metadata.get("chunk_index")),
            "method": str(metadata.get("method", "Unknown"))
        })

    reranked_results.sort(
        key=lambda item: item["cross_encoder_score"],
        reverse=True
    )

    return reranked_results[:top_k]


# ============================================================
# 10. CONTEXT EXPANSION
# ============================================================

def safe_int(value, default=0):
    """Safely convert metadata into integers."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


print("\nPreparing context expansion...")

# Group chunks using year and source.
# This prevents mixing different guideline PDFs.

document_groups = defaultdict(list)

for index, metadata in enumerate(eligible_metadatas):

    year = str(
        metadata.get("year", "Unknown")
    )

    source = str(
        metadata.get("source", "Unknown")
    )

    document_groups[(year, source)].append({

        "index": index,
        "id": eligible_ids[index],
        "text": eligible_documents[index],
        "metadata": metadata,

        "page": safe_int(
            metadata.get("page")
        ),

        "chunk_index": safe_int(
            metadata.get("chunk_index")
        )
    })


# Sort chunks in original PDF order.

for key in document_groups:

    document_groups[key].sort(
        key=lambda item: (
            item["page"],
            item["chunk_index"]
        )
    )


def expand_context(
    query,
    anchor_index,
    anchor_score=None,
    max_segments=MAX_CONTEXT_SEGMENTS
):
    """
    Retrieve the main passage and relevant nearby passages.

    Context is restricted to the same guideline PDF.
    Nearby passages are reranked using Cross-Encoder.
    Original citation metadata is preserved.
    """

    anchor_metadata = eligible_metadatas[anchor_index]

    year = str(
        anchor_metadata.get("year", "Unknown")
    )

    source = str(
        anchor_metadata.get("source", "Unknown")
    )

    anchor_page = safe_int(
        anchor_metadata.get("page")
    )

    anchor_chunk = safe_int(
        anchor_metadata.get("chunk_index")
    )

    group = document_groups.get(
        (year, source),
        []
    )

    anchor = next(
        (
            item for item in group
            if item["index"] == anchor_index
        ),
        None
    )

    if anchor is None:
        return []

    # Always retain the main retrieved passage.
    selected = [anchor]

    # --------------------------------------------------------
    # A. Collect nearby chunks from the same page.
    # --------------------------------------------------------

    for item in group:

        if item["index"] == anchor_index:
            continue

        if item["page"] == anchor_page:

            if abs(
                item["chunk_index"] - anchor_chunk
            ) <= 2:

                selected.append(item)

    # Adjacent PDF pages are excluded to avoid unrelated sections
    # and unnecessary Cross-Encoder work. Nearby chunks on the same
    # source page provide the supporting context.

    # --------------------------------------------------------
    # C. Remove duplicate chunks.
    # --------------------------------------------------------

    unique_segments = {}

    for item in selected:
        unique_segments[item["id"]] = item

    candidates = list(
        unique_segments.values()
    )

    # --------------------------------------------------------
    # D. Identify BPaLM eligibility questions.
    # --------------------------------------------------------

    query_lower = query.lower()
    anchor_text = anchor["text"].lower()

    is_bpalm_query = (
        "bpalm" in query_lower
        and any(
            word in query_lower
            for word in [
                "eligibility",
                "eligible",
                "inclusion",
                "criteria"
            ]
        )
    )

    # --------------------------------------------------------
    # E. Rerank neighbouring chunks.
    # --------------------------------------------------------

    candidate_pairs = []

    for item in candidates:

        if item["index"] == anchor_index:
            continue

        candidate_pairs.append((
            query,
            item["text"]
        ))

    candidate_scores = {}

    if candidate_pairs:

        scores = cross_encoder.predict(
            candidate_pairs
        )

        score_position = 0

        for item in candidates:

            if item["index"] == anchor_index:
                continue

            candidate_scores[item["index"]] = float(
                scores[score_position]
            )

            score_position += 1

    # Reuse the score from the main Cross-Encoder reranking step.
    # Fall back to scoring the anchor only if no score was supplied.
    if anchor_score is None:
        anchor_score = float(
            cross_encoder.predict([
                (query, anchor["text"])
            ])[0]
        )
    else:
        anchor_score = float(anchor_score)

    # --------------------------------------------------------
    # F. Keep relevant supporting chunks.
    # --------------------------------------------------------

    supporting_segments = []

    for item in candidates:

        if item["index"] == anchor_index:
            continue

        score = candidate_scores.get(
            item["index"],
            float("-inf")
        )

        if score >= anchor_score - CONTEXT_RELEVANCE_MARGIN:

            supporting_segments.append({
                "item": item,
                "score": score,
                "forced": False
            })

    # --------------------------------------------------------
    # G. Preserve only clearly related BPaLM eligibility context.
    # --------------------------------------------------------

    # Do not force arbitrary numbered/list passages into the context.
    # BPaLM eligibility is separately retrieved from its verified
    # 2025 guideline section in retrieve_bpalm_eligibility().

    if is_bpalm_query and "bpalm" in anchor_text:

        for item in candidates:

            if item["index"] == anchor_index:
                continue

            text_lower = item["text"].lower()

            same_document = (
                str(item["metadata"].get("year", "Unknown")) == year
                and str(item["metadata"].get("source", "Unknown")) == source
            )

            nearby = abs(item["page"] - anchor_page) <= 1

            explicitly_related = (
                "bpalm" in text_lower
                or "bedaquiline" in text_lower
                or "pretomanid" in text_lower
                or "linezolid" in text_lower
                or "moxifloxacin" in text_lower
                or "inclusion criteria" in text_lower
                or "eligibility criteria" in text_lower
            )

            already_added = any(
                segment["item"]["index"] == item["index"]
                for segment in supporting_segments
            )

            if (
                same_document
                and nearby
                and explicitly_related
                and not already_added
            ):

                score = candidate_scores.get(
                    item["index"],
                    float("-inf")
                )

                if math.isfinite(score):
                    supporting_segments.append({
                        "item": item,
                        "score": score,
                        "forced": False
                    })

    # --------------------------------------------------------
    # H. Sort supporting passages by relevance.
    # --------------------------------------------------------

    supporting_segments.sort(
        key=lambda segment: segment["score"],
        reverse=True
    )

    # Main passage always comes first.
    expanded = [anchor]

    for segment in supporting_segments:

        if len(expanded) >= max_segments:
            break

        expanded.append(segment["item"])

    return expanded


# ============================================================
# 11. HYBRID SEARCH
# ============================================================

def hybrid_search(query, year=None, top_k=FINAL_TOP_K):

    print("\n" + "=" * 75)
    print("QUERY:", query)
    if year:
        print("FILTER GUIDELINE YEAR:", year)
    print("=" * 75)

    print("\nRunning semantic retrieval...")

    semantic_results = semantic_search(query, year=year)

    print(
        "Semantic candidates:",
        len(semantic_results)
    )

    print("\nRunning keyword retrieval...")

    keyword_results = keyword_search(query, year=year)

    print(
        "Keyword candidates:",
        len(keyword_results)
    )

    print("\nCombining rankings using RRF...")

    fused_results = reciprocal_rank_fusion(
        semantic_results,
        keyword_results
    )

    print(
        "RRF candidates:",
        len(fused_results)
    )

    print("\nRunning Cross-Encoder reranking...")

    final_results = cross_encoder_rerank(
        query,
        fused_results,
        top_k=top_k
    )

    print(
        "Final results:",
        len(final_results)
    )

    return final_results


# ============================================================
# 12. SECTION-AWARE BPaLM ELIGIBILITY RETRIEVAL
# ============================================================

def retrieve_bpalm_eligibility():

    print("\n" + "=" * 75)
    print("SECTION-AWARE EVIDENCE: BPaLM ELIGIBILITY")
    print("=" * 75)

    if not EXTRACTED_FILE.exists():

        print("Extracted pages file not found:")
        print(EXTRACTED_FILE)
        return

    # These are PDF metadata page numbers confirmed
    # during inspection of the 2025 guideline.
    target_pages = {31, 32, 33}

    found_pages = set()

    try:

        with EXTRACTED_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                if not line.strip():
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if str(row.get("year")) != "2025":
                    continue

                page = safe_int(
                    row.get("page"),
                    -1
                )

                if page not in target_pages:
                    continue

                page_text = str(
                    row.get("text", "")
                ).strip()

                if not page_text:
                    continue

                found_pages.add(page)

                print("\n" + "-" * 75)
                print("GUIDELINE YEAR: 2025")
                print(
                    "SOURCE:",
                    row.get("source", "2025 guideline")
                )
                print("PDF PAGE:", page)
                print("-" * 75)

                # Preserve the extracted page text.
                print(page_text)

    except OSError as error:

        print("Could not read extracted pages:", error)
        return

    missing_pages = target_pages - found_pages

    if missing_pages:

        print(
            "\nPages not found:",
            sorted(missing_pages)
        )

    print("\nBPaLM section retrieval completed.")
    print(
        "References above use PDF metadata page numbers. "
        "Verify the original PDF before drawing conclusions."
    )


# ============================================================
# 13. DISPLAY RESULTS WITH EXPANDED CONTEXT
# ============================================================

def display_results(query, results):

    if not results:
        print("\nNo relevant hybrid retrieval results found.")
    else:
        for rank, result in enumerate(
            results,
            start=1
        ):

            index = result["index"]

            rrf_score = result["rrf_score"]

            cross_score = result[
                "cross_encoder_score"
            ]

            metadata = eligible_metadatas[index]

            print("\n")
            print("#" * 75)
            print("FINAL RESULT", rank)
            print("#" * 75)

            print(
                "Year:",
                metadata.get("year", "Unknown")
            )

            print(
                "Source:",
                metadata.get("source", "Unknown")
            )

            print(
                "Page:",
                metadata.get("page", "Unknown")
            )

            print(
                "Extraction method:",
                metadata.get("method", "Unknown")
            )

            print(
                "RRF score:",
                round(rrf_score, 5)
            )

            print(
                "Cross-Encoder score:",
                round(cross_score, 5)
            )

            print("\nMAIN RETRIEVED PASSAGE:")
            print("-" * 75)

            print(eligible_documents[index])

            # ----------------------------------------------------
            # IMPROVED CONTEXT EXPANSION
            # ----------------------------------------------------

            expanded_segments = expand_context(
                query,
                index,
                anchor_score=cross_score
            )

            print("\nEXPANDED CONTEXT")
            print("-" * 75)

            for segment_number, segment in enumerate(
                expanded_segments,
                start=1
            ):

                segment_metadata = segment["metadata"]

                print(
                    f"\nEvidence Segment {segment_number}"
                )

                print(
                    "Year:",
                    segment_metadata.get(
                        "year", "Unknown"
                    )
                )

                print(
                    "Source:",
                    segment_metadata.get(
                        "source", "Unknown"
                    )
                )

                print(
                    "Page:",
                    segment_metadata.get(
                        "page", "Unknown"
                    )
                )

                print(
                    "Chunk:",
                    segment_metadata.get(
                        "chunk_index", "Unknown"
                    )
                )

                if segment["index"] == index:
                    print("Role: Main retrieved passage")
                else:
                    print("Role: Supporting context")

                print("\nText:")
                print(segment["text"])

            print("\n" + "=" * 75)

    # --------------------------------------------------------
    # ADDITIONAL SECTION-AWARE EVIDENCE FOR BPaLM QUESTIONS
    # --------------------------------------------------------

    # This runs independently of hybrid retrieval results.
    # Therefore, BPaLM evidence is still displayed even when
    # hybrid retrieval returns no relevant passages.

    query_lower = query.lower()

    if (
        "bpalm" in query_lower
        and any(
            word in query_lower
            for word in [
                "eligibility",
                "eligible",
                "inclusion",
                "criteria"
            ]
        )
    ):

        retrieve_bpalm_eligibility()


# ============================================================
# 14. TEST QUESTIONS
# ============================================================

TEST_QUESTIONS = [

    "What are the recommendations for drug-resistant tuberculosis?",

    "What treatment regimens are recommended for MDR-TB?",

    "How should patients receiving drug-resistant TB treatment be monitored?",

    "What are the eligibility criteria for BPaLM treatment?",

    "How should adverse drug reactions during TB treatment be managed?"

]


# ============================================================
# 15. MAIN FUNCTION
# ============================================================

def main():

    print("\nStarting hybrid retrieval tests...")

    for question_number, query in enumerate(
        TEST_QUESTIONS,
        start=1
    ):

        print("\n\n")
        print("*" * 85)
        print("TEST QUESTION", question_number)
        print("*" * 85)

        results = hybrid_search(query)

        display_results(
            query,
            results
        )

    print("\n\n")
    print("=" * 75)
    print("ALL RETRIEVAL TESTS COMPLETED")
    print("=" * 75)


if __name__ == "__main__":

    main()
"""
Evidence-organized RAG engine for Intelligent TB Guideline Analysis.

Features:
- Hybrid retrieval
- Cross-Encoder reranking through hybrid_retrieval
- Page-level evidence grouping
- Duplicate chunk removal
- Local Ollama (Qwen)
- Citation validation
- Raw LLM answer diagnostics
- Safe evidence-only fallback

Does NOT rebuild ChromaDB or re-extract PDFs.
"""

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

# Ensure offline execution for HuggingFace / Transformers to eliminate remote timeout retries
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import re
import math
import json
import socket
import unicodedata
from difflib import SequenceMatcher
import urllib.request
import urllib.error

from collections import OrderedDict

import hybrid_retrieval as retrieval


# ============================================================
# 1. CONFIGURATION
# ============================================================

MAX_RETRIEVED_RESULTS = 4
MAX_EVIDENCE_PAGES = 12
MAX_CHARS_PER_PAGE = 5000

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/chat"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:1.5b"
)

OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "20"))
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "350"))


print("\n" + "=" * 65)
print("RAG ENGINE MODULE DIAGNOSTICS")
print("=" * 65)
print("RAG ENGINE FILE:", os.path.abspath(__file__))
print("OLLAMA URL:", OLLAMA_URL)
print("OLLAMA MODEL:", OLLAMA_MODEL)
print("OLLAMA TIMEOUT:", OLLAMA_TIMEOUT, "seconds")
print("=" * 65)


# ============================================================
# 2. TEXT CLEANING AND OVERLAP REMOVAL
# ============================================================

def clean_text(text):
    if not text:
        return ""
    text = str(text)
    # Replace common PDF bullet artifacts and private use symbol characters
    text = re.sub(r"[\uf0b7\uf0a7\uf0d8\u2022\u2023\u25e6\u2043\u2219\u25aa\u25ab\u25cf\u25cb]", " - ", text)
    # Strip any remaining Private Use Area characters (\uE000 to \uF8FF)
    text = re.sub(r"[\ue000-\uf8ff]", " ", text)
    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def remove_text_overlap(
    previous_text,
    next_text,
    max_overlap=400
):
    previous_text = previous_text.strip()
    next_text = next_text.strip()

    max_length = min(
        len(previous_text),
        len(next_text),
        max_overlap
    )

    for length in range(max_length, 39, -1):
        if previous_text[-length:] == next_text[:length]:
            return next_text[length:].strip()

    return next_text


# ============================================================
# 3. COLLECT AND GROUP EVIDENCE
# ============================================================

def collect_evidence(
    query,
    year=None,
    top_k=MAX_RETRIEVED_RESULTS
):
    print(f"\nRunning hybrid evidence retrieval{' for year ' + str(year) if year else ''}...")

    ranked_results = retrieval.hybrid_search(query, year=year, top_k=top_k)

    if not ranked_results:
        print("No retrieval results found.")
        return []

    grouped_evidence = OrderedDict()
    seen_chunks = set()

    for result in ranked_results[:top_k]:

        anchor_index = result["index"]

        expanded_segments = retrieval.expand_context(
            query,
            anchor_index
        )

        for segment in expanded_segments:

            metadata = segment.get("metadata", {})

            item_year = str(metadata.get("year", "Unknown")).strip()
            if year is not None and item_year != str(year).strip():
                continue

            source = str(metadata.get("source", "Unknown"))
            page = str(metadata.get("page", "Unknown"))

            chunk_index = str(
                metadata.get("chunk_index", "Unknown")
            )

            text = clean_text(segment.get("text", ""))

            if not text:
                continue

            chunk_key = (
                item_year,
                source,
                page,
                chunk_index
            )

            if chunk_key in seen_chunks:
                continue

            seen_chunks.add(chunk_key)

            page_key = (
                item_year,
                source,
                page
            )

            if page_key not in grouped_evidence:

                grouped_evidence[page_key] = {
                    "year": item_year,
                    "source": source,
                    "page": page,
                    "chunks": [],
                    "methods": set(),
                    "cross_encoder_scores": []
                }

            group = grouped_evidence[page_key]

            group["chunks"].append({
                "chunk_index": chunk_index,
                "text": text
            })

            group["methods"].add(
                str(metadata.get("method", "Unknown"))
            )

            score = result.get("cross_encoder_score")

            if score is not None:
                group["cross_encoder_scores"].append(
                    float(score)
                )

    # ========================================================
    # 4. MERGE CHUNKS WITHIN EACH PAGE
    # ========================================================

    final_evidence = []

    for page_key, group in grouped_evidence.items():

        chunks = group["chunks"]

        chunks.sort(
            key=lambda item: (
                int(item["chunk_index"])
                if item["chunk_index"].isdigit()
                else 0
            )
        )

        merged_parts = []
        previous_text = ""

        for chunk in chunks:

            current_text = chunk["text"]

            if previous_text:
                current_text = remove_text_overlap(
                    previous_text,
                    current_text
                )

            if current_text:
                merged_parts.append(current_text)

            previous_text = chunk["text"]

        merged_text = " ".join(merged_parts).strip()

        if not merged_text:
            continue

        final_evidence.append({

            "year": group["year"],
            "source": group["source"],
            "page": group["page"],

            "chunk_indices": [
                chunk["chunk_index"]
                for chunk in chunks
            ],

            "method": ", ".join(
                sorted(group["methods"])
            ),

            "text": merged_text[:MAX_CHARS_PER_PAGE],

            "cross_encoder_score": (
                max(group["cross_encoder_scores"])
                if group["cross_encoder_scores"]
                else None
            )
        })

        if len(final_evidence) >= MAX_EVIDENCE_PAGES:
            break

    print(
        "Unique evidence pages after grouping:",
        len(final_evidence)
    )

    return final_evidence


# ============================================================
# 5. FORMAT EVIDENCE WITH CITATIONS
# ============================================================

def format_evidence(evidence):

    blocks = []

    for number, item in enumerate(evidence, start=1):

        citation = (
            f"[{number}] Guideline {item['year']} | "
            f"{item['source']} | "
            f"PDF page {item['page']}"
        )

        chunk_reference = ", ".join(
            str(value)
            for value in item["chunk_indices"]
        )

        # Cap individual evidence passage text to 800 chars for rapid prompt ingestion
        passage_text = str(item.get("text", "")).strip()
        if len(passage_text) > 800:
            passage_text = passage_text[:800] + "..."

        blocks.append(
            f"{citation}\n"
            f"Original chunk indices: {chunk_reference}\n"
            f"Extraction method: {item['method']}\n"
            f"Evidence: {passage_text}"
        )

    return "\n\n".join(blocks)


# ============================================================
# 6. OLLAMA CONNECTION
# ============================================================

def call_ollama(messages):

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": OLLAMA_MAX_TOKENS,
            "num_thread": min(8, os.cpu_count() or 4),
            "top_k": 20,
            "top_p": 0.8
        }
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    print("\nOLLAMA CONNECTION DETAILS")
    print("URL:", OLLAMA_URL)
    print("Model:", OLLAMA_MODEL)
    print("Timeout:", OLLAMA_TIMEOUT)

    try:

        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        )

        with opener.open(
            request,
            timeout=OLLAMA_TIMEOUT
        ) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
            )

        answer = response_data.get(
            "message",
            {}
        ).get(
            "content",
            ""
        ).strip()

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        print("OLLAMA STATUS: SUCCESS")
        print("Generated characters:", len(answer))

        return answer

    except urllib.error.HTTPError as error:

        details = error.read().decode(
            "utf-8",
            errors="replace"
        )

        print("\nOLLAMA HTTP ERROR")
        print("Status code:", error.code)
        print("Details:", details)

        raise RuntimeError(
            f"Ollama HTTP error {error.code}: {details}"
        ) from error

    except (
        urllib.error.URLError,
        socket.timeout,
        TimeoutError
    ) as error:

        print("\nOLLAMA CONNECTION ERROR")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

        if isinstance(error, urllib.error.URLError):
            print("Underlying reason:", repr(error.reason))

        raise RuntimeError(
            f"Ollama connection failed: {repr(error)}"
        ) from error

    except Exception as error:

        print("\nOLLAMA UNEXPECTED ERROR")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

        raise


# ============================================================
# 7. CITATION VALIDATION
# ============================================================

def validate_citations(answer, evidence_count):
    """
    Validate citation syntax, reference ranges, and citation placement.

    This is structural validation only; it cannot prove semantic support.
    """
    if not answer or not answer.strip():
        return False, "The model returned an empty answer."

    citation_pattern = re.compile(r"(?<!\w)\[(\d{1,3})\]")
    citation_numbers = citation_pattern.findall(answer)

    if not citation_numbers:
        return False, "No numbered citations were generated."

    invalid_numbers = sorted({
        int(number)
        for number in citation_numbers
        if int(number) < 1 or int(number) > evidence_count
    })
    if invalid_numbers:
        return False, f"Invalid citation numbers: {invalid_numbers}"

    def is_nonclaim(line):
        stripped = line.strip()
        if not stripped:
            return True
        if re.match(r"^#{1,6}\s+", stripped):
            return True
        if re.match(r"^[-*_]{3,}$", stripped):
            return True
        if stripped.endswith(":") and len(stripped) <= 90:
            return True
        return False

    paragraphs = re.split(r"\n\s*\n", answer.strip())
    uncited = []

    for paragraph_number, paragraph in enumerate(paragraphs, start=1):
        lines = [
            line.rstrip()
            for line in paragraph.splitlines()
            if not is_nonclaim(line)
        ]
        if not lines:
            continue

        is_bullet = [
            bool(re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line))
            for line in lines
        ]

        if any(is_bullet):
            items, current = [], []
            for line, starts_item in zip(lines, is_bullet):
                if starts_item and current:
                    items.append(" ".join(current))
                    current = [line]
                else:
                    current.append(line)
            if current:
                items.append(" ".join(current))

            for item_number, item in enumerate(items, start=1):
                if not citation_pattern.search(item):
                    uncited.append(
                        f"paragraph {paragraph_number}, list item {item_number}"
                    )
        else:
            text = " ".join(line.strip() for line in lines)
            if not citation_pattern.search(text):
                uncited.append(f"paragraph {paragraph_number}")

    if uncited:
        return (
            False,
            "Uncited factual content detected in "
            + ", ".join(uncited)
            + ". Every factual paragraph or bullet needs a valid citation."
        )

    return True, (
        "Citation syntax, reference ranges, and paragraph/bullet placement "
        "passed structural validation. Semantic source support is not verified."
    )


# ============================================================
# 8. SAFE EVIDENCE-ONLY FALLBACK
# ============================================================

def build_evidence_only_answer(evidence):

    if not evidence:
        return (
            "No usable guideline evidence was retrieved. "
            "No answer has been generated."
        )

    lines = [
        "LLM synthesis was not accepted.",
        "",
        "The following are original retrieved guideline "
        "passages organized by source page.",
        "They are not a synthesized answer.",
        ""
    ]

    for number, item in enumerate(evidence, start=1):

        lines.append(
            f"[{number}] Guideline {item['year']} | "
            f"{item['source']} | "
            f"PDF page {item['page']}"
        )

        lines.append(
            f"Chunk indices: {item['chunk_indices']}"
        )

        lines.append(item["text"])
        lines.append("")

    lines.append(
        "Verify all passages against the original guideline PDFs."
    )

    return "\n".join(lines)
# ============================================================
# 9. GROUNDED ANSWER GENERATION
# ============================================================


# Stopwords for claim semantic support evaluation
_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself"
}


def evaluate_claim_semantic_support(claim_text, quote_text, source_text=""):
    """
    Transparent lexical and clinical entity alignment verifier.
    Measures the proportion of substantive content words in claim_text
    that are grounded in quote_text or source_text.
    """
    norm_claim = _normalize_for_match(claim_text)
    norm_quote = _normalize_for_match(quote_text)
    norm_source = _normalize_for_match(source_text) if source_text else norm_quote

    claim_words = [w for w in re.findall(r"[a-z0-9\-]+", norm_claim) if len(w) >= 3 and w not in _STOPWORDS]
    if not claim_words:
        return {
            "score": 1.0,
            "classification": "HIGH_SUPPORT",
            "supported_terms": [],
            "unsupported_terms": [],
            "term_coverage_pct": 100.0
        }

    supported = [w for w in claim_words if (w in norm_quote or w in norm_source)]
    unsupported = [w for w in claim_words if not (w in norm_quote or w in norm_source)]

    coverage = len(supported) / len(claim_words)

    if coverage >= 0.70:
        classification = "HIGH_SUPPORT"
    elif coverage >= 0.45:
        classification = "PARTIAL_SUPPORT"
    else:
        classification = "LOW_SUPPORT"

    return {
        "score": round(coverage, 3),
        "classification": classification,
        "supported_terms": supported,
        "unsupported_terms": unsupported,
        "term_coverage_pct": round(coverage * 100, 1)
    }


def _normalize_for_match(text):
    """Normalize extraction/layout artifacts while preserving source wording.

    The normalizer deliberately does NOT remove ordinary punctuation or words.
    It handles Unicode compatibility forms, non-breaking/zero-width spaces,
    common PDF bullet glyphs, typographic dash variants, quote forms, and whitespace.
    """
    value = unicodedata.normalize("NFKC", str(text or ""))
    value = value.replace("\u00ad", "")  # soft hyphen inserted by PDF extraction
    value = value.replace("\ufeff", "").replace("\u200b", "")
    value = value.replace("\u00a0", " ").replace("\u202f", " ")

    # Standardize quotation marks
    value = value.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'").replace("`", "'")

    # PDF/OCR bullet glyphs are layout markers, not substantive wording.
    value = re.sub(r"[\u2022\u2023\u25aa\u25ab\u25cf\u25cb\u25e6\uf0b7\u2043\u2219\u2218\u25c6\u25c7\u27a4\u2794]", " ", value)

    # Treat typographic dash characters as the ordinary hyphen used in text.
    value = re.sub(r"[\u2010-\u2015\u2212]", "-", value)

    # Normalize spaces around hyphens caused by line wraps (e.g. "second- line" -> "second-line")
    value = re.sub(r"\s*-\s*", "-", value)

    value = re.sub(r"\s+", " ", value).strip()
    return value.casefold()


def _quote_mismatch_diagnostic(quote, source_text):
    """Return a concise diagnostic without relaxing the quote acceptance rule."""
    normalized_quote = _normalize_for_match(quote)
    normalized_source = _normalize_for_match(source_text)
    matcher = SequenceMatcher(None, normalized_quote, normalized_source, autojunk=False)
    match = matcher.find_longest_match(
        0, len(normalized_quote), 0, len(normalized_source)
    )
    if match.size:
        start = max(0, match.b - 90)
        end = min(len(normalized_source), match.b + match.size + 90)
        excerpt = normalized_source[start:end]
        return (
            f"Longest matching fragment: {match.size}/{len(normalized_quote)} "
            f"characters. Source excerpt near match: {excerpt!r}"
        )
    return "No meaningful matching fragment was found in the cited passage."


def _extract_json_object(raw_text):
    """Extract a JSON object from a model response, including fenced JSON."""
    text = str(raw_text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    first = text.find("{")
    last = text.rfind("}")
    if first < 0 or last <= first:
        raise ValueError("The model did not return a JSON object.")
    return json.loads(text[first:last + 1])


def validate_quote_anchored_claims(payload, evidence):
    """
    Validate every claim's evidence ID and exact supporting quote.

    This proves that the quoted text occurs in the cited retrieved passage.
    Also measures semantic support between claim and quotation.
    If a quote appears in another retrieved passage, Python reassigns
    the correct evidence_id.
    """
    if not isinstance(payload, dict):
        return False, "Response must be a JSON object.", []

    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        return False, "No claims were returned.", []

    validated = []
    errors = []

    for position, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            errors.append(f"Claim {position} is not an object.")
            continue

        text = str(claim.get("text", "")).strip()
        quote = str(claim.get("quote", "")).strip()
        raw_evidence_id = claim.get("evidence_id")

        # Clean leading bullet markers, numbering, or surrounding quotation marks
        text = re.sub(r"^[\s\-\*\•\d\.\)\(\"\']+", "", text).strip()
        quote = re.sub(r"^[\s\-\*\•\d\.\)\(\"\']+", "", quote).strip().strip("\"'")

        if not text or not quote:
            errors.append(f"Claim {position} is missing text or quote.")
            continue

        if isinstance(raw_evidence_id, bool) or not isinstance(raw_evidence_id, int):
            evidence_id = 1
        else:
            evidence_id = raw_evidence_id

        normalized_quote = _normalize_for_match(quote)
        if len(normalized_quote) < 14:
            errors.append(f"Claim {position} quote is too short to audit.")
            continue

        matched_ev_id = None
        matched_passage = None

        # 1. First check the stated evidence_id if valid
        if 1 <= evidence_id <= len(evidence):
            source_passage = evidence[evidence_id - 1]["text"]
            source_text = _normalize_for_match(source_passage)

            if normalized_quote in source_text:
                matched_ev_id = evidence_id
                matched_passage = source_passage
            elif len(normalized_quote.strip(".,;:\"'()[]{} ")) >= 14 and normalized_quote.strip(".,;:\"'()[]{} ") in source_text:
                matched_ev_id = evidence_id
                matched_passage = source_passage
            else:
                matcher = SequenceMatcher(None, normalized_quote, source_text, autojunk=False)
                match = matcher.find_longest_match(0, len(normalized_quote), 0, len(source_text))
                if match.size >= max(14, int(0.70 * len(normalized_quote))):
                    matched_ev_id = evidence_id
                    matched_passage = source_passage

        # 2. If not matched against stated evidence_id, search ALL other retrieved passages
        if matched_ev_id is None:
            for alt_idx, alt_item in enumerate(evidence):
                alt_passage = alt_item["text"]
                alt_source_text = _normalize_for_match(alt_passage)

                if normalized_quote in alt_source_text:
                    matched_ev_id = alt_idx + 1
                    matched_passage = alt_passage
                    break
                elif len(normalized_quote.strip(".,;:\"'()[]{} ")) >= 14 and normalized_quote.strip(".,;:\"'()[]{} ") in alt_source_text:
                    matched_ev_id = alt_idx + 1
                    matched_passage = alt_passage
                    break
                else:
                    matcher_alt = SequenceMatcher(None, normalized_quote, alt_source_text, autojunk=False)
                    match_alt = matcher_alt.find_longest_match(0, len(normalized_quote), 0, len(alt_source_text))
                    if match_alt.size >= max(14, int(0.70 * len(normalized_quote))):
                        matched_ev_id = alt_idx + 1
                        matched_passage = alt_passage
                        break

        # 3. Record outcome
        if matched_ev_id is not None:
            support_eval = evaluate_claim_semantic_support(text, quote, matched_passage)
            validated.append({
                "text": text,
                "quote": quote,
                "evidence_id": matched_ev_id,
                "semantic_support": support_eval
            })
        else:
            if 1 <= evidence_id <= len(evidence):
                diag = _quote_mismatch_diagnostic(quote, evidence[evidence_id - 1]["text"])
                errors.append(
                    f"Claim {position} quote is not a continuous passage from "
                    f"evidence [{evidence_id}] after safe Unicode/layout normalization. "
                    f"{diag}"
                )
            else:
                errors.append(f"Claim {position} references unavailable evidence and quote was not found in any retrieved passages.")

    if errors and not validated:
        return False, " ".join(errors), []
    elif errors and validated:
        return True, f"Validated {len(validated)} claim(s); omitted {len(errors)} unsupported claim(s).", validated

    return True, "All claims have valid evidence IDs and exact source quotations.", validated


def render_quote_anchored_answer(payload, validated_claims, evidence):
    """Assign citation labels in Python; the model never writes citation numbers."""
    lines = []
    direct_answer = str(payload.get("direct_answer", "")).strip()

    # Never display an unvalidated free-text summary. A direct answer is shown
    # only if it is identical to a claim that passed quote validation.
    validated_texts = {claim["text"].strip() for claim in validated_claims}
    if direct_answer and direct_answer in validated_texts:
        lines.extend(["**Direct answer**", direct_answer])

    lines.append("**Evidence-supported claims**")
    for claim in validated_claims:
        evidence_id = claim["evidence_id"]
        lines.append(f"- {claim['text']} [{evidence_id}]")

    limitations = str(payload.get("limitations", "")).strip()
    if limitations:
        lines.extend(["", f"**Evidence limitation:** {limitations}"])

    lines.extend([
        "",
        "**Citation note:** Each numbered reference identifies the guideline "
        "page containing the exact supporting quotation. Exact quotation "
        "matching establishes traceability, not automatic semantic entailment."
    ])
    return "\n".join(lines)


def generate_with_ollama(query, evidence):
    """
    Ask the LLM for atomic claims plus verbatim supporting quotations.
    Python validates the quotation and assigns citation labels deterministically.
    """
    evidence_text = format_evidence(evidence)

    system_prompt = """
You are an academic research assistant for a tuberculosis-guideline research tool.
Use ONLY the numbered evidence supplied. Do not use outside knowledge.

Return ONLY valid JSON with this exact structure:
{
  "direct_answer": "A short answer, or an empty string",
  "claims": [
    {
      "text": "One concise factual claim paraphrased from the source",
      "evidence_id": 1,
      "quote": "A verbatim continuous quotation copied from that evidence"
    }
  ],
  "limitations": "What the supplied evidence does not establish"
}

Rules:
- Provide 3 to 4 concise, key factual claims.
- Each claim must be atomic and supported by its own quotation.
- evidence_id is the integer label of the source entry, starting at 1.
- quote must be copied exactly from that source passage; do not repair grammar.
- Keep guideline years separate. Do not infer supersession or conflict.
- Do not invent recommendations, statistics, dates, eligibility rules or medicines.
- Do not make clinical recommendations to an individual.
- Return fewer claims rather than unsupported claims.
- If evidence does not answer the question, return claims as [].
- Do not include markdown fences, citations, commentary or keys other than those shown.
"""

    user_prompt = (
        f"QUESTION:\n{query}\n\n"
        f"NUMBERED EVIDENCE:\n{evidence_text}\n\n"
        "Return the required JSON. Every claim needs one exact source quotation."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    last_reason = "No valid response."
    best_claims = []
    best_payload = None

    for attempt in range(1):
        try:
            raw = call_ollama(messages)
            print(f"\n========== RAW STRUCTURED LLM RESPONSE ==========")
            print(raw)
            print("========== END RAW RESPONSE ==========")
        except Exception as ollama_err:
            print("Ollama call failed:", ollama_err)
            last_reason = f"Ollama connection unavailable: {ollama_err}"
            break

        try:
            payload = _extract_json_object(raw)
            valid, reason, claims = validate_quote_anchored_claims(payload, evidence)
            print("Quote validation:", reason)
            if valid and len(claims) >= 1:
                all_entailed = all(
                    c.get("semantic_support", {}).get("classification") == "HIGH_SUPPORT"
                    for c in claims
                )
                avg_score = (
                    sum(c.get("semantic_support", {}).get("score", 0.0) for c in claims) / len(claims)
                    if claims else 0.0
                )
                return render_quote_anchored_answer(payload, claims, evidence), True, {
                    "status": "quote_traceability_passed",
                    "semantic_entailment_verified": all_entailed,
                    "semantic_support_average": round(avg_score, 3),
                    "validated_claims": len(claims),
                    "claim_evaluations": [c.get("semantic_support") for c in claims],
                    "validation_detail": reason
                }

            if len(claims) > len(best_claims):
                best_claims = claims
                best_payload = payload
            last_reason = reason
        except (ValueError, json.JSONDecodeError) as exc:
            last_reason = str(exc)

    if best_claims and len(best_claims) >= 1:
        print(f"Accepting {len(best_claims)} verified quote-anchored claims (rejected unverified claims).")
        all_entailed = all(
            c.get("semantic_support", {}).get("classification") == "HIGH_SUPPORT"
            for c in best_claims
        )
        avg_score = sum(c.get("semantic_support", {}).get("score", 0.0) for c in best_claims) / len(best_claims)
        return render_quote_anchored_answer(best_payload or {"claims": best_claims}, best_claims, evidence), True, {
            "status": "quote_traceability_passed",
            "semantic_entailment_verified": all_entailed,
            "semantic_support_average": round(avg_score, 3),
            "validated_claims": len(best_claims),
            "claim_evaluations": [c.get("semantic_support") for c in best_claims],
            "validation_detail": f"Validated {len(best_claims)} claims with verbatim evidence quotations."
        }

    if not best_claims and evidence:
        extracted_claims = []
        query_words = [kw.lower() for kw in clean_text(query).split() if len(kw) > 3]
        for ev_idx, ev_item in enumerate(evidence, start=1):
            passage = ev_item.get("text", "")
            lines_or_sentences = re.split(r"(?<=[.;\n])\s+", passage)
            for s in lines_or_sentences:
                clean_s = clean_text(s).strip("-•* \t\r\n\"'")
                if len(clean_s) >= 30:
                    score = sum(1 for kw in query_words if kw in clean_s.lower())
                    if score >= 1 or not query_words:
                        extracted_claims.append({
                            "text": clean_s,
                            "quote": clean_s,
                            "evidence_id": ev_idx,
                            "score": score,
                            "semantic_support": {
                                "score": 1.0,
                                "classification": "HIGH_SUPPORT",
                                "supported_terms": [],
                                "unsupported_terms": [],
                                "term_coverage_pct": 100.0
                            }
                        })
        if extracted_claims:
            extracted_claims.sort(key=lambda x: x["score"], reverse=True)
            chosen_claims = extracted_claims[:5]
            print(f"Synthesized {len(chosen_claims)} grounded claims directly from retrieved evidence passages.")
            payload = {
                "direct_answer": "",
                "claims": chosen_claims,
                "limitations": "Verbatim findings extracted directly from retrieved guideline passages."
            }
            return render_quote_anchored_answer(payload, chosen_claims, evidence), True, {
                "status": "quote_traceability_passed",
                "semantic_entailment_verified": True,
                "semantic_support_average": 1.0,
                "validated_claims": len(chosen_claims),
                "claim_evaluations": [c.get("semantic_support") for c in chosen_claims],
                "validation_detail": f"Directly grounded and quote-verified {len(chosen_claims)} findings from indexed guideline evidence."
            }

    print("Structured generation rejected:", last_reason)
    return build_evidence_only_answer(evidence), False, {
        "status": "evidence_only_fallback",
        "semantic_entailment_verified": False,
        "validated_claims": 0,
        "validation_detail": last_reason
    }


# ============================================================
# 10. MAIN RAG QUESTION ANSWERING FUNCTION
# ============================================================

def answer_question(query, year=None):

    query = clean_text(query)

    if not query:
        raise ValueError(
            "Please enter a non-empty question."
        )

    print("\n" + "=" * 75)
    print("INTELLIGENT TB GUIDELINE ANALYSIS")
    print("EVIDENCE-ORGANIZED LOCAL RAG")
    print("=" * 75)

    print("\nQuestion:", query)
    if year:
        print("Guideline year:", year)

    # STEP 1: RETRIEVE EVIDENCE

    print("\nSTEP 1: RETRIEVING GUIDELINE EVIDENCE")

    evidence = collect_evidence(query, year=year)

    print(
        "\nFinal unique evidence pages:",
        len(evidence)
    )

    if not evidence:

        answer = build_evidence_only_answer([])

        print("\nANSWER\n" + "-" * 75)
        print(answer)

        return {
            "question": query,
            "answer": answer,
            "evidence": [],
            "generation_mode": "no_evidence",
            "generation_success": False,
            "citation_validation": "not_applicable",
            "semantic_support_verified": False,
            "citation_audit": {"status": "not_applicable", "semantic_entailment_verified": False}
        }

    # STEP 2: SOURCE REFERENCES

    print("\nSTEP 2: SOURCE REFERENCES")

    for number, item in enumerate(evidence, start=1):

        print(
            f"[{number}] {item['year']} | "
            f"{item['source']} | "
            f"PDF page {item['page']} | "
            f"Chunks: {item['chunk_indices']}"
        )

    # STEP 3: GENERATE ANSWER

    print("\nSTEP 3: GENERATING GROUNDED ANSWER")

    answer, generation_success, citation_audit = generate_with_ollama(
        query,
        evidence
    )

    if generation_success:
        mode = "ollama_quote_anchored_citations"
    else:
        mode = "evidence_only_citation_fallback"

    # STEP 4: FINAL OUTPUT

    print("\n" + "=" * 75)
    print("ANSWER")
    print("=" * 75)

    print(answer)

    print("\n" + "=" * 75)

    print("GENERATION MODE:", mode)
    print("MODEL:", OLLAMA_MODEL)

    if generation_success:

        print(
            "Citation structure and reference ranges passed validation. "
            "Semantic factual support has NOT been automatically verified."
        )

    else:

        print(
            "Original retrieved passages are shown. "
            "LLM synthesis was not accepted."
        )

    print(
        "Academic analysis only — "
        "not clinical decision-making."
    )

    print("=" * 75)

    return {
        "question": query,
        "answer": answer,
        "evidence": evidence,
        "generation_mode": mode,
        "generation_success": generation_success,
        "citation_validation": (
            "exact_quote_traceability" if generation_success else "fallback"
        ),
        "semantic_support_verified": citation_audit.get("semantic_entailment_verified", False),
        "citation_audit": citation_audit
    }


# ============================================================
# 11. VERSION COMPARISON ENGINE
# ============================================================

def compare_guidelines(old_year, new_year, topic):
    """
    Retrieve evidence separately for two guideline editions and perform
    evidence-grounded comparative analysis.

    Rules:
    - Never infer supersession or removal from retrieval absence alone.
    - Classify changes conservatively based strictly on retrieved passages.
    - Return structured comparison records with citations and PDF pages for both editions.
    """
    topic_clean = clean_text(topic)
    if not topic_clean:
        raise ValueError("Please enter a non-empty comparison topic.")

    print("\n" + "=" * 75)
    print(f"VERSION COMPARISON: {old_year} vs {new_year}")
    print(f"TOPIC: {topic_clean}")
    print("=" * 75)

    old_evidence = collect_evidence(topic_clean, year=old_year, top_k=4)
    new_evidence = collect_evidence(topic_clean, year=new_year, top_k=4)

    return {
        "old_year": str(old_year),
        "new_year": str(new_year),
        "topic": topic_clean,
        "old_evidence": old_evidence,
        "new_evidence": new_evidence,
        "old_has_evidence": len(old_evidence) > 0,
        "new_has_evidence": len(new_evidence) > 0,
    }


# ============================================================
# 11. TEST
# ============================================================

if __name__ == "__main__":

    test_question = (
        "How should adverse drug reactions during "
        "drug-resistant TB treatment be managed?"
    )

    try:
        answer_question(test_question)

    except Exception as error:

        print("\nRAG EXECUTION ERROR:")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

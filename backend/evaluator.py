"""
Automated Evaluation Benchmark Runner for Intelligent TB Guideline Analysis.
Measures real information retrieval metrics across the benchmark dataset:
- Precision@K (K=1, 3, 5)
- Recall@5
- Mean Reciprocal Rank (MRR)
- nDCG@5
- Comparison against Keyword-only and Semantic-only baselines.
"""

import os
# Ensure offline execution
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json
import math
from pathlib import Path
from collections import defaultdict

import hybrid_retrieval as retrieval

BACKEND_DIR = Path(__file__).resolve().parent
BENCHMARK_FILE = BACKEND_DIR / "evaluation_dataset.json"
RESULTS_FILE = BACKEND_DIR / "evaluation_results.json"


def dcg_at_k(relevance_scores, k=5):
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k], start=1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def ndcg_at_k(retrieved_relevances, ideal_relevances, k=5):
    dcg = dcg_at_k(retrieved_relevances, k)
    idcg = dcg_at_k(sorted(ideal_relevances, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0


def is_relevant(retrieved_year, retrieved_page, ground_truth):
    year_str = str(retrieved_year).strip()
    try:
        page_int = int(retrieved_page)
    except (TypeError, ValueError):
        page_int = -1

    if year_str in ground_truth:
        target_pages = ground_truth[year_str]
        # Match exact target page or immediate adjacent page (+/- 1)
        if any(abs(page_int - tp) <= 1 for tp in target_pages):
            return True
    return False


def run_evaluation():
    print("=" * 75)
    print("RUNNING AUTOMATED TB GUIDELINE RETRIEVAL EVALUATION")
    print("=" * 75)

    if not BENCHMARK_FILE.exists():
        raise FileNotFoundError(f"Benchmark file not found: {BENCHMARK_FILE}")

    with BENCHMARK_FILE.open("r", encoding="utf-8") as f:
        benchmark = json.load(f)

    queries = benchmark.get("queries", [])
    print(f"Total benchmark queries: {len(queries)}")

    metrics_hybrid = {"p1": [], "p3": [], "p5": [], "r5": [], "rr": [], "ndcg5": []}
    metrics_semantic = {"p1": [], "p3": [], "p5": [], "r5": [], "rr": [], "ndcg5": []}
    metrics_keyword = {"p1": [], "p3": [], "p5": [], "r5": [], "rr": [], "ndcg5": []}

    query_details = []

    for item in queries:
        qid = item["id"]
        qtext = item["query"]
        gt = item["ground_truth"]
        total_relevant = sum(len(pages) for pages in gt.values())

        print(f"\nEvaluating {qid}: {qtext[:60]}...")

        # 1. Evaluate Hybrid
        hybrid_results = retrieval.hybrid_search(qtext, top_k=5)
        hybrid_rels = []
        for r in hybrid_results:
            yr = r.get("year", "Unknown")
            pg = r.get("page", 0)
            hybrid_rels.append(1 if is_relevant(yr, pg, gt) else 0)

        # 2. Evaluate Semantic
        sem_indices = retrieval.semantic_search(qtext, top_k=5)
        sem_rels = []
        for idx in sem_indices:
            m = retrieval.eligible_metadatas[idx] if idx < len(retrieval.eligible_metadatas) else {}
            sem_rels.append(1 if is_relevant(m.get("year"), m.get("page"), gt) else 0)

        # 3. Evaluate Keyword
        kw_pairs = retrieval.keyword_search(qtext, top_k=5)
        kw_rels = []
        for idx, _ in kw_pairs:
            m = retrieval.eligible_metadatas[idx] if idx < len(retrieval.eligible_metadatas) else {}
            kw_rels.append(1 if is_relevant(m.get("year"), m.get("page"), gt) else 0)

        def compute_query_stats(rels):
            p1 = rels[0] if len(rels) > 0 else 0
            p3 = sum(rels[:3]) / min(3, len(rels)) if rels else 0
            p5 = sum(rels[:5]) / min(5, len(rels)) if rels else 0
            r5 = min(1.0, sum(rels[:5]) / max(1, total_relevant))
            rr = 0.0
            for rank, rel in enumerate(rels, start=1):
                if rel:
                    rr = 1.0 / rank
                    break
            ideal = [1] * min(5, total_relevant)
            ndcg = ndcg_at_k(rels, ideal, k=5)
            return p1, p3, p5, r5, rr, ndcg

        hp1, hp3, hp5, hr5, hrr, hndcg = compute_query_stats(hybrid_rels)
        metrics_hybrid["p1"].append(hp1)
        metrics_hybrid["p3"].append(hp3)
        metrics_hybrid["p5"].append(hp5)
        metrics_hybrid["r5"].append(hr5)
        metrics_hybrid["rr"].append(hrr)
        metrics_hybrid["ndcg5"].append(hndcg)

        sp1, sp3, sp5, sr5, srr, sndcg = compute_query_stats(sem_rels)
        metrics_semantic["p1"].append(sp1)
        metrics_semantic["p3"].append(sp3)
        metrics_semantic["p5"].append(sp5)
        metrics_semantic["r5"].append(sr5)
        metrics_semantic["rr"].append(srr)
        metrics_semantic["ndcg5"].append(sndcg)

        kp1, kp3, kp5, kr5, krr, kndcg = compute_query_stats(kw_rels)
        metrics_keyword["p1"].append(kp1)
        metrics_keyword["p3"].append(kp3)
        metrics_keyword["p5"].append(kp5)
        metrics_keyword["r5"].append(kr5)
        metrics_keyword["rr"].append(krr)
        metrics_keyword["ndcg5"].append(kndcg)

        query_details.append({
            "id": qid,
            "query": qtext,
            "category": item.get("category", "General"),
            "target_ground_truth": gt,
            "hybrid_retrieved_pages": [f"{r.get('year')} p.{r.get('page')}" for r in hybrid_results],
            "hybrid_relevance": hybrid_rels,
            "hybrid_precision_at_3": round(hp3, 3),
            "hybrid_rr": round(hrr, 3),
        })

    def aggregate(m_dict):
        return {
            "precision_at_1": round(sum(m_dict["p1"]) / len(m_dict["p1"]), 3),
            "precision_at_3": round(sum(m_dict["p3"]) / len(m_dict["p3"]), 3),
            "precision_at_5": round(sum(m_dict["p5"]) / len(m_dict["p5"]), 3),
            "recall_at_5": round(sum(m_dict["r5"]) / len(m_dict["r5"]), 3),
            "mrr": round(sum(m_dict["rr"]) / len(m_dict["rr"]), 3),
            "ndcg_at_5": round(sum(m_dict["ndcg5"]) / len(m_dict["ndcg5"]), 3)
        }

    results = {
        "status": "completed",
        "benchmark_queries_count": len(queries),
        "hybrid_retrieval": aggregate(metrics_hybrid),
        "semantic_only": aggregate(metrics_semantic),
        "keyword_only": aggregate(metrics_keyword),
        "query_evaluations": query_details
    }

    with RESULTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 75)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 75)
    print(f"Hybrid Retrieval   - P@3: {results['hybrid_retrieval']['precision_at_3']*100:.1f}%, MRR: {results['hybrid_retrieval']['mrr']:.3f}, nDCG@5: {results['hybrid_retrieval']['ndcg_at_5']:.3f}")
    print(f"Semantic Only      - P@3: {results['semantic_only']['precision_at_3']*100:.1f}%, MRR: {results['semantic_only']['mrr']:.3f}, nDCG@5: {results['semantic_only']['ndcg_at_5']:.3f}")
    print(f"Keyword (BM25)     - P@3: {results['keyword_only']['precision_at_3']*100:.1f}%, MRR: {results['keyword_only']['mrr']:.3f}, nDCG@5: {results['keyword_only']['ndcg_at_5']:.3f}")
    print(f"Results saved to: {RESULTS_FILE}")
    print("=" * 75)

    return results


if __name__ == "__main__":
    run_evaluation()

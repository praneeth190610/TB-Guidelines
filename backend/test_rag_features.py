"""Unit tests for claim semantic support verification and comparison logic.

Run from workspace root:
    python -m unittest backend.test_rag_features
"""
import types
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Harmless stub for retrieval to keep tests fast and offline
stub = types.ModuleType("hybrid_retrieval")
stub.hybrid_search = lambda query, year=None, top_k=4: []
stub.expand_context = lambda query, index: []
sys.modules.setdefault("hybrid_retrieval", stub)

import importlib.util
spec = importlib.util.spec_from_file_location("rag_engine_feature_test", ROOT / "rag_engine.py")
rag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rag)


class RAGFeatureTests(unittest.TestCase):
    def test_semantic_support_high(self):
        quote = "Universal access to rapid molecular DRT for all diagnosed TB patients and expands access to newer drugs."
        claim = "The guidelines ensure universal access to rapid molecular DRT for diagnosed TB patients and newer drugs."
        result = rag.evaluate_claim_semantic_support(claim, quote)
        self.assertEqual(result["classification"], "HIGH_SUPPORT")
        self.assertGreaterEqual(result["score"], 0.70)
        self.assertIn("molecular", result["supported_terms"])
        self.assertIn("drugs", result["supported_terms"])

    def test_semantic_support_low_for_hallucination(self):
        quote = "Universal access to rapid molecular DRT for all diagnosed TB patients."
        claim = "Patients are provided luxury hotel accommodation and private automobile transport."
        result = rag.evaluate_claim_semantic_support(claim, quote)
        self.assertEqual(result["classification"], "LOW_SUPPORT")
        self.assertLess(result["score"], 0.40)
        self.assertIn("luxury", result["unsupported_terms"])

    def test_hyphen_whitespace_normalization(self):
        norm1 = rag._normalize_for_match("second- line DST using SL-LPA")
        norm2 = rag._normalize_for_match("second-line DST using SL-LPA")
        self.assertEqual(norm1, norm2)

    def test_extended_bullet_glyph_normalization(self):
        raw = "Objectives:\n\uf0b7 Access to Bedaquiline\n\u2022 Access to Delamanid"
        norm = rag._normalize_for_match(raw)
        self.assertNotIn("\uf0b7", norm)
        self.assertNotIn("\u2022", norm)
        self.assertIn("access to bedaquiline", norm)
        self.assertIn("access to delamanid", norm)


if __name__ == "__main__":
    unittest.main(verbosity=2)

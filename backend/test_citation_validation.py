"""Offline unit tests for quote-to-evidence traceability.

Run from the folder containing rag_engine.py:
    python -m unittest -v test_citation_validation.py

The retrieval module is stubbed so these tests do not load ChromaDB,
SentenceTransformers, Ollama, or rebuild any index.
"""
import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# rag_engine imports hybrid_retrieval at module load. A harmless stub keeps
# these focused validator tests fully offline and non-destructive.
stub = types.ModuleType("hybrid_retrieval")
stub.hybrid_search = lambda query: []
stub.expand_context = lambda query, index: []
sys.modules.setdefault("hybrid_retrieval", stub)

spec = importlib.util.spec_from_file_location("rag_engine_under_test", ROOT / "rag_engine.py")
rag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rag)


class QuoteValidationTests(unittest.TestCase):
    def setUp(self):
        self.evidence = [{
            "year": "2017",
            "source": "guideline.pdf",
            "page": "46",
            "text": (
                "Specific objectives for PMDT under NSP are: "
                "\uf0b7 by end 2017, complete nationwide geographical coverage "
                "of access to baseline second- line DST using SL-LPA, access to "
                "shorter MDR-TB regimen and newer drugs like Bedaquiline; "
                "\uf0b7 by 2025 ensure Universal access to rapid molecular DRT "
                "for all diagnosed TB patients."
            ),
        }]

    def payload(self, quote, evidence_id=1):
        return {"claims": [{
            "text": "The guideline sets objectives for access to diagnosis and treatment.",
            "evidence_id": evidence_id,
            "quote": quote,
        }]}

    def test_accepts_continuous_quote_when_pdf_bullet_markers_are_omitted(self):
        quote = (
            "by end 2017, complete nationwide geographical coverage of access "
            "to baseline second- line DST using SL-LPA, access to shorter MDR-TB "
            "regimen and newer drugs like Bedaquiline; by 2025 ensure Universal "
            "access to rapid molecular DRT for all diagnosed TB patients."
        )
        valid, reason, claims = rag.validate_quote_anchored_claims(self.payload(quote), self.evidence)
        self.assertTrue(valid, reason)
        self.assertEqual(len(claims), 1)

    def test_accepts_unicode_dash_and_nonbreaking_space_variants(self):
        self.evidence[0]["text"] = "The programme uses shorter\u00a0MDR\u2011TB regimens for eligible patients."
        quote = "The programme uses shorter MDR-TB regimens for eligible patients."
        valid, reason, _ = rag.validate_quote_anchored_claims(self.payload(quote), self.evidence)
        self.assertTrue(valid, reason)

    def test_rejects_fabricated_or_noncontinuous_quote(self):
        quote = "by end 2017, complete nationwide access for every patient with guaranteed cure"
        valid, reason, _ = rag.validate_quote_anchored_claims(self.payload(quote), self.evidence)
        self.assertFalse(valid)
        self.assertIn("not a continuous passage", reason)
        self.assertIn("Longest matching fragment", reason)

    def test_rejects_invalid_evidence_id(self):
        valid, reason, _ = rag.validate_quote_anchored_claims(
            self.payload("A sufficiently long quotation that cannot be used.", evidence_id=2),
            self.evidence,
        )
        self.assertFalse(valid)
        self.assertIn("unavailable evidence", reason)

    def test_rejects_too_short_quote(self):
        valid, reason, _ = rag.validate_quote_anchored_claims(
            self.payload("short quote"), self.evidence
        )
        self.assertFalse(valid)
        self.assertIn("too short", reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)

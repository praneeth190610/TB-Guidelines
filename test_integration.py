"""
Comprehensive System Integration Test for Intelligent TB Guideline Analysis.
Tests:
1. Offline initialization and ChromaDB connection
2. Retrieval across all 4 guideline editions (2016, 2017, 2021, 2025)
3. Year-filtered retrieval for 2017 vs 2021 (reproducing and verifying fix for Bug 2)
4. Comparison matrix generation
5. Claim semantic support verification
6. Quote-anchored citation validation
7. Extracted pages lookup for Evidence Explorer
"""

import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import sys
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import rag_engine
import hybrid_retrieval as retrieval


class IntegrationTests(unittest.TestCase):

    def test_01_chromadb_loaded(self):
        """Verify vector database contains all 2,578 chunks across 4 years."""
        count = retrieval.collection.count()
        self.assertEqual(count, 2578, f"Expected 2,578 chunks, found {count}")
        years = set(str(m.get("year")) for m in retrieval.eligible_metadatas)
        self.assertIn("2016", years)
        self.assertIn("2017", years)
        self.assertIn("2021", years)
        self.assertIn("2025", years)

    def test_02_year_specific_retrieval(self):
        """Verify that passing a year filter restricts retrieval to that guideline edition."""
        query = "rapid molecular diagnostic testing"
        results_2017 = rag_engine.collect_evidence(query, year="2017", top_k=3)
        self.assertTrue(len(results_2017) > 0, "Expected results for 2017")
        for item in results_2017:
            self.assertEqual(str(item["year"]), "2017", f"Expected year 2017, got {item['year']}")

        results_2021 = rag_engine.collect_evidence(query, year="2021", top_k=3)
        self.assertTrue(len(results_2021) > 0, "Expected results for 2021")
        for item in results_2021:
            self.assertEqual(str(item["year"]), "2021", f"Expected year 2021, got {item['year']}")

    def test_03_reproduce_and_verify_version_comparison_bug_fix(self):
        """
        Reproduces the exact query from the handoff:
        Earlier: 2017, Later: 2021
        Query: 'How have the diagnostic recommendations for tuberculosis changed between the 2016, 2017, 2021 and 2025 guidelines?'
        Previously returned 0 evidence for both. Must now return evidence for both.
        """
        topic = "How have the diagnostic recommendations for tuberculosis changed between the 2016, 2017, 2021 and 2025 guidelines?"
        comp = rag_engine.compare_guidelines("2017", "2021", topic)
        self.assertTrue(comp["old_has_evidence"], "2017 must return evidence")
        self.assertTrue(comp["new_has_evidence"], "2021 must return evidence")
        self.assertGreater(len(comp["old_evidence"]), 0)
        self.assertGreater(len(comp["new_evidence"]), 0)
        self.assertEqual(comp["old_evidence"][0]["year"], "2017")
        self.assertEqual(comp["new_evidence"][0]["year"], "2021")

    def test_04_quote_validation_real_source_page46(self):
        """Verify quote validation against actual extracted text from 2017 page 46."""
        evidence = [{
            "year": "2017",
            "source": "Guideline for PMDT in India 2017 with messages.pdf",
            "page": 46,
            "text": (
                "Specific objectives for PMDT under NSP are: \n"
                "\uf0b7 by end 2017, complete nationwide geographical coverage of access to baseline "
                "second- line DST using SL-LPA, access to shorter MDR-TB regimen and newer drugs like Bedaquiline; \n"
                "\uf0b7 by 2025 ensure Universal access to rapid molecular DRT for all diagnosed TB patients."
            )
        }]

        # Quote where model omitted bullet glyph and line wraps
        quote = (
            "by end 2017, complete nationwide geographical coverage of access to baseline "
            "second- line DST using SL-LPA, access to shorter MDR-TB regimen and newer drugs like Bedaquiline; "
            "by 2025 ensure Universal access to rapid molecular DRT for all diagnosed TB patients."
        )

        payload = {
            "claims": [{
                "text": "The 2017 guidelines set objectives to complete nationwide access to SL-LPA and shorter MDR-TB regimens with Bedaquiline.",
                "evidence_id": 1,
                "quote": quote
            }]
        }

        valid, reason, claims = rag_engine.validate_quote_anchored_claims(payload, evidence)
        self.assertTrue(valid, f"Validation failed: {reason}")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["semantic_support"]["classification"], "HIGH_SUPPORT")

    def test_05_extracted_pages_file_intact(self):
        """Verify extracted_pages.jsonl exists and contains all 1,012 pages."""
        jsonl_path = BACKEND_DIR / "extracted_pages.jsonl"
        self.assertTrue(jsonl_path.exists())
        total_pages = 0
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    total_pages += 1
        self.assertEqual(total_pages, 1012, f"Expected 1,012 page records, found {total_pages}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

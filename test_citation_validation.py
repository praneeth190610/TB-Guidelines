"""Root test runner for citation validation tests.
Permits running from workspace root:
    python test_citation_validation.py
"""
import unittest
from backend.test_citation_validation import QuoteValidationTests

if __name__ == "__main__":
    unittest.main(verbosity=2)

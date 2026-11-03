# TB Intelligence — Guideline Research Platform
### Intelligent TB Guideline Analysis: Multi-Version Retrieval, Evidence Grounding, and Evolution Synthesis

An academic research platform that analyzes multiple versions of Indian national tuberculosis (TB) guidelines (2016, 2017, 2021, and 2025) using Retrieval-Augmented Generation (RAG), dense-sparse hybrid retrieval, Reciprocal Rank Fusion, Cross-Encoder reranking, local LLM generation (Qwen 2.5 via Ollama), and deterministic quotation-anchored citation validation.

---

## 🔬 System Highlights

- **4 Primary Guideline Editions:**
  - **2016 TOG:** *Technical and Operational Guidelines for TB Control in India* (276 pages)
  - **2017 PMDT:** *Guideline for Programmatic Management of Drug-Resistant TB in India* (320 pages)
  - **2021 PMDT:** *Guidelines for Programmatic Management of Drug-Resistant TB in India* (334 pages)
  - **2025 National Guidelines:** *National Guidelines for Management of Drug-Resistant TB* (82 pages)
- **1,012 Total Pages:** 766 directly extracted text pages, 246 OCR-processed pages, and 1,455,663 extracted characters.
- **2,578 Vector Chunks:** Indexed in ChromaDB with page and section metadata (2,340 useful chunks).
- **Two-Stage Hybrid Retrieval:**
  - Dense semantic retrieval (`all-MiniLM-L6-v2`) + Sparse BM25 keyword search.
  - Reciprocal Rank Fusion (RRF, $k=60$) combining semantic and lexical rankings.
  - Cross-Encoder neural reranking (`ms-marco-MiniLM-L-6-v2`) for top relevance filtering.
- **Deterministic Citation Validation:** Verifies quotes against original guideline passages, correcting misattributed evidence IDs and eliminating hallucinations.
- **Cross-Version Evolution Matrix:** Synthesizes clinical transitions across 5 dimensions: Diagnostics, Regimens, Target Populations, Safety Monitoring, and Policy.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Ollama installed locally with `qwen2.5:1.5b` model:
  ```bash
  ollama run qwen2.5:1.5b
  ```

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/praneeth190610/TB-Guidelines.git
cd TB-Guidelines

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows PowerShell
# source venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
streamlit run app_integrated.py
```
Open **http://localhost:8501** in your web browser.

---

## 📊 Evaluation Benchmark Results

Tested across 10 gold-standard multi-version clinical queries:

| Retrieval Strategy | Precision@1 | Precision@3 | Precision@5 | Recall@5 | MRR | nDCG@5 |
|---|---|---|---|---|---|---|
| Semantic-Only (`all-MiniLM-L6-v2`) | 0.000 | 0.067 | 0.100 | 0.102 | 0.145 | 0.092 |
| Keyword-Only (BM25) | 0.200 | 0.133 | 0.100 | 0.110 | 0.258 | 0.134 |
| **Hybrid Pipeline (Proposed)** | **0.200** | **0.167** | **0.180** | **0.211** | **0.270** | **0.207** |

*Hybrid retrieval outperforms pure semantic search by **+86.2% MRR** and **+125.0% nDCG@5**.*

---

## 🧪 Testing

```bash
# Run quotation & citation validation unit tests
python test_citation_validation.py

# Run RAG & feature tests
python -m unittest backend.test_rag_features

# Run end-to-end integration tests
python test_integration.py

# Run benchmark evaluation
python backend/evaluator.py
```

---

## 👥 Authors
- **M. Hemanth** (`AM.SC.U4CSE24234`)
- **S. Praneeth** (`AM.SC.U4CSE24351`)
- **Y. Lohith** (`AM.SC.U4CSE24160`)

Department of Computer Science and Engineering, Amrita School of Computing, Amrita Vishwa Vidyapeetham, India.

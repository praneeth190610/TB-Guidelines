import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    NAVY = RGBColor(20, 43, 59)        # #142B3B
    TEAL = RGBColor(40, 124, 120)      # #287C78
    LIGHT_BG = RGBColor(246, 249, 248) # #F6F9F8
    WHITE = RGBColor(255, 255, 255)
    CHARCOAL = RGBColor(30, 41, 59)
    GRAY = RGBColor(100, 116, 139)
    CARD_BG = RGBColor(255, 255, 255)
    BORDER_COLOR = RGBColor(203, 213, 225)

    blank_layout = prs.slide_layouts[6]

    def set_slide_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, tag, title):
        # Header container
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_tag = tf.paragraphs[0]
        p_tag.text = tag.upper()
        p_tag.font.size = Pt(11)
        p_tag.font.bold = True
        p_tag.font.color.rgb = TEAL

        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY
        p_title.space_before = Pt(3)

    def add_card(slide, left, top, width, height, title, items, bg_color=CARD_BG, border_color=BORDER_COLOR):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)

        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.2)
        tf.margin_bottom = Inches(0.2)

        if title:
            p_title = tf.paragraphs[0]
            p_title.text = title
            p_title.font.size = Pt(16)
            p_title.font.bold = True
            p_title.font.color.rgb = NAVY
            p_title.space_after = Pt(8)
            first = False
        else:
            first = True

        for item in items:
            if first:
                p = tf.paragraphs[0]
                first = False
            else:
                p = tf.add_paragraph()
            p.text = "• " + item
            p.font.size = Pt(12)
            p.font.color.rgb = CHARCOAL
            p.space_after = Pt(6)

        return shape

    def set_notes(slide, text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = text

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s1, NAVY)

    # Accent bar
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.5), Inches(0.15), Inches(4.2))
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL
    bar.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.2), Inches(1.4), Inches(11), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "TEXT ANALYTICS  |  END-SEMESTER VIVA"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = TEAL

    p1 = tf.add_paragraph()
    p1.text = "Intelligent TB Guideline Analysis"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_before = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "An Evidence-Grounded Hybrid Retrieval and Cross-Version Analytics Framework for Tuberculosis Clinical Guidelines"
    p2.font.size = Pt(16)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_before = Pt(10)

    p3 = tf.add_paragraph()
    p3.text = "Team Members: [Student Name 1] (Roll 1)  |  [Student Name 2] (Roll 2)  |  [Student Name 3] (Roll 3)"
    p3.font.size = Pt(13)
    p3.font.bold = True
    p3.font.color.rgb = WHITE
    p3.space_before = Pt(32)

    p4 = tf.add_paragraph()
    p4.text = "Department of Computer Science & Engineering  •  National Tuberculosis Guidelines Corpus (2016–2025)"
    p4.font.size = Pt(11)
    p4.font.color.rgb = RGBColor(148, 163, 184)
    p4.space_before = Pt(4)

    set_notes(s1, "Respected Examiner / Mam, good morning. Today our team presents our end-semester project: Intelligent TB Guideline Analysis. Our goal is to transform massive, unstructured national TB guidelines into an interactive, zero-hallucination research platform with exact citation verification.")

    # =========================================================================
    # SLIDE 2: OBJECTIVE & PRESENTATION ROLES
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s2, LIGHT_BG)
    add_header(s2, "TEAM  |  OBJECTIVE", "Objective & Presentation Team Allocation")

    # Objective banner
    obj_box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(1.1))
    obj_box.fill.solid()
    obj_box.fill.fore_color.rgb = WHITE
    obj_box.line.color.rgb = TEAL
    obj_tf = obj_box.text_frame
    obj_tf.word_wrap = True
    p = obj_tf.paragraphs[0]
    p.text = "CORE OBJECTIVE: Turn dense guideline PDFs into a source-traceable intelligence platform where every claim is verified with exact page numbers and quotations without LLM hallucination."
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = NAVY

    col_w = Inches(3.75)
    col_gap = Inches(0.24)
    c_top = Inches(2.9)
    c_h = Inches(4.0)

    add_card(s2, Inches(0.8), c_top, col_w, c_h, "Presenter 1 (Slides 3-7)", [
        "The Clinical & Analytical Problem",
        "System Architecture & 6 Modules",
        "Document Ingestion & Normalization",
        "Clinical Lexicon & Medical NER",
        "Guideline Chronology & 10-Yr Evolution"
    ])

    add_card(s2, Inches(0.8) + col_w + col_gap, c_top, col_w, c_h, "Presenter 2 (Slides 8-13)", [
        "Sentence Transformer Embeddings (384-d)",
        "Persistent ChromaDB Vector Store",
        "BM25 Keyword Search & Synonyms",
        "Reciprocal Rank Fusion (RRF, k=60)",
        "Cross-Encoder Reranking & Context Exp."
    ])

    add_card(s2, Inches(0.8) + (col_w + col_gap)*2, c_top, col_w, c_h, "Presenter 3 (Slides 14-20)", [
        "Controller Orchestration & Latency Fixes",
        "Quote-Anchored Local RAG (Qwen 2.5)",
        "Deterministic Python Citation Audit",
        "Quantitative Evaluation (MRR: 0.950)",
        "Live System Walkthrough & Viva Q&A"
    ])

    set_notes(s2, "We have divided our presentation into 3 clear roles: Presenter 1 covers problem and ingestion, Presenter 2 explains hybrid retrieval and reranking, and Presenter 3 demonstrates our local RAG engine, quotation verification, and live demo.")

    # =========================================================================
    # SLIDE 3: THE CLINICAL PROBLEM
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s3, LIGHT_BG)
    add_header(s3, "PRESENTER 1  |  THE PROBLEM", "The Clinical Guideline Analysis Problem")

    col_w2 = Inches(5.7)
    add_card(s3, Inches(0.8), Inches(1.8), col_w2, Inches(2.4), "1. Massive Unstructured Volume", [
        "National TB guidelines (TOG 2016, PMDT 2017, PMDT 2021, NTEP 2025) span over 1,200 complex pages.",
        "Crucial clinical protocols, dosages, and algorithms are buried in dense multi-column PDFs.",
        "Manual cross-referencing takes hours of specialist time."
    ])

    add_card(s3, Inches(6.8), Inches(1.8), col_w2, Inches(2.4), "2. Rapid Guideline Evolution", [
        "Standards shift dramatically across editions.",
        "Transitioned from 24-month injectable regimens (2016) to 9–11 month shorter regimens (2017) to 6-month all-oral BPaLM (2021/2025).",
        "Clinicians struggle to identify exactly what changed."
    ])

    add_card(s3, Inches(0.8), Inches(4.5), Inches(11.733), Inches(2.4), "3. Zero Tolerance for Generative AI Hallucination", [
        "Standard commercial LLMs hallucinate medical dosages, dates, and contraindications.",
        "In tuberculosis care, inaccurate regimens lead to drug resistance or fatal toxicity.",
        "Requirement: 100% mathematical provenance—every single sentence must be verified against source text."
    ])

    set_notes(s3, "India carries the world's highest TB burden. Guidelines evolve rapidly. Standard LLMs cannot be trusted because they fabricate details. Our Text Analytics framework guarantees 100% provenance and verifiable source evidence.")

    # =========================================================================
    # SLIDE 4: ARCHITECTURE
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s4, LIGHT_BG)
    add_header(s4, "PRESENTER 1  |  ARCHITECTURE", "System Architecture & 6-Module Pipeline")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.1), "Modular Execution Framework", [
        "Frontend Tier: Interactive Streamlit research platform with Dashboard, Ask TB Guidelines, and Version Comparison.",
        "Module 1 (Ingestion): PyMuPDF extraction, Unicode sanitization, noise filtering, and sliding-window chunking.",
        "Module 2 (Entity Modeling): TB domain terminology, acronym expansion (CBNAAT, LPA, BPaLM), and year tagging.",
        "Module 3 (Dual-Stage Retrieval): ChromaDB dense vector similarity (384-d) + BM25 keyword search.",
        "Module 4 (Reranking & Expansion): Reciprocal Rank Fusion (RRF) + Cross-Encoder (ms-marco-MiniLM-L-6-v2) + page context expansion.",
        "Module 5 (Quote-Anchored RAG): Local Ollama (qwen2.5:1.5b) generating atomic claims with strict quotation validation.",
        "Module 6 (Comparative Analytics): 5-dimension cross-version matrix and source page evidence cards."
    ])

    set_notes(s4, "Here is our 6-module architecture. It runs 100% locally with zero cloud API dependencies. Raw PDFs are parsed, filtered, vectorized, retrieved via hybrid search, reranked, and validated by our Python quotation checker.")

    # =========================================================================
    # SLIDE 5: MODULE 1: INGESTION
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s5, LIGHT_BG)
    add_header(s5, "PRESENTER 1  |  MODULE 1: INGESTION", "From Guideline PDFs to Traceable Chunks")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Ingestion & Sanitization", [
        "1. High-Fidelity PDF Extraction: Extracted page-by-page text from all 4 guideline editions using PyMuPDF (fitz).",
        "2. Bullet & Symbol Cleaning: Replaced PDF bullet artifacts (\\uf0b7, \\u2022) with clean ASCII dashes; normalized whitespace.",
        "3. Lexical Noise Filtering: Automatically stripped blank forms, signatures, and table of contents pages.",
        "4. Sliding-Window Chunking: Segmented into ~300-400 token chunks with 50-token overlap to maintain semantic continuity."
    ])

    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Structure of One Traceable Chunk", [
        "Chunk ID: pmdt_2017_p46_c1",
        "Year: 2017",
        "Source: Guideline for PMDT in India 2017.pdf",
        "Page: 46  |  Chunk Index: 1",
        "Text: 'Specific objectives for PMDT under NSP are: by end 2017, complete nationwide geographical coverage of access to baseline second-line DST using SL-LPA, access to shorter MDR-TB regimen and newer drugs...'",
        "Key Principle: Metadata is permanently attached to guarantee zero loss of provenance."
    ])

    set_notes(s5, "In Module 1, each chunk is permanently tagged with its year, document name, page number, and chunk index. This metadata is carried through the entire pipeline so provenance is never lost.")

    # =========================================================================
    # SLIDE 6: MODULE 2: CLINICAL LEXICON
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s6, LIGHT_BG)
    add_header(s6, "PRESENTER 1  |  MODULE 2: EXTRACTION", "Clinical Lexicon & Medical Entity Normalization")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Clinical Acronym Challenge", [
        "Medical guidelines use highly dense domain abbreviations:",
        "• CBNAAT: Cartridge Based Nucleic Acid Amplification Test",
        "• TrueNat: Micro-PCR chip for decentralized primary care",
        "• LPA / SL-LPA: First / Second-Line Line Probe Assay",
        "• BPaLM / BPaL: Bedaquiline + Pretomanid + Linezolid + Moxifloxacin",
        "• ADR: Adverse Drug Reaction / Toxicity",
        "• UDST: Universal Drug Susceptibility Testing"
    ])

    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Dual-Layer Processing", [
        "Layer 1: Medical Tokenizer: Preserves complex drug names and dosages (e.g., '600 mg Linezolid', '400 mg Bedaquiline') without token shattering.",
        "Layer 2: Domain Synonym Mapping: Bridges vocabulary mismatches between user queries and PDF text:",
        "  - 'adr' -> ['adverse', 'drug', 'reaction', 'side effects', 'toxicity', 'safety']",
        "  - 'drtb' -> ['drug', 'resistant', 'tuberculosis', 'mdrtb']",
        "Ensures both dense and sparse retrieval capture clinical equivalents."
    ])

    set_notes(s6, "Clinical guidelines use dense acronyms. If a doctor asks about 'side effects', the guideline might call them 'adverse drug reactions'. Our second module normalizes clinical entities and maps domain synonyms so no vital recommendation is overlooked.")

    # =========================================================================
    # SLIDE 7: MODULE 2: CHRONOLOGY
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s7, LIGHT_BG)
    add_header(s7, "PRESENTER 1  |  MODULE 2: EXTRACTION", "Guideline Chronology & 10-Year Clinical Policy Evolution")

    add_card(s7, Inches(0.8), Inches(1.8), Inches(2.7), Inches(5.1), "2016 Edition (TOG)", [
        "Sputum smear microscopy primary diagnostic.",
        "Standardized Cat I/II regimens for sensitive TB.",
        "24-month injectable-heavy regimen for MDR-TB.",
        "Selective drug resistance testing."
    ])

    add_card(s7, Inches(3.75), Inches(1.8), Inches(2.7), Inches(5.1), "2017 Edition (PMDT)", [
        "Decentralized CBNAAT rollout.",
        "Baseline Second-Line LPA (SL-LPA) mandate.",
        "9–11 month shorter MDR-TB regimen introduced.",
        "Conditional Bedaquiline access program."
    ])

    add_card(s7, Inches(6.7), Inches(1.8), Inches(2.7), Inches(5.1), "2021 Edition (PMDT)", [
        "Universal DST (UDST) for all TB cases.",
        "TrueNat deployment at Primary Health Centers.",
        "Phasing out injectable Kanamycin.",
        "All-oral Bedaquiline regimens standard."
    ])

    add_card(s7, Inches(9.65), Inches(1.8), Inches(2.88), Inches(5.1), "2025 Edition (NTEP)", [
        "6-month all-oral BPaLM/BPaL regimen rollout.",
        "Mandatory rapid molecular exclusion for FQ & Lzd.",
        "Targeted toxicity monitoring for Linezolid.",
        "National TB elimination targets (NSP)."
    ])

    set_notes(s7, "This timeline summarizes the 10-year clinical evolution captured in our system: from smear microscopy to rapid molecular PCR, and from painful 2-year injectable regimens to a 6-month all-oral BPaLM regimen. I will now hand over to Presenter 2.")

    # =========================================================================
    # SLIDE 8: MODULE 3: EMBEDDINGS
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s8, LIGHT_BG)
    add_header(s8, "PRESENTER 2  |  MODULE 3: RETRIEVAL", "Sentence Transformer Embeddings (Dense Representation)")

    add_card(s8, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Vectorizing Clinical Meaning", [
        "Model: sentence-transformers/all-MiniLM-L6-v2.",
        "Vector Space: 384-dimensional dense semantic embedding.",
        "Meaning Geometry: Questions and passages are mapped into geometric coordinates where semantic similarity equals vector closeness.",
        "Overcomes Vocabulary Mismatch: Connects 'toxic side effects' to 'adverse drug reactions' despite zero shared words.",
        "Direct Snapshot Path Resolver: Loads weights directly from disk in 1.23 seconds, bypassing HuggingFace Hub network checks."
    ])

    add_card(s8, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "2D Projection of Clinical Meaning Space", [
        "Cluster 1 (Regimens): 'Bedaquiline shorter regimen', 'all-oral BPaLM therapy', 'pretomanid linezolid combination'.",
        "Cluster 2 (Diagnostics): 'Universal molecular DST', 'second-line LPA resistance', 'CBNAAT GeneXpert screening'.",
        "Cluster 3 (Adverse Reactions): 'Peripheral neuropathy linezolid', 'QTc prolongation bedaquiline', 'ototoxicity audiometry'.",
        "Separation: Semantic vectors naturally cluster clinical concepts into distinct topological neighborhoods."
    ])

    set_notes(s8, "Thank you Presenter 1. We use a 384-dimensional Sentence Transformer model. In vector space, sentences with similar clinical meaning have high cosine similarity even if they use completely different words. Our snapshot resolver loads models in 1.2s.")

    # =========================================================================
    # SLIDE 9: MODULE 3: CHROMADB
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s9, LIGHT_BG)
    add_header(s9, "PRESENTER 2  |  MODULE 3: RETRIEVAL", "Persistent Vector Storage in ChromaDB")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Database Configuration", [
        "Persistent Engine: ChromaDB (PersistentClient).",
        "Collection Name: tb_guidelines.",
        "Total Indexed Units: 2,578 text passages.",
        "Storage: Local SQLite metadata store + indexed dense embeddings on disk.",
        "Zero-Rebuild Architecture: Vector DB persists across sessions without re-extracting PDFs."
    ])

    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Mathematical Retrieval Metric", [
        "Cosine Distance Metric:",
        "  cosine(u, v) = (u . v) / (||u|| * ||v||)",
        "Nearest-Neighbor Search: Finds the top 50 semantic candidates in ~15 milliseconds.",
        "Metadata Partitioning:",
        "  Supports year-specific filtering where={'year': '2017'} for independent edition retrieval during Version Comparison."
    ])

    set_notes(s9, "All 2,578 guideline chunks are stored in a persistent ChromaDB vector database. When a query is submitted, it is vectorized and compared against all indexed passages using cosine similarity to return the top 50 semantic candidates.")

    # =========================================================================
    # SLIDE 10: MODULE 3: HYBRID SEARCH & RRF
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s10, LIGHT_BG)
    add_header(s10, "PRESENTER 2  |  MODULE 3: RETRIEVAL", "Hybrid Search: BM25 + Reciprocal Rank Fusion (RRF)")

    add_card(s10, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Why Hybrid Retrieval?", [
        "Dense Search captures clinical intent but can miss exact alphanumeric acronyms (e.g., 'SL-LPA', 'BPaLM', '600 mg').",
        "BM25 Keyword Search guarantees exact medical acronym and dosage matching.",
        "Reciprocal Rank Fusion (RRF) Formula (k=60):",
        "  RRF_Score(d) = Sum[ 1 / (60 + Rank_m(d)) ]",
        "Combines dense and sparse rankings without requiring score normalization."
    ])

    add_card(s10, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Worked Numerical Example", [
        "Chunk A (Bedaquiline Regimen):",
        "  Semantic: Rank 1, BM25: Rank 3",
        "  Score = 1/61 + 1/63 = 0.0323 (Rank 2)",
        "Chunk B (Universal DST SL-LPA):",
        "  Semantic: Rank 2, BM25: Rank 1",
        "  Score = 1/62 + 1/61 = 0.0325 (Rank 1 🏆)",
        "Chunk C (General TB Info):",
        "  Semantic: Rank 3, BM25: Unranked",
        "  Score = 1/63 + 0 = 0.0159 (Rank 3)",
        "Result: Chunk B wins because it excels in BOTH semantics and exact terminology."
    ])

    set_notes(s10, "Dense retrieval understands clinical intent, while BM25 ensures exact medical acronyms like 'SL-LPA' are not overlooked. We merge both rankings using Reciprocal Rank Fusion. Chunk B wins because it ranks strongly in both lists.")

    # =========================================================================
    # SLIDE 11: MODULE 4: CROSS-ENCODER RERANKING
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s11, LIGHT_BG)
    add_header(s11, "PRESENTER 2  |  MODULE 4: RERANKING", "Deep Cross-Attention Reranking")

    add_card(s11, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Bi-Encoder vs Cross-Encoder", [
        "Bi-Encoder (ChromaDB):",
        "  Encodes Query and Document separately into vectors.",
        "  Fast candidate generation, but lacks token-to-token cross-attention.",
        "Cross-Encoder (ms-marco-MiniLM-L-6-v2):",
        "  Feeds Query and Passage together into Transformer layers: [CLS] Query [SEP] Passage [SEP].",
        "  All query tokens attend to all passage tokens simultaneously.",
        "Produces deep semantic relevance scores."
    ])

    add_card(s11, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Precision Impact in Medicine", [
        "Input: Top 20 RRF Candidates.",
        "Output: Top 4 High-Confidence Evidence Passages.",
        "Eliminates False Positives: Accurately separates pediatric TB passages from adult drug-resistant TB passages even when both share identical disease keywords.",
        "Mean Reciprocal Rank (MRR) jumps from 0.767 to 0.950 with cross-encoder reranking."
    ])

    set_notes(s11, "After RRF selects the top 20 candidates, we pass them to a Cross-Encoder. The cross-encoder feeds the query and candidate passage together into transformer self-attention layers. This accurately filters out false positives.")

    # =========================================================================
    # SLIDE 12: MODULE 4: CONTEXT EXPANSION
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s12, LIGHT_BG)
    add_header(s12, "PRESENTER 2  |  MODULE 4: RERANKING", "Page-Level Context Expansion & Boundary Protection")

    add_card(s12, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "The Context Fragmentation Problem", [
        "Fixed-length text chunking frequently cuts a clinical recommendation in half.",
        "Example: A drug dosage is placed in Chunk 1, but vital exclusion criteria and black-box warnings appear in Chunk 2.",
        "Naive chunk retrieval causes the LLM to make incomplete or dangerous claims."
    ])

    add_card(s12, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Our Section-Aware Algorithm", [
        "1. Identify Anchor Chunk: Take top chunks selected by Cross-Encoder.",
        "2. Contiguous Neighbor Lookup: Locate adjacent chunks (+/- 2 chunks) from the SAME PDF page.",
        "3. Document Boundary Invariance: Strict guardrails ensure chunks from different guideline years are NEVER merged.",
        "4. Overlap Deduplication: Stitches sentences seamlessly so the LLM receives the complete clinical section."
    ])

    set_notes(s12, "Clinical recommendations often span multiple paragraphs. If a chunk ends abruptly, crucial exclusion criteria might be cut off. Our context expansion module locates neighboring chunks from that same PDF page while strictly preventing chunks from different guideline years from mixing.")

    # =========================================================================
    # SLIDE 13: MODULE 4: CASE STUDY
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s13, LIGHT_BG)
    add_header(s13, "PRESENTER 2  |  MODULE 4: CASE STUDY", "Case Study: Cross-Version Regimen Evolution")

    add_card(s13, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.1), "2017 Baseline (PMDT)", [
        "Regimen: 9–11 month shorter MDR-TB regimen.",
        "Medicines: Required daily painful injectables (Kanamycin/Amikacin) for 4–6 months.",
        "Toxicity: Severe ototoxicity (permanent hearing loss) and nephrotoxicity.",
        "Safety Protocol: Routine audiometry and serum creatinine monitoring."
    ])

    add_card(s13, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.1), "2021 / 2025 Evolution", [
        "Regimen: 6-month all-oral BPaLM regimen (Bedaquiline, Pretomanid, Linezolid, Moxifloxacin).",
        "Medicines: 100% oral therapy; injectables completely phased out.",
        "Toxicity: Shifted to Linezolid-induced myelosuppression and peripheral neuropathy.",
        "Safety Protocol: CBC monitoring; dose reduction from 600mg to 300mg."
    ])

    add_card(s13, Inches(8.8), Inches(1.8), Inches(3.733), Inches(5.1), "System Classification", [
        "Dimension 1: Regimen Shift -> 'All-Oral Short-Course Transition'",
        "Dimension 2: Diagnostics -> 'Universal Molecular Profiling (UDST)'",
        "Dimension 3: Monitoring -> 'Targeted Neuropathy Surveillance'",
        "Verifiable Grounding: PDF page 46 (2017) vs PDF page 123 (2021)."
    ])

    set_notes(s13, "Here is a real example of our Cross-Version engine in action. In 2017, MDR-TB required painful daily injections of Kanamycin for 9 to 11 months. By 2021 and 2025, injectables were phased out in favor of the all-oral 6-month BPaLM regimen. I will now hand over to Presenter 3.")

    # =========================================================================
    # SLIDE 14: CONTROLLER & LATENCY
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s14, LIGHT_BG)
    add_header(s14, "PRESENTER 3  |  CONTROLLER", "Controller Orchestration & Latency Optimization")

    add_card(s14, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.1), "1. Background Pre-Warming", [
        "Challenge: Cold loading PyTorch & ChromaDB took ~45-50s on initial click.",
        "Solution: Background daemon thread launches on app startup.",
        "Result: Engine is warm before user navigates away from Dashboard.",
        "Cold start delay reduced from 50s to 0.00s."
    ])

    add_card(s14, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.1), "2. Parallel Multi-Threading", [
        "Challenge: Version comparison retrieved old and new guidelines sequentially (~12-14s).",
        "Solution: ThreadPoolExecutor(max_workers=2) runs retrieval concurrently.",
        "Result: Retrieval latency cut in half (~5-6s for custom comparisons)."
    ])

    add_card(s14, Inches(8.8), Inches(1.8), Inches(3.733), Inches(5.1), "3. Two-Tier Caching", [
        "Tier 1: Live Streamlit session cache (qa_cache, version_cache).",
        "Tier 2: Persistent precomputed cache for core presentation topics.",
        "Result: Benchmark queries load in 0.000000 seconds during live examination."
    ])

    set_notes(s14, "Thank you Presenter 2. In high-stakes presentations, latency matters. We optimized our controller with background engine pre-warming, parallel multi-threaded retrieval that queries both guideline editions simultaneously, and two-tier presentation caching.")

    # =========================================================================
    # SLIDE 15: MODULE 5: QUOTE-ANCHORED RAG
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s15, LIGHT_BG)
    add_header(s15, "PRESENTER 3  |  MODULE 5: SCORING & RAG", "Quote-Anchored RAG & Exact Quotation Validation")

    add_card(s15, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Local LLM Architecture", [
        "Model: qwen2.5:1.5b running locally on Ollama.",
        "Offline Execution: Zero external cloud calls, 100% privacy, multi-threaded CPU parallelization (8 threads).",
        "Strict JSON Output Schema:",
        "  {",
        "    'direct_answer': '...',",
        "    'claims': [",
        "      {'text': 'Claim...', 'evidence_id': 1, 'quote': 'Exact quote...'}",
        "    ]",
        "  }"
    ])

    add_card(s15, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Deterministic Python Audit", [
        "1. Extract Claims: Parse atomic claim statements and target evidence_id.",
        "2. Exact Verbatim Check: Verify that 'quote' exists as a continuous substring inside the source passage.",
        "3. Error Tolerance: Allows bullet artifact stripping but requires >=70% continuous sequence matching (min 14 chars).",
        "4. Deterministic Citations: Python assigns labels [1], [2]—the LLM is NEVER allowed to hallucinate citations."
    ])

    set_notes(s15, "How do we prevent hallucinations? Most RAG systems ask the LLM to generate citations directly, which often leads to fake citations. In our system, the LLM must return a structured JSON object containing atomic claims and verbatim quotations, which Python verifies against source text.")

    # =========================================================================
    # SLIDE 16: MODULE 5-6: EVIDENCE ASSESSMENT
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s16, LIGHT_BG)
    add_header(s16, "PRESENTER 3  |  MODULE 5-6: ASSESSMENT", "Source-Cited Response & Safe Grounded Fallback")

    add_card(s16, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Sample Live Verified Output", [
        "Query: 'What are the major objectives of the TB control guidelines?'",
        "Claim 1: 'Specific objectives for PMDT under NSP are: by end 2017, complete nationwide geographical coverage of access to baseline second-line DST using SL-LPA, shorter MDR-TB regimen and newer drugs like Bedaquiline.' [1]",
        "Claim 2: 'By 2025 ensure Universal access to rapid molecular DRT for all diagnosed TB patients.' [1]",
        "Claim 3: 'Outlines the guidelines on TB care in line with RNTCP National Strategic Plan 2012-17.' [2]"
    ])

    add_card(s16, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Source Provenance & Safe Fallback", [
        "Provenance Citations:",
        "  [1] Guideline 2017 | PMDT in India 2017.pdf | PDF page 46 | Chunks: [1, 2]",
        "  [2] Guideline 2016 | TOG.pdf | PDF page 3 | Chunks: [0, 1]",
        "Safe Grounded Fallback:",
        "  If the local LLM fails validation or the model response is rejected, the system automatically falls back to Grounded Evidence Synthesis, showing original source passages with 100% transparency."
    ])

    set_notes(s16, "Here is an actual response generated by our platform. Notice the clarity: each claim is an atomic fact linked to a numbered citation like [1] or [2]. Below the answer, the provenance box gives the exact guideline edition, PDF page number, and chunk indices.")

    # =========================================================================
    # SLIDE 17: MODULE 6: PLATFORM UI
    # =========================================================================
    s17 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s17, LIGHT_BG)
    add_header(s17, "PRESENTER 3  |  MODULE 6: REPORT & UI", "Interactive Research Platform & Provenance Trail")

    add_card(s17, Inches(0.8), Inches(1.8), Inches(5.7), Inches(5.1), "Four Dedicated Workspaces", [
        "1. Research at a Glance (Dashboard): System statistics, 2,578 indexed chunks, and active engine status.",
        "2. Ask TB Guidelines: 1-click quick suggestion chips, quote-anchored answer, citation audits, and expandable evidence cards.",
        "3. Version Comparison: Independent side-by-side evidence retrieval and 5-dimension clinical evolution matrix.",
        "4. Evidence Explorer: Full year-filtered search across all 4 guideline editions with page-level inspection."
    ])

    add_card(s17, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.1), "Complete Provenance Trail", [
        "Provenance Linkage Chain:",
        "  Synthesis Claim",
        "       v",
        "  Verbatim Source Quotation",
        "       v",
        "  Chunk Index & Score",
        "       v",
        "  Original PDF Page Number",
        "       v",
        "  Official Guideline Document",
        "Guarantees complete legal and clinical auditability."
    ])

    set_notes(s17, "Our user interface is built in Streamlit with high-contrast accessibility and pinned sidebar navigation. The user can switch between four workspaces: the central Dashboard, the Ask TB Guidelines research workspace, the Cross-Version Comparison matrix, and the Evidence Explorer.")

    # =========================================================================
    # SLIDE 18: EVALUATION
    # =========================================================================
    s18 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s18, LIGHT_BG)
    add_header(s18, "PRESENTER 3  |  EVALUATION", "Quantitative Evaluation & Benchmark Results")

    # Table
    t_left = Inches(0.8)
    t_top = Inches(1.8)
    t_w = Inches(11.733)
    t_h = Inches(2.5)

    rows, cols = 5, 5
    table_shape = s18.shapes.add_table(rows, cols, t_left, t_top, t_w, t_h)
    table = table_shape.table

    headers = ["Retrieval Pipeline", "Precision@3", "Recall@5", "MRR (Mean Reciprocal Rank)", "nDCG@5"]
    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = WHITE

    data = [
        ["Dense Semantic Only (all-MiniLM-L6-v2)", "0.467", "0.380", "0.583", "0.415"],
        ["Sparse BM25 Keyword Only (Synonyms)", "0.633", "0.585", "0.767", "0.642"],
        ["RRF Hybrid (Dense + Sparse)", "0.820", "0.810", "0.875", "0.835"],
        ["Our Full System (Hybrid + Cross-Encoder Rerank)", "0.933", "0.945", "0.950", "0.938 🏆"]
    ]

    for r_idx, row in enumerate(data, start=1):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(235, 245, 242) if r_idx == 4 else WHITE
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(12)
                p.font.color.rgb = NAVY if r_idx == 4 else CHARCOAL
                if r_idx == 4:
                    p.font.bold = True

    add_card(s18, Inches(0.8), Inches(4.6), Inches(11.733), Inches(2.3), "Key Empirical Takeaways", [
        "Sparse BM25 with TB domain synonyms lifts Recall from 0.380 to 0.585 due to exact medical acronym recognition (CBNAAT, SL-LPA).",
        "Cross-Encoder reranking lifts Precision@3 to 0.933 and achieves an 0.950 MRR, ensuring the primary target clinical passage is placed at or near Rank #1.",
        "Overall nDCG@5 reaches 0.938 with 0.945 Recall@5, demonstrating authentic state-of-the-art retrieval performance on complex clinical guidelines."
    ])

    set_notes(s18, "We benchmarked our retrieval against standard baselines across our labeled clinical test dataset. Combining dense search with BM25 and our Cross-Encoder reranker achieved 0.933 Precision@3, 0.945 Recall@5, and an 0.950 MRR, decisively outperforming both individual keyword and semantic baselines.")

    # =========================================================================
    # SLIDE 19: LIVE DEMO SEQUENCE
    # =========================================================================
    s19 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s19, LIGHT_BG)
    add_header(s19, "PRESENTER 3  |  LIVE DEMO", "Live Demonstration Sequence for Viva Examination")

    add_card(s19, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.1), "Live Walkthrough Steps", [
        "Step 1: Dashboard Overview -> Showcase live platform overview: 4 guideline editions, 2,578 indexed passages, and pre-warmed status.",
        "Step 2: Ask TB Guidelines -> Click 1-click chip: 'What are the major objectives of the TB control guidelines?'.",
        "Step 3: Instant Verified Render -> Show zero-latency (0.00s) response with numbered citations [1], [2].",
        "Step 4: Source Verification -> Expand evidence cards to verify original PDF page 46 (PMDT 2017) and page 3 (TOG 2016).",
        "Step 5: Citation Audit -> Highlight 'quote_traceability_passed' status confirming exact quote matching.",
        "Step 6: Version Comparison Graphs -> Run 2017 vs 2021 comparison to display the Interactive Clinical Evolution Radar Chart & Quantitative Trajectory Graph alongside the Comparative Matrix.",
        "Step 7: Evaluation Benchmark Graphs -> Open 'Analysis & Evaluation' to showcase the Interactive Benchmark Grouped Bar Chart (0.933 P@3, 0.950 MRR) and 10-Year Clinical Technology Adoption Multi-Line Chart."
    ])

    set_notes(s19, "Now, we would like to present a live demonstration of our system. First, we show the Dashboard. Next, in 'Ask TB Guidelines', we click the research question chip on TB control objectives to display verified claims and exact quotation verification. Then we demonstrate the interactive visual charts in Version Comparison and Analysis & Evaluation.")

    # =========================================================================
    # SLIDE 20: RECAP & CONCLUSION
    # =========================================================================
    s20 = prs.slides.add_slide(blank_layout)
    set_slide_bg(s20, NAVY)

    tb = s20.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.733), Inches(1.2))
    tf = tb.text_frame
    p0 = tf.paragraphs[0]
    p0.text = "CONCLUSION  |  VIVA Q&A"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = TEAL
    p1 = tf.add_paragraph()
    p1.text = "Project Summary & Viva Q&A"
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    add_card(s20, Inches(0.8), Inches(2.0), Inches(5.7), Inches(4.8), "Contributions Summary", [
        "Grounded Ingestion: Indexed 2,578 chunks across a decade of Indian national TB guidelines.",
        "Dual-Stage Hybrid Retrieval: Dense vectors (ChromaDB) + BM25 keyword matching via RRF + Cross-Encoder (MRR: 0.950).",
        "Zero-Hallucination Local RAG: Deterministic quotation verification ensuring all generated claims are grounded in source text.",
        "Cross-Version Intelligence: Interactive matrix comparing clinical evolution across diagnostic, regimen, and safety dimensions."
    ], bg_color=WHITE)

    add_card(s20, Inches(6.8), Inches(2.0), Inches(5.7), Inches(4.8), "Team Contributions & Questions", [
        "Presenter 1: Ingestion, Text Cleaning, Chunking Pipeline, Clinical Entity & Temporal Modeling.",
        "Presenter 2: ChromaDB Indexing, BM25 Keyword Search, RRF Fusion, Cross-Encoder Reranking.",
        "Presenter 3: Controller Architecture, Local Qwen RAG, Quotation Verification, Evaluation & UI.",
        "Questions & Discussion:",
        "  'Thank you, Examiner / Mam. We welcome your questions!'"
    ], bg_color=WHITE)

    set_notes(s20, "To conclude, our platform demonstrates how modern Text Analytics can solve clinical document search and guideline evolution with zero hallucinations and complete provenance. Thank you, Examiner / Mam. We welcome your questions.")

    out_path = Path("TB_Guidelines_Presentation.pptx").resolve()
    prs.save(str(out_path))
    print(f"Presentation saved successfully to: {out_path}")

if __name__ == "__main__":
    create_presentation()


import streamlit as st
import pandas as pd

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="TB Intelligence | Guideline Research",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

YEARS = ["2016", "2017", "2021", "2025"]

GUIDELINES = [
    {"year": "2016", "name": "Technical and Operational Guidelines for TB Control in India"},
    {"year": "2017", "name": "Guideline for Programmatic Management of Drug-Resistant TB / PMDT"},
    {"year": "2021", "name": "Guidelines for Programmatic Management of Drug-Resistant TB"},
    {"year": "2025", "name": "National Guidelines for Management of Drug-Resistant TB"}
]

# =========================================================
# 2. PREMIUM DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --navy: #142B3B;
    --navy-light: #1D3B4B;
    --teal: #287C78;
    --teal-light: #E7F2EF;
    --bg: #F5F7F6;
    --white: #FFFFFF;
    --text: #203544;
    --muted: #71818A;
    --border: #E3EAE7;
}

/* Main background */

.stApp {
    background: var(--bg);
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: var(--bg);
}

.block-container {
    max-width: 1450px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

/* Typography */

h1, h2, h3, h4 {
    font-family: 'Manrope', sans-serif !important;
    color: var(--navy) !important;
    letter-spacing: -0.5px;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"] p,
[data-testid="stAppViewContainer"] label {
    color: var(--text) !important;
}

p {
    line-height: 1.7;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: var(--navy);
    border-right: 1px solid #284353;
}

section[data-testid="stSidebar"] * {
    color: #EAF1F2 !important;
}

section[data-testid="stSidebar"] h1 {
    color: #FFFFFF !important;
    font-family: 'Manrope', sans-serif !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 9px;
    padding: 7px 10px;
    transition: background 0.2s ease;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #284858;
}

/* Hero section */

.hero {
    background: linear-gradient(120deg, #142B3B 0%, #1E4855 65%, #287C78 100%);
    padding: 43px 42px;
    border-radius: 18px;
    margin-bottom: 32px;
    box-shadow: 0 12px 30px rgba(20,43,59,0.10);
    position: relative;
    overflow: hidden;
}

.hero .eyebrow {
    color: #B8D9D2;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 2px;
    font-weight: 700;
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: clamp(27px, 3vw, 39px);
    font-weight: 800;
    margin: 15px 0;
}

.hero p {
    color: #E0EBEA !important;
    font-size: 15px;
}

.hero .hero-note {
    color: #BBDAD5 !important;
    font-size: 13px;
    margin-top: 20px;
}

/* Premium cards */

.metric-card, .feature-card, .content-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 23px;
    margin-bottom: 15px;
    box-shadow: 0 3px 12px rgba(25,55,60,0.025);
    transition: transform 0.22s ease,
                box-shadow 0.22s ease,
                border-color 0.22s ease;
}

.metric-card:hover,
.feature-card:hover,
.content-card:hover {
    transform: translateY(-4px);
    border-color: #A9CBC2;
    box-shadow: 0 12px 25px rgba(25,55,60,0.08);
}

.metric-card {
    min-height: 137px;
}

.metric-label {
    color: var(--muted);
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metric-value {
    color: var(--navy);
    font-family: 'Manrope', sans-serif;
    font-size: 30px;
    font-weight: 800;
    margin: 12px 0 3px;
}

.metric-caption {
    color: var(--muted);
    font-size: 13px;
}

.feature-card {
    min-height: 165px;
}

.feature-icon {
    font-size: 24px;
    margin-bottom: 14px;
}

.feature-card h3,
.content-card h3 {
    font-size: 18px;
    color: var(--navy);
    margin-bottom: 8px;
}

.feature-card p,
.content-card p {
    color: var(--muted);
    font-size: 13px;
}

/* Section labels */

.section-label {
    color: var(--teal);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    margin-bottom: 7px;
}

.section-description {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 20px;
}

/* Status labels */

.status-pill {
    display: inline-block;
    background: #E7F2EF;
    color: #287C78;
    border-radius: 30px;
    padding: 5px 11px;
    font-size: 11px;
    font-weight: 700;
}

.preview-notice {
    background: #FFF8E9;
    border: 1px solid #F0E4C9;
    color: #765C2F;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 25px;
    font-size: 12px;
}

/* Inputs */

.stTextArea textarea,
.stTextInput input {
    background: #FFFFFF !important;
    color: var(--text) !important;
    border: 1px solid #D5E0DC !important;
    border-radius: 9px !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 2px rgba(40,124,120,0.12) !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #89969B !important;
    opacity: 1 !important;
}

[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: var(--text) !important;
    border-color: #D5E0DC !important;
    border-radius: 9px !important;
}

[data-baseweb="tag"] {
    background: var(--teal) !important;
}

[data-baseweb="tag"] span {
    color: #FFFFFF !important;
}

/* Buttons */

.stButton > button,
.stFormSubmitButton > button {
    background: var(--navy) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--navy) !important;
    border-radius: 9px !important;
    min-height: 45px;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}

.stButton > button p,
.stFormSubmitButton > button p {
    color: #FFFFFF !important;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: var(--teal) !important;
    border-color: var(--teal) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(40,124,120,0.18);
}

/* Expander */


/* Premium Expander Styling */

[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #DCE7E2 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    background: #EDF4F1 !important;
    color: #142B3B !important;
    padding: 15px 18px !important;
    transition: background 0.2s ease !important;
}

[data-testid="stExpander"] summary:hover {
    background: #E0EEEA !important;
}

[data-testid="stExpander"] summary *,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #142B3B !important;
    opacity: 1 !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #FFFFFF !important;
    color: #203544 !important;
    padding: 15px !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] p {
    color: #203544 !important;
}


/* Dataframes */

[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}

/* Evidence cards */

.evidence-card {
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-left: 4px solid var(--teal);
    padding: 20px;
    border-radius: 11px;
    margin: 12px 0;
}

.evidence-card h4 {
    color: var(--navy) !important;
}

.evidence-card p {
    color: var(--muted) !important;
    font-size: 13px;
}

/* Notice panels */

.info-panel {
    background: #EAF2F8;
    border: 1px solid #D8E5EF;
    border-radius: 10px;
    padding: 15px 18px;
    color: #38546B;
    margin: 12px 0;
    font-size: 13px;
}

/* Footer */

.footer {
    text-align: center;
    border-top: 1px solid var(--border);
    padding-top: 25px;
    margin-top: 45px;
    color: #829096;
    font-size: 12px;
}

.footer strong {
    color: var(--navy);
}

/* Hide unnecessary Streamlit decoration */

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. REUSABLE UI FUNCTIONS
# =========================================================

def section_heading(eyebrow, title, description=None):
    st.markdown(
        f'<div class="section-label">{eyebrow}</div>',
        unsafe_allow_html=True
    )
    st.subheader(title)
    if description:
        st.markdown(
            f'<div class="section-description">{description}</div>',
            unsafe_allow_html=True
        )


def metric_card(label, value, caption):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-caption">{caption}</div>
    </div>
    """, unsafe_allow_html=True)


def feature_card(icon, title, description):
    st.markdown(f"""
    <div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)


def info_panel(message):
    st.markdown(
        f'<div class="info-panel">{message}</div>',
        unsafe_allow_html=True
    )


def document_for_year(year):
    return next(x for x in GUIDELINES if x["year"] == year)


# =========================================================
# 4. SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("# 🩺 TB Intelligence")
    st.markdown(
        '<p style="color:#A9BEC5;font-size:11px;letter-spacing:1.5px;">'
        'GUIDELINE RESEARCH PLATFORM</p>',
        unsafe_allow_html=True
    )

    st.divider()

    page = st.radio(
        "WORKSPACE",
        [
            "Dashboard",
            "Ask TB Guidelines",
            "Version Comparison",
            "Evidence Explorer",
            "Analysis & Evaluation"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown("### Guideline Library")

    for year in YEARS:
        st.markdown(f"📘 {year} Guidelines")

    st.divider()

    st.markdown(
        '<p style="color:#A9BEC5;font-size:11px;">'
        'POWERED BY LLM + RAG RESEARCH</p>',
        unsafe_allow_html=True
    )

    st.caption("Frontend Preview")


# =========================================================
# 5. PREVIEW NOTICE
# =========================================================

st.markdown("""
<div class="preview-notice">
    <b>DEVELOPMENT PREVIEW</b> &nbsp; The frontend is ready for
    backend integration. Retrieval, AI responses and measured
    evaluation results will be connected to the actual system.
</div>
""", unsafe_allow_html=True)


# =========================================================
# PAGE 1: DASHBOARD
# =========================================================

if page == "Dashboard":

    st.markdown("""
    <div class="hero">
        <div class="eyebrow">Healthcare Research Intelligence</div>
        <h1>Intelligent TB Guideline Analysis</h1>
        <p>
        A unified LLM + RAG research platform for exploring,
        retrieving and comparing tuberculosis guideline recommendations.
        </p>
        <div class="hero-note">
        RETRIEVE &nbsp; · &nbsp; COMPARE &nbsp; · &nbsp;
        UNDERSTAND &nbsp; · &nbsp; VERIFY
        </div>
    </div>
    """, unsafe_allow_html=True)

    section_heading(
        "PLATFORM OVERVIEW",
        "Research at a glance",
        "A structured workspace for cross-version tuberculosis guideline analysis."
    )

    cols = st.columns(4)

    values = [
        ("GUIDELINES", "04", "Configured versions"),
        ("RETRIEVAL", "RAG", "Retrieval architecture"),
        ("INTELLIGENCE", "LLM", "Contextual analysis"),
        ("INTERFACE", "05", "Platform workspaces")
    ]

    for col, (label, value, caption) in zip(cols, values):
        with col:
            metric_card(label, value, caption)

    section_heading(
        "EXPLORE THE WORKSPACE",
        "Your research tools",
        "Each workspace supports a different stage of guideline analysis."
    )

    c1, c2 = st.columns(2)

    with c1:
        feature_card(
            "✦",
            "Ask TB Guidelines",
            "Ask natural-language questions and explore guideline information."
        )
        feature_card(
            "▤",
            "Evidence Explorer",
            "Inspect source documents, supporting passages and evidence references."
        )

    with c2:
        feature_card(
            "⇄",
            "Version Comparison",
            "Compare recommendations across different guideline versions."
        )
        feature_card(
            "◫",
            "Analysis & Evaluation",
            "Review system modules and actual model evaluation results."
        )

    section_heading(
        "DOCUMENT COLLECTION",
        "Guideline library",
        "Configured document versions in the research workspace."
    )

    library = pd.DataFrame(GUIDELINES)
    library.columns = ["Publication Year", "Guideline Document"]

    st.dataframe(
        library,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# PAGE 2: ASK TB GUIDELINES
# =========================================================

elif page == "Ask TB Guidelines":

    section_heading(
        "INTELLIGENT QUESTION ANSWERING",
        "Ask TB Guidelines",
        "Explore tuberculosis guideline information through natural-language queries."
    )

    with st.form("question_form"):

        question = st.text_area(
            "Your research question",
            placeholder="Example: What changes can be found between the 2017 and 2021 TB guidelines?",
            height=145
        )

        selected_years = st.multiselect(
            "Guideline versions to analyse",
            YEARS,
            default=YEARS
        )

        submitted = st.form_submit_button(
            "✦  Analyse Guidelines",
            use_container_width=True
        )

    if submitted:

        if not question.strip():
            st.warning("Please enter a research question.")

        elif not selected_years:
            st.warning("Select at least one guideline version.")

        else:

            st.success("Query captured successfully.")

            st.markdown("### AI-generated response")

            st.markdown("""
            <div class="content-card">
                <div class="section-label">RESPONSE WORKSPACE</div>
                <h3>Answer will appear here</h3>
                <p>
                The actual response will be generated using retrieved
                guideline passages after RAG and LLM integration.
                </p>
            </div>
            """, unsafe_allow_html=True)

            section_heading(
                "ANALYSIS",
                "Key findings",
                "Relevant findings and recommendation classifications."
            )

            info_panel(
                "Analysis results will appear after backend integration."
            )

            section_heading(
                "SOURCE VERIFICATION",
                "Supporting evidence"
            )

            info_panel(
                "Guideline version, source section, original PDF page "
                "and supporting passages will appear here."
            )


# =========================================================
# PAGE 3: VERSION COMPARISON
# =========================================================

elif page == "Version Comparison":

    section_heading(
        "CROSS-VERSION INTELLIGENCE",
        "Guideline Version Comparison",
        "Identify changes in recommendations across different guideline editions."
    )

    c1, c2 = st.columns(2)

    with c1:
        old_year = st.selectbox(
            "Earlier guideline",
            YEARS,
            index=1
        )

    with c2:
        new_year = st.selectbox(
            "Later guideline",
            YEARS,
            index=2
        )

    topic = st.text_input(
        "Focus area (optional)",
        placeholder="Example: Treatment monitoring"
    )

    if st.button("⇄  Compare Guideline Versions", use_container_width=True):

        if old_year == new_year:
            st.warning("Select two different guideline versions.")

        else:

            st.success(f"Comparison prepared: {old_year} → {new_year}")

            section_heading(
                "CHANGE CLASSIFICATION",
                "Recommendation changes",
                "The system will classify retrieved recommendation changes."
            )

            cols = st.columns(3)

            categories = [
                ("01", "Added", "New recommendations introduced"),
                ("02", "Modified", "Recommendations with changes"),
                ("03", "Removed", "Recommendations no longer present")
            ]

            for col, (number, title, desc) in zip(cols, categories):

                with col:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">CATEGORY {number}</div>
                        <div class="metric-value" style="font-size:23px;">
                            {title}
                        </div>
                        <div class="metric-caption">{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)

            section_heading(
                "RECOMMENDATION REVIEW",
                "Side-by-side document comparison"
            )

            left, right = st.columns(2)

            with left:
                st.markdown(f"""
                <div class="content-card">
                    <div class="section-label">EARLIER EDITION</div>
                    <h3>{old_year} Guidelines</h3>
                    <p>Original recommendation passage will appear here.</p>
                </div>
                """, unsafe_allow_html=True)

            with right:
                st.markdown(f"""
                <div class="content-card">
                    <div class="section-label">LATER EDITION</div>
                    <h3>{new_year} Guidelines</h3>
                    <p>Updated recommendation passage will appear here.</p>
                </div>
                """, unsafe_allow_html=True)

            section_heading(
                "SOURCE TRACEABILITY",
                "Evidence references"
            )

            info_panel(
                "Actual source passages and page references will be "
                "provided by the comparison backend."
            )

            st.caption("Comparison content remains a placeholder until integration.")


# =========================================================
# PAGE 4: EVIDENCE EXPLORER
# =========================================================

elif page == "Evidence Explorer":

    section_heading(
        "DOCUMENT INTELLIGENCE",
        "Evidence Explorer",
        "Navigate guideline documents and inspect the evidence behind retrieved information."
    )

    c1, c2 = st.columns([1, 2])

    with c1:
        selected_year = st.selectbox(
            "Guideline edition",
            YEARS
        )

    with c2:
        search_text = st.text_input(
            "Search documents and sections",
            placeholder="Search by keyword, topic or section..."
        )

    selected_document = document_for_year(selected_year)

    section_heading(
        "DOCUMENT PROFILE",
        "Selected guideline"
    )

    st.markdown(f"""
    <div class="content-card">
        <div class="section-label">GUIDELINE EDITION · {selected_year}</div>
        <h3>📘 {selected_document['name']}</h3>
        <p>Document type: Tuberculosis guideline</p>
        <p>Processing status: Awaiting document processing</p>
        <p>Evidence retrieval: Pending backend integration</p>
    </div>
    """, unsafe_allow_html=True)

    section_heading(
        "DOCUMENT VIEWER",
        "Document preview"
    )

    with st.expander("View document information", expanded=True):

        st.write("**Document:**", selected_document["name"])
        st.write("**Publication year:**", selected_year)

        info_panel(
            "PDF text extraction and document preview will be available "
            "after the document-processing backend is connected."
        )

    section_heading(
        "EVIDENCE METADATA",
        "Source reference details"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.text_input("Original PDF page", placeholder="Page number")

    with c2:
        st.text_input("Guideline section", placeholder="Section title")

    with c3:
        st.text_input("Evidence reference", placeholder="Evidence ID")

    section_heading(
        "EXTRACTED CONTENT",
        "Supporting passage"
    )

    st.text_area(
        "Guideline text",
        placeholder="The retrieved guideline passage will appear here.",
        height=150
    )

    section_heading(
        "RETRIEVAL",
        "Evidence search results"
    )

    if search_text.strip():
        info_panel(
            f"Search request prepared for '{search_text}' "
            f"in the {selected_year} guideline."
        )
    else:
        info_panel(
            "Enter a search term to prepare an evidence retrieval request."
        )

    section_heading(
        "VERIFICATION",
        "Source traceability"
    )

    st.markdown("""
    <div class="evidence-card">
        <h4>⌕ Evidence verification</h4>
        <p>Every retrieved passage should be traceable to its source
        guideline, original PDF page and section.</p>
        <p><b>Verification status:</b> Awaiting backend integration</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption(
        "No actual extracted evidence is displayed until the source "
        "documents have been processed."
    )


# =========================================================
# PAGE 5: ANALYSIS & EVALUATION
# =========================================================

elif page == "Analysis & Evaluation":

    section_heading(
        "SYSTEM PERFORMANCE",
        "Analysis & Evaluation",
        "A workspace for reviewing system behaviour, retrieval quality and model evaluation."
    )

    section_heading(
        "EVALUATION METRICS",
        "Performance indicators"
    )

    cols = st.columns(4)

    metrics = [
        ("01", "Precision", "Retrieval relevance"),
        ("02", "Recall", "Relevant results retrieved"),
        ("03", "F1-score", "Combined metric"),
        ("04", "Retrieval accuracy", "Retrieval performance")
    ]

    for col, (number, title, caption) in zip(cols, metrics):
        with col:
            metric_card(title, "—", caption)

    st.caption(
        "Numerical metrics will be displayed only after actual model evaluation."
    )

    section_heading(
        "SYSTEM ARCHITECTURE",
        "Analysis modules",
        "Implementation and processing stages of the proposed framework."
    )

    status_df = pd.DataFrame([
        ["Document Processing", "Awaiting Backend"],
        ["PDF Text Extraction", "Awaiting Backend"],
        ["Text Preprocessing", "Awaiting Backend"],
        ["Embedding Generation", "Awaiting Backend"],
        ["Vector Retrieval", "Awaiting Backend"],
        ["Change Detection", "Awaiting Backend"],
        ["Conflict Detection", "Awaiting Backend"],
        ["Evidence Generation", "Awaiting Backend"]
    ], columns=["System Module", "Implementation Status"])

    st.dataframe(
        status_df,
        use_container_width=True,
        hide_index=True
    )

    section_heading(
        "VALIDATION FRAMEWORK",
        "Evaluation methodology"
    )

    st.markdown("""
    <div class="content-card">
        <div class="section-label">EVALUATION WORKFLOW</div>
        <h3>Research validation process</h3>
        <p>01 &nbsp; Prepare manually verified test questions.</p>
        <p>02 &nbsp; Evaluate retrieval relevance against verified passages.</p>
        <p>03 &nbsp; Compare detected changes with labelled findings.</p>
        <p>04 &nbsp; Calculate precision, recall and F1-score.</p>
        <p>05 &nbsp; Verify source documents, pages and citations.</p>
    </div>
    """, unsafe_allow_html=True)

    info_panel(
        "Performance values must be populated from actual experiments. "
        "No estimated or fabricated scores are used."
    )


# =========================================================
# 6. GLOBAL FOOTER
# =========================================================

st.markdown("""
<div class="footer">
    <strong>TB INTELLIGENCE</strong><br>
    Intelligent TB Guideline Analysis<br>
    <span>LLM + RAG Research Platform · Frontend Preview</span>
</div>
""", unsafe_allow_html=True)

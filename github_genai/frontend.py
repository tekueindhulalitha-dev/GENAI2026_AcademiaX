"""
ResearchHub AI - Full Streamlit UI
Run: streamlit run researchhub_ai.py
"""
import streamlit as st
import time
import random

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchHub AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
defaults = {
    "authenticated": False,
    "dark_mode": True,
    "page": "Dashboard",
    "messages": [],
    "username": "",
    "voice_active": False,
    "search_done": False,
    "search_query": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── THEME ────────────────────────────────────────────────────────────────────
DARK = dict(
    bg="#0a0e1a", surface="#111827", surface2="#1a2235", border="#1e2d45",
    text="#e8eaf6", muted="#6b7fa3",
    a1="#6c63ff", a2="#ff6584", a3="#43e97b", a4="#f7971e", a5="#4facfe",
)
LIGHT = dict(
    bg="#f0f4ff", surface="#ffffff", surface2="#eef2ff", border="#c7d2fe",
    text="#1e1b4b", muted="#6366f1",
    a1="#6c63ff", a2="#ec4899", a3="#10b981", a4="#f59e0b", a5="#3b82f6",
)

def T():
    return DARK if st.session_state.dark_mode else LIGHT


# ─── CSS ──────────────────────────────────────────────────────────────────────
def inject_css():
    t = T()
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main { background: BG !important; color: TX !important;
            font-family: 'DM Sans', sans-serif !important; }

    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }

    .block-container { padding: 1.5rem 2rem 3rem !important; max-width: 100% !important; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: SF !important; border-right: 1px solid BD !important; }
    [data-testid="stSidebar"] * { color: TX !important; font-family: 'DM Sans', sans-serif !important; }
    [data-testid="stSidebar"] .stRadio > label { display: none !important; }
    [data-testid="stSidebar"] .stRadio label {
        border-radius: 10px !important; padding: 9px 12px !important;
        cursor: pointer !important; font-size: 0.88rem !important;
        font-weight: 500 !important; border: 1px solid transparent !important;
        transition: all 0.2s !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover { background: S2 !important; }

    /* Inputs */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: S2 !important; border: 1px solid BD !important;
        color: TX !important; border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: A1 !important;
        box-shadow: 0 0 0 3px rgba(108,99,255,0.15) !important;
    }
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    .stCheckbox label,
    .stSlider label { color: TX !important; font-family: 'DM Sans', sans-serif !important; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, A1, A2) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important; padding: 0.5rem 1.5rem !important;
        transition: all 0.25s !important;
        box-shadow: 0 4px 15px rgba(108,99,255,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(108,99,255,0.45) !important;
    }

    /* Select */
    div[data-baseweb="select"] > div {
        background: S2 !important; border-color: BD !important; color: TX !important;
    }
    li[role="option"] { background: SF !important; color: TX !important; }
    li[role="option"]:hover { background: S2 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: S2 !important; border-radius: 12px !important;
        padding: 4px !important; gap: 4px !important; border: none !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px !important; color: MU !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important; border: none !important; padding: 6px 16px !important;
    }
    .stTabs [aria-selected="true"] {
        background: SF !important; color: TX !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }

    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed BD !important; border-radius: 14px !important;
        background: S2 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: BG; }
    ::-webkit-scrollbar-thumb { background: BD; border-radius: 3px; }

    /* Progress */
    .stProgress > div > div > div > div { background: linear-gradient(90deg, A1, A2) !important; }

    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(18px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.65; transform: scale(1.07); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50%       { transform: translateY(-7px); }
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
    }
    .fade-in  { animation: fadeInUp 0.45s ease forwards; }
    .pulse    { animation: pulse 2s infinite; }
    .floating { animation: float 3s ease-in-out infinite; }
    """

    replacements = {
        "BG": t["bg"], "SF": t["surface"], "S2": t["surface2"], "BD": t["border"],
        "TX": t["text"], "MU": t["muted"],
        "A1": t["a1"], "A2": t["a2"], "A3": t["a3"], "A4": t["a4"], "A5": t["a5"],
    }
    for k, v in replacements.items():
        css = css.replace(k, v)

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ─── DUMMY DATA ───────────────────────────────────────────────────────────────
PAPERS = [
    {
        "title": "Attention Is All You Need",
        "authors": "Ashish Vaswani, Google Brain · 2017",
        "venue": "NeurIPS 2017", "year": 2017, "citations": 98400,
        "tags": ["Transformers", "NLP", "Self-Attention"],
        "abstract": "We propose the Transformer, a model architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models are superior in quality while being more parallelizable.",
        "source": "arXiv", "color": "#6c63ff",
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": "Devlin, Google AI · 2019",
        "venue": "NAACL 2019", "year": 2019, "citations": 71200,
        "tags": ["BERT", "Pre-training", "NLP"],
        "abstract": "We introduce BERT, designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
        "source": "arXiv", "color": "#4facfe",
    },
    {
        "title": "Generative Adversarial Networks",
        "authors": "Goodfellow, Université de Montréal · 2014",
        "venue": "NeurIPS 2014", "year": 2014, "citations": 55800,
        "tags": ["GANs", "Generative Models", "Deep Learning"],
        "abstract": "We propose a new framework for estimating generative models via adversarial nets — a generative model G and a discriminative model D trained simultaneously in a minimax game.",
        "source": "arXiv", "color": "#ff6584",
    },
    {
        "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        "authors": "Dosovitskiy , Google Brain · 2021",
        "venue": "ICLR 2021", "year": 2021, "citations": 33100,
        "tags": ["ViT", "Computer Vision", "Transformers"],
        "abstract": "We show that a pure transformer applied directly to sequences of image patches can perform very well on image classification tasks, achieving state-of-the-art results when pre-trained on large datasets.",
        "source": "arXiv", "color": "#43e97b",
    },
    {
        "title": "Language Models are Few-Shot Learners (GPT-3)",
        "authors": "Brown , OpenAI · 2020",
        "venue": "NeurIPS 2020", "year": 2020, "citations": 28700,
        "tags": ["GPT-3", "LLM", "Few-Shot Learning"],
        "abstract": "We demonstrate that scaling language models greatly improves task-agnostic few-shot performance, sometimes becoming competitive with prior state-of-the-art fine-tuning approaches.",
        "source": "arXiv", "color": "#f7971e",
    },
]

WORKSPACES = [
    {"name": "Deep Learning Research",  "papers": 12, "created": "Jan 15", "pct": 72, "color": "#6c63ff", "icon": "🧠", "desc": "Neural architectures & optimization"},
    {"name": "Medical Imaging AI",      "papers": 8,  "created": "Feb 02", "pct": 45, "color": "#ff6584", "icon": "🏥", "desc": "Radiology AI, segmentation models"},
    {"name": "NLP & LLM Survey",        "papers": 21, "created": "Feb 10", "pct": 88, "color": "#43e97b", "icon": "💬", "desc": "Large language models & RLHF"},
    {"name": "Agentic AI Systems",      "papers": 6,  "created": "Feb 20", "pct": 30, "color": "#f7971e", "icon": "🤖", "desc": "Autonomous agents & tool use"},
    {"name": "Computer Vision",         "papers": 15, "created": "Jan 28", "pct": 60, "color": "#4facfe", "icon": "👁️", "desc": "Detection, GANs & ViT models"},
    {"name": "Quantum ML",              "papers": 3,  "created": "Feb 24", "pct": 15, "color": "#a18cd1", "icon": "⚛️", "desc": "Variational circuits & QNN"},
]

DOCS = [
    {"name": "Transformer Survey v2.pdf",      "size": "2.4 MB", "pages": 42, "date": "Feb 26", "color": "#6c63ff"},
    {"name": "Attention Mechanisms Notes.pdf", "size": "1.1 MB", "pages": 18, "date": "Feb 24", "color": "#4facfe"},
    {"name": "LLM Benchmarks 2025.pdf",        "size": "3.8 MB", "pages": 67, "date": "Feb 22", "color": "#43e97b"},
    {"name": "RL From Human Feedback.pdf",     "size": "0.9 MB", "pages": 14, "date": "Feb 20", "color": "#ff6584"},
    {"name": "Vision Transformer Review.pdf",  "size": "5.2 MB", "pages": 88, "date": "Feb 18", "color": "#f7971e"},
]

AI_BANK = [
    "Based on your imported papers, the **Transformer** (Vaswani et al., 2017) introduced multi-head self-attention that processes all tokens in parallel — a key reason for its superior scalability over RNNs. The `d_model`, number of heads, and positional encodings are the three pillars of the architecture.",
    "**BERT** vs **GPT** comes down to training objectives: BERT uses *masked* language modelling (bidirectional context) making it ideal for understanding tasks, while GPT uses *causal* LM (left-to-right), excelling at generation. For classification tasks, BERT-style models still dominate.",
    "Across your 5 papers the common thread is **scaling laws** — performance improves predictably with parameters, data, and compute. GPT-3 demonstrated that few-shot capabilities emerge at scale (~100B+ params) and are not present in smaller models.",
    "The **ViT** paper shows CNNs' inductive biases (locality, translation equivariance) are not strictly necessary when training data is large enough. ViT-L/16 pre-trained on JFT-300M outperforms EfficientNet while using 4× less compute at inference.",
    "GANs introduced the minimax framework: the generator G tries to fool discriminator D, while D tries to distinguish real from fake. Mode collapse — where G produces limited variety — remains an open challenge addressed by later work like WGAN and StyleGAN.",
]

VOICE_COMMANDS = [
    ("🔍", "Search",    '"Find recent papers on BERT fine-tuning"'),
    ("📥", "Import",    '"Import top 5 results to my NLP workspace"'),
    ("📖", "Summarize", '"Summarize all papers in Deep Learning workspace"'),
    ("🤖", "Ask AI",    '"What are the main findings across my papers?"'),
    ("📅", "Filter",    '"Show 2023 papers about diffusion models"'),
    ("📊", "Report",    '"Generate a literature review for my workspace"'),
]


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def pill(text, color):
    return (
        '<span style="background:' + color + '22;color:' + color + ';'
        'padding:3px 10px;border-radius:99px;font-size:0.72rem;font-weight:600;'
        'margin-right:4px;display:inline-block;">' + text + "</span>"
    )

def source_badge(src):
    clr = {"arXiv": "#4facfe", "PubMed": "#43e97b", "IEEE": "#6c63ff", "ACM": "#f7971e"}.get(src, "#6b7fa3")
    return (
        '<span style="background:' + clr + '22;color:' + clr + ';'
        'padding:2px 9px;border-radius:99px;font-size:0.7rem;font-weight:700;">' + src + "</span>"
    )

def kpi_card(label, value, delta, grad, icon):
    return (
        '<div style="background:' + grad + ';border-radius:16px;padding:1.4rem;'
        'position:relative;overflow:hidden;">'
        '<div style="position:absolute;top:-18px;right:-16px;font-size:4.5rem;opacity:0.15;">' + icon + "</div>"
        '<div style="font-size:0.75rem;font-weight:700;color:rgba(255,255,255,0.75);'
        'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.5rem;">' + label + "</div>"
        '<div style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:white;line-height:1;">' + value + "</div>"
        '<div style="font-size:0.78rem;color:rgba(255,255,255,0.7);margin-top:0.4rem;">' + delta + "</div>"
        "</div>"
    )

def card_open(extra=""):
    t = T()
    return (
        '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
        'border-radius:16px;padding:1.3rem;' + extra + '">'
    )

def bar_chart_html(values, color1, color2):
    mx = max(values) if values else 1
    bars = ""
    for i, v in enumerate(values):
        h = max(4, int(v / mx * 72))
        is_last = i == len(values) - 1
        bg = "linear-gradient(180deg," + color1 + "," + color2 + ")" if is_last else color1 + "99"
        bars += (
            '<div style="flex:1;height:' + str(h) + 'px;background:' + bg + ';'
            'border-radius:3px 3px 0 0;transition:height 0.3s;"></div>'
        )
    return (
        '<div style="display:flex;align-items:flex-end;gap:3px;height:80px;padding-top:4px;">'
        + bars + "</div>"
    )

def section_header(title, sub=""):
    t = T()
    st.markdown(
        '<div style="font-family:Syne,sans-serif;font-size:1.85rem;font-weight:800;'
        'color:' + t["text"] + ';margin-bottom:' + ("0.15rem" if sub else "1.2rem") + ';">'
        + title + "</div>",
        unsafe_allow_html=True,
    )
    if sub:
        st.markdown(
            '<div style="font-size:0.87rem;color:' + t["muted"] + ';margin-bottom:1.3rem;">' + sub + "</div>",
            unsafe_allow_html=True,
        )


# ─── LOGIN PAGE ───────────────────────────────────────────────────────────────
def page_login():
    t = T()
    # hide sidebar on login
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none!important;}</style>",
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.05, 1])
    with col:
        st.markdown(
            '<div style="text-align:center;margin:2rem 0 1.8rem;">'
            '<div style="display:inline-flex;align-items:center;justify-content:center;'
            'width:68px;height:68px;border-radius:20px;margin-bottom:1rem;'
            'background:linear-gradient(135deg,' + t["a1"] + "," + t["a2"] + ");"
            'font-size:2.2rem;'
            'box-shadow:0 10px 36px rgba(108,99,255,0.45);" class="floating">🔬</div>'
            '<div style="font-family:Syne,sans-serif;font-size:2.1rem;font-weight:800;color:' + t["text"] + ';">'
            "ResearchHub "
            '<span style="background:linear-gradient(135deg,' + t["a1"] + "," + t["a2"] + ");"
            '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">AI</span>'
            "</div>"
            '<div style="color:' + t["muted"] + ';font-size:0.87rem;margin-top:4px;">'
            "Autonomous research intelligence platform"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
            'border-radius:22px;padding:2.2rem;'
            'box-shadow:0 28px 72px rgba(0,0,0,0.28);" class="fade-in">'
            '<div style="font-family:Syne,sans-serif;font-size:1.35rem;font-weight:700;'
            'color:' + t["text"] + ';margin-bottom:0.25rem;">Welcome back 👋</div>'
            '<div style="color:' + t["muted"] + ';font-size:0.82rem;margin-bottom:1.4rem;">'
            "Sign in to continue your research journey"
            "</div>",
            unsafe_allow_html=True,
        )

        email    = st.text_input("Email address", placeholder="you@university.edu")
        password = st.text_input("Password", type="password", placeholder="••••••••")

        c1, c2 = st.columns(2)
        with c1:
            login_btn = st.button("Sign In →", use_container_width=True)
        with c2:
            demo_btn  = st.button("▶ Demo Login", use_container_width=True)

        st.markdown(
            '<div style="text-align:center;margin-top:1rem;font-size:0.8rem;color:' + t["muted"] + ';">'
            "Don't have an account? "
            '<span style="color:' + t["a1"] + ';font-weight:600;cursor:pointer;">Sign up free</span>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        if login_btn:
            if email and password:
                with st.spinner("Authenticating…"):
                    time.sleep(0.7)
                st.session_state.authenticated = True
                st.session_state.username = email.split("@")[0].capitalize()
                st.rerun()
            else:
                st.error("Please enter both email and password.")

        if demo_btn:
            with st.spinner("Loading demo…"):
                time.sleep(0.4)
            st.session_state.authenticated = True
            st.session_state.username = "Researcher"
            st.rerun()

        # Social proof strip
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:center;'
            'gap:1.5rem;margin-top:2rem;flex-wrap:wrap;">'
            + "".join(
                '<div style="text-align:center;">'
                '<div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.2rem;color:' + t["text"] + ';">' + val + "</div>"
                '<div style="font-size:0.72rem;color:' + t["muted"] + ';">' + lbl + "</div>"
                "</div>"
                + (
                    '<div style="width:1px;height:28px;background:' + t["border"] + ';"></div>'
                    if i < 2 else ""
                )
                for i, (val, lbl) in enumerate([("50K+", "Researchers"), ("2M+", "Papers Indexed"), ("98%", "Satisfaction")])
            )
            + "</div>",
            unsafe_allow_html=True,
        )


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
def render_sidebar():
    t = T()
    nav_items = [
        ("🏠", "Dashboard"), ("🔍", "Search Papers"), ("📁", "Workspaces"),
        ("🤖", "AI Assistant"), ("📤", "Upload PDF"), ("📂", "Doc Space"), ("🎙️", "Voice Search"),
    ]

    with st.sidebar:
        # Logo
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;padding:0.8rem 0.3rem 0.4rem;">'
            '<div style="width:38px;height:38px;border-radius:10px;flex-shrink:0;'
            'background:linear-gradient(135deg,' + t["a1"] + "," + t["a2"] + ");"
            'display:flex;align-items:center;justify-content:center;font-size:1.2rem;">🔬</div>'
            '<div>'
            '<div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.05rem;color:' + t["text"] + ';">ResearchHub</div>'
            '<div style="font-size:0.68rem;color:' + t["muted"] + ';">AI · v2.1</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        # User chip
        uname = st.session_state.username or "User"
        st.markdown(
            '<div style="background:' + t["surface2"] + ';border:1px solid ' + t["border"] + ';'
            'border-radius:12px;padding:9px 12px;margin:0.6rem 0 0.8rem;'
            'display:flex;align-items:center;gap:10px;">'
            '<div style="width:32px;height:32px;border-radius:50%;flex-shrink:0;'
            'background:linear-gradient(135deg,' + t["a1"] + "," + t["a2"] + ");"
            'display:flex;align-items:center;justify-content:center;'
            'font-size:0.85rem;font-weight:700;color:white;">' + uname[0].upper() + "</div>"
            '<div>'
            '<div style="font-weight:600;font-size:0.87rem;color:' + t["text"] + ';">' + uname + "</div>"
            '<div style="font-size:0.7rem;color:' + t["a3"] + ';">● Pro Plan</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="font-size:0.68rem;font-weight:700;color:' + t["muted"] + ';'
            'letter-spacing:0.08em;text-transform:uppercase;margin-bottom:5px;padding:0 3px;">'
            "NAVIGATION</div>",
            unsafe_allow_html=True,
        )

        current_idx = next((i for i, (_, lbl) in enumerate(nav_items) if lbl == st.session_state.page), 0)
        chosen = st.radio(
            "nav",
            [lbl for _, lbl in nav_items],
            index=current_idx,
            format_func=lambda x: next(ic for ic, lb in nav_items if lb == x) + "  " + x,
            label_visibility="collapsed",
        )
        if chosen != st.session_state.page:
            st.session_state.page = chosen
            st.rerun()

        st.markdown(
            '<hr style="border-color:' + t["border"] + ';margin:0.8rem 0;"/>',
            unsafe_allow_html=True,
        )

        dm = st.toggle("🌙  Dark mode", value=st.session_state.dark_mode)
        if dm != st.session_state.dark_mode:
            st.session_state.dark_mode = dm
            st.rerun()

        # Quick stats
        _bg2 = t["surface2"]
        _bd  = t["border"]
        _mu  = t["muted"]
        _tx  = t["text"]
        _a1  = t["a1"]
        _a3  = t["a3"]
        _stat = (
            '<div style="background:' + _bg2 + ';border:1px solid ' + _bd + ';'
            'border-radius:12px;padding:12px;margin-top:0.6rem;">'
            '<div style="font-size:0.68rem;font-weight:700;color:' + _mu + ';'
            'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:8px;">QUICK STATS</div>'
            '<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            '<span style="font-size:0.77rem;color:' + _mu + ';">Papers imported</span>'
            '<span style="font-size:0.77rem;font-weight:700;color:' + _tx + ';">47</span></div>'
            '<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            '<span style="font-size:0.77rem;color:' + _mu + ';">Workspaces</span>'
            '<span style="font-size:0.77rem;font-weight:700;color:' + _tx + ';">6</span></div>'
            '<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
            '<span style="font-size:0.77rem;color:' + _mu + ';">AI queries today</span>'
            '<span style="font-size:0.77rem;font-weight:700;color:' + _a3 + ';">12 / 50</span></div>'
            '<div style="background:' + _bd + ';border-radius:99px;height:4px;margin-top:4px;">'
            '<div style="width:24%;background:linear-gradient(90deg,' + _a1 + ',' + _a3 + ');'
            'border-radius:99px;height:4px;"></div></div></div>'
        )
        st.markdown(_stat, unsafe_allow_html=True)


        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🚪  Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()


# ─── DASHBOARD ────────────────────────────────────────────────────────────────
def page_dashboard():
    t = T()
    section_header("Good morning, " + st.session_state.username + " 👋", "Here's your research activity overview")

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("Papers Imported", "47", "↑ 8 this week",    "linear-gradient(135deg," + t["a1"] + "," + t["a5"] + ")", "📄"),
        ("Workspaces",      "6",  "↑ 2 this month",   "linear-gradient(135deg," + t["a2"] + ",#c471ed)",           "📁"),
        ("AI Queries",      "234","↑ 28 today",        "linear-gradient(135deg," + t["a3"] + ",#00b09b)",           "🤖"),
        ("Citations Found", "1.2M","Across all papers","linear-gradient(135deg," + t["a4"] + ",#f54ea2)",           "🔗"),
    ]
    for col, (lbl, val, dlt, grad, ico) in zip([c1, c2, c3, c4], kpis):
        with col:
            st.markdown(kpi_card(lbl, val, dlt, grad, ico), unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    left, right = st.columns([1.6, 1])

    with left:
        values = [random.randint(1, 12) for _ in range(30)]
        values[-1] = random.randint(8, 12)
        st.markdown(
            card_open()
            + '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.97rem;'
            'color:' + t["text"] + ';margin-bottom:0.8rem;">📈 Research Activity — Last 30 Days</div>'
            + bar_chart_html(values, t["a1"], t["a5"])
            + '<div style="display:flex;justify-content:space-between;margin-top:6px;">'
            + '<span style="font-size:0.7rem;color:' + t["muted"] + ';">Day 1</span>'
            + '<span style="font-size:0.7rem;color:' + t["muted"] + ';">Today</span>'
            + "</div></div>",
            unsafe_allow_html=True,
        )

    with right:
        domains = [("NLP & LLMs", 42, t["a1"]), ("Computer Vision", 28, t["a2"]), ("RL & Agents", 17, t["a3"]), ("Other", 13, t["a4"])]
        domain_rows = "".join(
            '<div style="margin-bottom:11px;">'
            '<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
            '<span style="font-size:0.8rem;color:' + t["text"] + ';font-weight:500;">' + n + "</span>"
            '<span style="font-size:0.8rem;color:' + t["muted"] + ';font-weight:600;">' + str(p) + "%</span>"
            "</div>"
            '<div style="background:' + t["border"] + ';border-radius:99px;height:5px;">'
            '<div style="width:' + str(p) + "%;background:" + c + ';border-radius:99px;height:5px;"></div>'
            "</div></div>"
            for n, p, c in domains
        )
        st.markdown(
            card_open("height:100%;")
            + '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.97rem;'
            'color:' + t["text"] + ';margin-bottom:0.9rem;">🏷️ Papers by Domain</div>'
            + domain_rows
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    r1, r2 = st.columns(2)

    with r1:
        st.markdown(
            '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.93rem;'
            'color:' + t["text"] + ';margin-bottom:0.7rem;">🕐 Recently Imported</div>',
            unsafe_allow_html=True,
        )
        for p in PAPERS[:3]:
            title_short = p["title"][:55] + ("…" if len(p["title"]) > 55 else "")
            tags_html = "".join(pill(tg, t["a1"]) for tg in p["tags"][:2])
            st.markdown(
                '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                'border-radius:13px;padding:1rem 1.2rem;margin-bottom:0.75rem;'
                'border-left:3px solid ' + p["color"] + ';">'
                '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.9rem;'
                'color:' + t["text"] + ';margin-bottom:4px;">' + title_short + "</div>"
                '<div style="font-size:0.77rem;color:' + t["a5"] + ';margin-bottom:6px;">' + p["authors"] + "</div>"
                + tags_html
                + "</div>",
                unsafe_allow_html=True,
            )

    with r2:
        st.markdown(
            '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.93rem;'
            'color:' + t["text"] + ';margin-bottom:0.7rem;">🚀 Active Workspaces</div>',
            unsafe_allow_html=True,
        )
        for ws in WORKSPACES[:3]:
            st.markdown(
                '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                'border-radius:13px;padding:1rem 1.2rem;margin-bottom:0.75rem;">'
                '<div style="display:flex;align-items:center;gap:10px;">'
                '<div style="width:34px;height:34px;border-radius:9px;background:' + ws["color"] + '22;'
                'display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;">' + ws["icon"] + "</div>"
                '<div>'
                '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.9rem;color:' + t["text"] + ';">' + ws["name"] + "</div>"
                '<div style="font-size:0.73rem;color:' + t["muted"] + ';">' + str(ws["papers"]) + " papers · " + ws["created"] + "</div>"
                "</div></div></div>",
                unsafe_allow_html=True,
            )


# ─── SEARCH PAPERS ────────────────────────────────────────────────────────────
def page_search():
    t = T()
    section_header("Search Research Papers", "Query millions of papers from arXiv, PubMed, IEEE, and more")

    sc1, sc2, sc3 = st.columns([4, 1.4, 1])
    with sc1:
        query = st.text_input("search_q", placeholder="🔍  Search papers, topics, authors, or DOIs…", label_visibility="collapsed")
    with sc2:
        source_filter = st.selectbox("src", ["All Sources", "arXiv", "PubMed", "IEEE", "ACM"], label_visibility="collapsed")
    with sc3:
        do_search = st.button("Search →", use_container_width=True)

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        yr = st.select_slider("Year range", options=list(range(2010, 2026)), value=(2018, 2025))
    with fc2:
        sort_by = st.selectbox("Sort by", ["Relevance", "Citations", "Date"])
    with fc3:
        field = st.selectbox("Field", ["All Fields", "NLP", "Computer Vision", "RL", "Medical AI"])
    with fc4:
        st.markdown("<br/>", unsafe_allow_html=True)
        oa = st.checkbox("Open Access only")

    st.markdown('<hr style="border-color:' + t["border"] + ';margin:0.4rem 0 1rem;"/>', unsafe_allow_html=True)

    if do_search or st.session_state.search_done:
        if do_search:
            st.session_state.search_done = True
            st.session_state.search_query = query

        q = st.session_state.search_query
        results_label = (
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">'
            '<div><span style="font-size:0.93rem;font-weight:600;color:' + t["text"] + ';">Found </span>'
            '<span style="color:' + t["a1"] + ';font-family:Syne,sans-serif;font-weight:800;font-size:1.05rem;">'
            + str(len(PAPERS)) + "</span>"
            '<span style="font-size:0.93rem;font-weight:600;color:' + t["text"] + ';"> papers</span>'
            + ('<span style="font-size:0.83rem;color:' + t["muted"] + ';"> for &ldquo;' + q + "&rdquo;</span>" if q else "")
            + "</div>"
            '<div style="font-size:0.77rem;color:' + t["muted"] + ';">Showing 1–5 of ' + str(len(PAPERS)) + "</div>"
            "</div>"
        )
        st.markdown(results_label, unsafe_allow_html=True)

        with st.spinner("Fetching results…"):
            time.sleep(0.35)

        for i, p in enumerate(PAPERS):
            tags_html = "".join(pill(tg, [t["a1"], t["a2"], t["a3"], t["a4"]][j % 4]) for j, tg in enumerate(p["tags"]))
            cite_color = t["a3"] if p["citations"] > 50000 else t["a4"]
            import_btn = (
                '<div style="background:' + t["a1"] + '22;color:' + t["a1"] + ';border:1px solid ' + t["a1"] + '44;'
                'border-radius:8px;padding:6px 13px;font-size:0.78rem;font-weight:600;cursor:pointer;'
                'white-space:nowrap;text-align:center;margin-bottom:5px;">+ Import</div>'
            )
            pdf_btn = (
                '<div style="background:' + t["surface2"] + ';color:' + t["muted"] + ';border:1px solid ' + t["border"] + ';'
                'border-radius:8px;padding:6px 13px;font-size:0.78rem;font-weight:600;cursor:pointer;text-align:center;">📄 PDF</div>'
            )
            st.markdown(
                '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                'border-left:3px solid ' + p["color"] + ';border-radius:14px;padding:1.15rem 1.35rem;'
                'margin-bottom:0.85rem;transition:all 0.25s;">'
                '<div style="display:flex;gap:1rem;align-items:flex-start;">'
                '<div style="flex:1;">'
                '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:1rem;color:' + t["text"] + ';margin-bottom:4px;">' + p["title"] + "</div>"
                '<div style="font-size:0.79rem;color:' + t["a5"] + ';margin-bottom:5px;">✍️ ' + p["authors"] + " &nbsp;|&nbsp; 📅 " + str(p["year"]) + " &nbsp;|&nbsp; 🏛️ " + p["venue"] + "</div>"
                '<div style="font-size:0.81rem;color:' + t["muted"] + ';line-height:1.55;margin-bottom:10px;">' + p["abstract"] + "</div>"
                '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">'
                + tags_html
                + source_badge(p["source"])
                + '<span style="margin-left:auto;font-size:0.77rem;color:' + cite_color + ';">🔗 ' + f'{p["citations"]:,}' + " citations</span>"
                "</div></div>"
                '<div style="flex-shrink:0;">' + import_btn + pdf_btn + "</div>"
                "</div></div>",
                unsafe_allow_html=True,
            )
    else:
        # Trending topics
        st.markdown(
            '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.95rem;'
            'color:' + t["text"] + ';margin-bottom:0.8rem;">🔥 Trending This Week</div>',
            unsafe_allow_html=True,
        )
        trends = ["Mixture of Experts", "RLHF Alignment", "Diffusion Models", "Vision-Language Models", "Agentic RAG", "Chain-of-Thought"]
        colors = [t["a1"], t["a2"], t["a3"], t["a4"], t["a5"], "#a18cd1"]
        tc = st.columns(3)
        for i, (trend, clr) in enumerate(zip(trends, colors)):
            with tc[i % 3]:
                st.markdown(
                    '<div style="background:' + clr + '11;border:1px solid ' + clr + '33;'
                    'border-radius:12px;padding:14px 16px;margin-bottom:8px;cursor:pointer;">'
                    '<div style="font-size:0.83rem;font-weight:600;color:' + clr + ';">🔍 ' + trend + "</div>"
                    '<div style="font-size:0.72rem;color:' + t["muted"] + ';margin-top:3px;">'
                    + str(random.randint(120, 890)) + " new papers</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )


# ─── WORKSPACES ───────────────────────────────────────────────────────────────
def page_workspaces():
    t = T()
    hc1, hc2 = st.columns([5, 1])
    with hc1:
        section_header("My Workspaces", "Organize and manage your research projects")
    with hc2:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("＋ New Workspace", use_container_width=True):
            st.info("🚀 Workspace creation coming soon!")

    cols = st.columns(3)
    for i, ws in enumerate(WORKSPACES):
        with cols[i % 3]:
            open_btn = (
                '<div style="flex:1;background:' + ws["color"] + '22;color:' + ws["color"] + ';'
                'border:1px solid ' + ws["color"] + '44;border-radius:8px;padding:6px;'
                'text-align:center;font-size:0.78rem;font-weight:600;cursor:pointer;">Open →</div>'
            )
            chat_btn = (
                '<div style="background:' + t["surface2"] + ';color:' + t["muted"] + ';'
                'border:1px solid ' + t["border"] + ';border-radius:8px;padding:6px 10px;'
                'font-size:0.78rem;cursor:pointer;">🤖</div>'
            )
            more_btn = (
                '<div style="background:' + t["surface2"] + ';color:' + t["muted"] + ';'
                'border:1px solid ' + t["border"] + ';border-radius:8px;padding:6px 10px;'
                'font-size:0.78rem;cursor:pointer;">⋯</div>'
            )
            st.markdown(
                '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                'border-top:3px solid ' + ws["color"] + ';border-radius:16px;padding:1.3rem;margin-bottom:1rem;">'
                '<div style="display:flex;align-items:center;gap:11px;margin-bottom:11px;">'
                '<div style="width:42px;height:42px;border-radius:12px;background:' + ws["color"] + '22;'
                'border:1px solid ' + ws["color"] + '44;display:flex;align-items:center;'
                'justify-content:center;font-size:1.3rem;flex-shrink:0;">' + ws["icon"] + "</div>"
                '<div>'
                '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.93rem;color:' + t["text"] + ';">' + ws["name"] + "</div>"
                '<div style="font-size:0.71rem;color:' + t["muted"] + ';">Created ' + ws["created"] + "</div>"
                "</div></div>"
                '<div style="font-size:0.8rem;color:' + t["muted"] + ';margin-bottom:11px;line-height:1.45;">' + ws["desc"] + "</div>"
                '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                '<span style="font-size:0.78rem;color:' + t["text"] + ';font-weight:600;">📄 ' + str(ws["papers"]) + " papers</span>"
                '<span style="font-size:0.72rem;color:' + ws["color"] + ';font-weight:600;">' + str(ws["pct"]) + "% complete</span>"
                "</div>"
                '<div style="background:' + t["border"] + ';border-radius:99px;height:5px;margin-bottom:13px;">'
                '<div style="width:' + str(ws["pct"]) + "%;background:" + ws["color"] + ';border-radius:99px;height:5px;"></div>'
                "</div>"
                '<div style="display:flex;gap:6px;">' + open_btn + chat_btn + more_btn + "</div>"
                "</div>",
                unsafe_allow_html=True,
            )


# ─── AI ASSISTANT ─────────────────────────────────────────────────────────────
def page_ai():
    t = T()
    section_header("AI Research Assistant", "Ask anything about your imported papers")

    ac1, ac2, ac3 = st.columns([2, 2, 1.5])
    with ac1:
        ws_names = [ws["name"] for ws in WORKSPACES]
        sel_ws = st.selectbox("Active Workspace", ws_names)
    with ac2:
        model = st.selectbox("Model", ["Llama 3.3 70B (Groq)", "Claude Sonnet 4", "GPT-4o"])
    with ac3:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    ws_obj = next((w for w in WORKSPACES if w["name"] == sel_ws), WORKSPACES[0])
    st.markdown(
        '<div style="background:' + ws_obj["color"] + '11;border:1px solid ' + ws_obj["color"] + '33;'
        'border-radius:12px;padding:9px 14px;margin-bottom:0.9rem;'
        'display:flex;align-items:center;gap:10px;">'
        '<span style="font-size:1.1rem;">' + ws_obj["icon"] + "</span>"
        '<span style="font-size:0.82rem;font-weight:600;color:' + ws_obj["color"] + ';">' + ws_obj["name"] + "</span>"
        '<span style="font-size:0.79rem;color:' + t["muted"] + ';"> · ' + str(ws_obj["papers"]) + " papers loaded · Context-aware mode</span>"
        '<span style="margin-left:auto;font-size:0.74rem;background:' + t["a3"] + '22;color:' + t["a3"] + ';'
        'padding:3px 10px;border-radius:99px;font-weight:600;">🟢 Connected</span>'
        "</div>",
        unsafe_allow_html=True,
    )

    # Suggested prompts when chat is empty
    if not st.session_state.messages:
        st.markdown(
            '<div style="font-size:0.79rem;color:' + t["muted"] + ';margin-bottom:7px;font-weight:500;">💡 Suggested prompts:</div>',
            unsafe_allow_html=True,
        )
        suggestions = [
            "Summarize all papers in this workspace",
            "What are the key differences between these models?",
            "Extract main contributions of each paper",
            "Generate a literature review",
        ]
        sg1, sg2 = st.columns(2)
        for i, sug in enumerate(suggestions):
            with (sg1 if i % 2 == 0 else sg2):
                if st.button('"' + sug + '"', use_container_width=True, key="sug_" + str(i)):
                    st.session_state.messages.append({"role": "user", "content": sug})
                    st.session_state.messages.append({"role": "ai", "content": random.choice(AI_BANK)})
                    st.rerun()
        st.markdown("<br/>", unsafe_allow_html=True)

    # Chat history
    if st.session_state.messages:
        chat_rows = ""
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_rows += (
                    '<div style="display:flex;justify-content:flex-end;margin-bottom:8px;">'
                    '<div style="background:linear-gradient(135deg,' + t["a1"] + ',#8b5cf6);color:white;'
                    'border-radius:18px 18px 4px 18px;padding:11px 15px;max-width:75%;'
                    'font-size:0.88rem;line-height:1.5;">' + msg["content"] + "</div></div>"
                )
            else:
                chat_rows += (
                    '<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;">'
                    '<div style="width:28px;height:28px;border-radius:8px;flex-shrink:0;'
                    'background:linear-gradient(135deg,' + t["a1"] + "," + t["a2"] + ");"
                    'display:flex;align-items:center;justify-content:center;font-size:0.75rem;">🤖</div>'
                    '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                    'border-radius:18px 18px 18px 4px;padding:11px 15px;max-width:82%;'
                    'font-size:0.88rem;line-height:1.6;color:' + t["text"] + ';">' + msg["content"] + "</div></div>"
                )
        st.markdown(
            '<div style="max-height:380px;overflow-y:auto;padding:0.8rem;'
            'background:' + t["surface2"] + ';border:1px solid ' + t["border"] + ';border-radius:14px;margin-bottom:0.7rem;">'
            + chat_rows + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="border-color:' + t["border"] + ';margin:0.5rem 0;"/>', unsafe_allow_html=True)
    ic1, ic2 = st.columns([10, 1])
    with ic1:
        user_input = st.text_input("msg", placeholder="Ask about your papers, request summaries, comparisons…", label_visibility="collapsed")
    with ic2:
        send = st.button("➤", use_container_width=True)

    if send and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("🤖 Thinking…"):
            time.sleep(1.1)
        st.session_state.messages.append({"role": "ai", "content": random.choice(AI_BANK)})
        st.rerun()

    # Capability pills
    caps = ["📝 Summarize", "🔍 Compare", "💡 Insights", "📖 Lit Review", "❓ Q&A", "📊 Extract Data"]
    cap_html = '<div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:0.8rem;">' + "".join(
        '<span style="background:' + t["surface2"] + ';border:1px solid ' + t["border"] + ';'
        'color:' + t["muted"] + ';padding:5px 12px;border-radius:99px;font-size:0.75rem;font-weight:500;">' + c + "</span>"
        for c in caps
    ) + "</div>"
    st.markdown(cap_html, unsafe_allow_html=True)


# ─── UPLOAD PDF ───────────────────────────────────────────────────────────────
def page_upload():
    t = T()
    section_header("Upload Research Papers", "Import PDFs and let AI extract insights automatically")

    ul, ur = st.columns([1.3, 1])

    with ul:
        st.markdown(
            card_open()
            + '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.97rem;'
            'color:' + t["text"] + ';margin-bottom:1rem;">📤 Upload PDF Files</div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader("Drop PDFs here or click to browse", type=["pdf"], accept_multiple_files=True)
        ws_target = st.selectbox("Save to workspace", [ws["name"] for ws in WORKSPACES])

        oc1, oc2 = st.columns(2)
        with oc1:
            auto_sum   = st.checkbox("Auto-generate summary", value=True)
            extract_md = st.checkbox("Extract metadata",      value=True)
        with oc2:
            embed  = st.checkbox("Create embeddings", value=True)
            cites  = st.checkbox("Extract citations", value=False)

        process = st.button("⚡ Process & Import", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if process:
            if uploaded:
                for f in uploaded:
                    bar = st.progress(0, text="Processing " + f.name + "…")
                    for pct in range(0, 101, 5):
                        time.sleep(0.03)
                        bar.progress(pct, text="Processing " + f.name + "… " + str(pct) + "%")
                    st.success("✅ " + f.name + " imported successfully!")
            else:
                st.warning("Please select at least one PDF file.")

    with ur:
        pipeline_steps = [
            ("📥", "PDF Upload",        "Secure file transfer",             t["a1"], True),
            ("🔤", "Text Extraction",   "Extract all text layers",          t["a5"], True),
            ("🏷️", "Metadata Parsing",  "Authors, year, venue, DOI",        t["a3"], True),
            ("🧠", "AI Summarization",  "Groq Llama 70B analysis",          t["a2"], False),
            ("📐", "Vector Embedding",  "Semantic search indexing",         t["a4"], False),
            ("💾", "Workspace Storage", "Save to your workspace",           t["a1"], False),
        ]
        rows = "".join(
            '<div style="display:flex;align-items:center;gap:11px;padding:9px 0;border-bottom:1px solid ' + t["border"] + ';">'
            '<div style="width:33px;height:33px;border-radius:8px;background:' + clr + '22;'
            'display:flex;align-items:center;justify-content:center;font-size:0.95rem;flex-shrink:0;">' + ico + "</div>"
            '<div style="flex:1;">'
            '<div style="font-size:0.82rem;font-weight:600;color:' + t["text"] + ';">' + name + "</div>"
            '<div style="font-size:0.71rem;color:' + t["muted"] + ';">' + desc + "</div>"
            "</div>"
            '<div style="font-size:0.74rem;' + ('color:' + t["a3"] + ';font-weight:700;' if done else 'color:' + t["muted"] + ';') + '">'
            + ("✓ Ready" if done else "○ Queued")
            + "</div></div>"
            for ico, name, desc, clr, done in pipeline_steps
        )
        st.markdown(
            card_open("margin-bottom:1rem;")
            + '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.97rem;'
            'color:' + t["text"] + ';margin-bottom:0.8rem;">⚡ Processing Pipeline</div>'
            + rows
            + "</div>",
            unsafe_allow_html=True,
        )

        src_types = ["PDF", "arXiv URL", "DOI", "PubMed ID", "Semantic Scholar"]
        chips = "".join(
            '<span style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
            'color:' + t["text"] + ';padding:4px 10px;border-radius:8px;font-size:0.75rem;">' + s + "</span>"
            for s in src_types
        )
        st.markdown(
            '<div style="background:' + t["surface2"] + ';border:1px solid ' + t["border"] + ';'
            'border-radius:12px;padding:13px;">'
            '<div style="font-size:0.71rem;font-weight:700;color:' + t["muted"] + ';'
            'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:7px;">SUPPORTED SOURCES</div>'
            '<div style="display:flex;gap:6px;flex-wrap:wrap;">' + chips + "</div></div>",
            unsafe_allow_html=True,
        )


# ─── DOC SPACE ────────────────────────────────────────────────────────────────
def page_docspace():
    t = T()
    section_header("Doc Space", "All your research documents in one place")

    tab1, tab2, tab3 = st.tabs(["📄 All Documents", "📝 Notes", "📊 Generated Reports"])

    with tab1:
        tc1, tc2, tc3 = st.columns([3, 1.5, 1])
        with tc1:
            st.text_input("ds_search", placeholder="🔍 Search documents…", label_visibility="collapsed")
        with tc2:
            st.selectbox("ds_type", ["All Types", "PDFs", "Notes", "Reports"], label_visibility="collapsed")
        with tc3:
            st.button("＋ New Doc", use_container_width=True)

        dc = st.columns(3)
        for i, doc in enumerate(DOCS):
            with dc[i % 3]:
                st.markdown(
                    '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                    'border-top:3px solid ' + doc["color"] + ';border-radius:14px;padding:1.2rem;margin-bottom:1rem;">'
                    '<div style="font-size:2.4rem;margin-bottom:9px;">📄</div>'
                    '<div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.87rem;'
                    'color:' + t["text"] + ';margin-bottom:5px;line-height:1.35;">' + doc["name"] + "</div>"
                    '<div style="font-size:0.74rem;color:' + t["muted"] + ';margin-bottom:10px;">'
                    + doc["size"] + " · " + str(doc["pages"]) + " pages · " + doc["date"]
                    + "</div>"
                    '<div style="display:flex;gap:6px;">'
                    '<div style="flex:1;background:' + doc["color"] + '22;color:' + doc["color"] + ';'
                    'border:1px solid ' + doc["color"] + '44;border-radius:7px;padding:5px;'
                    'text-align:center;font-size:0.75rem;font-weight:600;cursor:pointer;">Open</div>'
                    '<div style="background:' + t["surface2"] + ';color:' + t["muted"] + ';'
                    'border:1px solid ' + t["border"] + ';border-radius:7px;padding:5px 10px;'
                    'font-size:0.75rem;cursor:pointer;">⋯</div>'
                    "</div></div>",
                    unsafe_allow_html=True,
                )

    with tab2:
        st.markdown(
            card_open()
            + '<div style="font-family:Syne,sans-serif;font-weight:700;color:' + t["text"] + ';margin-bottom:0.9rem;">📝 Research Notes</div>',
            unsafe_allow_html=True,
        )
        note = st.text_area(
            "note_area",
            height=240,
            label_visibility="collapsed",
            placeholder="# Research Notes\n\nStart writing your thoughts, observations, and insights here…\n\nSupports **Markdown** formatting!",
        )
        nc1, _ = st.columns([1, 5])
        with nc1:
            if st.button("💾 Save Note"):
                st.success("Note saved!")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        reports = [
            ("📖", "Literature Review",  "Comprehensive analysis of 47 papers",   "Feb 25", t["a1"]),
            ("📊", "Citation Network",   "Visual map of paper relationships",       "Feb 23", t["a2"]),
            ("💡", "Key Insights Report","Top findings extracted by AI",            "Feb 20", t["a3"]),
            ("📈", "Research Trends",    "Emerging topics and methodologies",       "Feb 18", t["a4"]),
        ]
        for ico, name, desc, date, clr in reports:
            st.markdown(
                '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
                'border-left:3px solid ' + clr + ';border-radius:13px;padding:1.1rem 1.3rem;margin-bottom:0.8rem;'
                'display:flex;align-items:center;gap:13px;">'
                '<div style="width:42px;height:42px;border-radius:11px;background:' + clr + '22;'
                'border:1px solid ' + clr + '44;display:flex;align-items:center;'
                'justify-content:center;font-size:1.25rem;flex-shrink:0;">' + ico + "</div>"
                '<div style="flex:1;">'
                '<div style="font-family:Syne,sans-serif;font-weight:700;color:' + t["text"] + ';font-size:0.92rem;">' + name + "</div>"
                '<div style="font-size:0.77rem;color:' + t["muted"] + ';margin-top:2px;">' + desc + " · Generated " + date + "</div>"
                "</div>"
                '<div style="display:flex;gap:6px;flex-shrink:0;">'
                '<div style="background:' + clr + '22;color:' + clr + ';border:1px solid ' + clr + '44;'
                'border-radius:8px;padding:5px 12px;font-size:0.76rem;font-weight:600;cursor:pointer;">📥 Download</div>'
                '<div style="background:' + t["surface2"] + ';color:' + t["muted"] + ';'
                'border:1px solid ' + t["border"] + ';border-radius:8px;padding:5px 12px;'
                'font-size:0.76rem;cursor:pointer;">View</div>'
                "</div></div>",
                unsafe_allow_html=True,
            )


# ─── VOICE SEARCH ─────────────────────────────────────────────────────────────
def page_voice():
    t = T()
    section_header("Voice Search", "Search papers using natural speech commands")

    _, vc, _ = st.columns([1, 2, 1])
    with vc:
        active = st.session_state.voice_active
        ring_style = (
            "animation:pulse 1.2s infinite;"
            "box-shadow:0 0 0 20px rgba(108,99,255,0.1),0 0 0 40px rgba(108,99,255,0.05);"
            if active else ""
        )
        status_text = "🔴  LISTENING…" if active else "🎙️  Click Start to activate voice search"
        waveform = ""
        if active:
            bars = "".join(
                '<div style="width:3px;background:' + t["a1"] + ';border-radius:2px;'
                'animation:pulse ' + str(round(0.3 + i * 0.08, 2)) + "s infinite;"
                'height:' + str(random.randint(6, 28)) + 'px;"></div>'
                for i in range(20)
            )
            waveform = '<div style="display:flex;gap:3px;justify-content:center;align-items:center;height:32px;margin-top:1rem;">' + bars + "</div>"

        st.markdown(
            '<div style="text-align:center;padding:2rem 0;">'
            '<div style="font-size:0.85rem;color:' + t["muted"] + ';margin-bottom:1.5rem;font-weight:500;">' + status_text + "</div>"
            '<div style="width:120px;height:120px;border-radius:50%;margin:0 auto;cursor:pointer;'
            'background:linear-gradient(135deg,' + t["a1"] + "," + t["a2"] + ");"
            'display:flex;align-items:center;justify-content:center;font-size:3rem;'
            + ring_style + '">'
            "🎙️</div>"
            + waveform
            + "</div>",
            unsafe_allow_html=True,
        )

        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            if st.button("🎙️ Start", use_container_width=True):
                st.session_state.voice_active = True
                st.rerun()
        with vc2:
            if st.button("⏹ Stop", use_container_width=True):
                st.session_state.voice_active = False
                st.rerun()
        with vc3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.voice_active = False
                st.rerun()

        if active:
            with st.spinner("Listening and transcribing…"):
                time.sleep(2)
            st.session_state.voice_active = False
            st.info('🎤 Transcribed: "Show me recent papers on transformer attention in NLP"')
            st.rerun()

        # Commands guide
        cmd_rows = "".join(
            '<div style="display:flex;align-items:center;gap:11px;padding:8px 0;border-bottom:1px solid ' + t["border"] + ';">'
            '<span style="font-size:1.1rem;">' + ico + "</span>"
            '<div>'
            '<span style="font-size:0.8rem;font-weight:600;color:' + t["a1"] + ';">' + cmd + ":  </span>"
            '<span style="font-size:0.8rem;color:' + t["muted"] + ';font-style:italic;">' + ex + "</span>"
            "</div></div>"
            for ico, cmd, ex in VOICE_COMMANDS
        )
        st.markdown(
            '<div style="background:' + t["surface"] + ';border:1px solid ' + t["border"] + ';'
            'border-radius:16px;padding:1.4rem;margin-top:1.5rem;">'
            '<div style="font-family:Syne,sans-serif;font-weight:700;color:' + t["text"] + ';margin-bottom:0.8rem;">💡 Voice Command Examples</div>'
            + cmd_rows
            + "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br/>", unsafe_allow_html=True)
        st.selectbox("🌐 Language", ["English (US)", "English (UK)", "Spanish", "French", "German", "Japanese"])


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    inject_css()

    if not st.session_state.authenticated:
        page_login()
        return

    render_sidebar()

    dispatch = {
        "Dashboard":    page_dashboard,
        "Search Papers": page_search,
        "Workspaces":   page_workspaces,
        "AI Assistant": page_ai,
        "Upload PDF":   page_upload,
        "Doc Space":    page_docspace,
        "Voice Search": page_voice,
    }
    dispatch.get(st.session_state.page, page_dashboard)()


if __name__ == "__main__":
    main()
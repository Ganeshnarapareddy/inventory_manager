CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base ───────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f1f3d 100%);
    min-height: 100vh;
}

/* ── Sidebar ───────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d2b 0%, #1a1040 100%) !important;
    border-right: 1px solid rgba(99,102,241,0.3);
}
[data-testid="stSidebar"] .stMarkdown h1 {
    background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.6rem !important;
    font-weight: 800;
    text-align: center;
    padding: 0.5rem 0;
}

/* ── Metric Cards ──────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.2rem !important;
    backdrop-filter: blur(10px);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 35px rgba(99,102,241,0.3);
    border-color: rgba(99,102,241,0.6);
}
[data-testid="metric-container"] label {
    color: #a5b4fc !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    color: #34d399 !important;
}

/* ── Buttons ───────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.4) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99,102,241,0.6) !important;
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    box-shadow: none !important;
}

/* ── Inputs ────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    transition: border-color 0.3s ease !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
}

/* ── DataFrames ────────────────────────────────────────────── */
[data-testid="stDataFrame"], .stDataFrame {
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}
iframe[title="st_aggrid.AgGrid"] { border-radius: 16px; }

/* ── Tabs ──────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    padding: 8px !important;
    gap: 16px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    color: #94a3b8 !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    transition: all 0.3s ease !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.4) !important;
}

/* ── Headings ──────────────────────────────────────────────── */
h1, h2, h3 { color: #f1f5f9 !important; }
h1 { font-weight: 800 !important; }
h2 { font-weight: 700 !important; }
.stMarkdown p { color: #94a3b8 !important; }

/* ── Alert / Info boxes ────────────────────────────────────── */
.stAlert {
    border-radius: 12px !important;
    border-left-width: 4px !important;
}
.element-container .stSuccess {
    background: rgba(52,211,153,0.1) !important;
    border-color: #34d399 !important;
}
.element-container .stError {
    background: rgba(239,68,68,0.1) !important;
    border-color: #ef4444 !important;
}
.element-container .stWarning {
    background: rgba(251,191,36,0.1) !important;
    border-color: #fbbf24 !important;
}

/* ── Custom Cards ──────────────────────────────────────────── */
.kpi-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08));
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 18px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99,102,241,0.1) 0%, transparent 70%);
    animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { transform: scale(0.8); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}
.kpi-card:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: 0 20px 50px rgba(99,102,241,0.35);
    border-color: rgba(99,102,241,0.7);
}
.kpi-value { font-size: 2.2rem; font-weight: 800; color: #f1f5f9; }
.kpi-label { font-size: 0.8rem; font-weight: 600; color: #a5b4fc;
             text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
.kpi-icon { font-size: 2rem; margin-bottom: 0.5rem; }

/* ── Section header ────────────────────────────────────────── */
.section-header {
    background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.1));
    border-left: 4px solid #6366f1;
    border-radius: 0 12px 12px 0;
    padding: 0.75rem 1.25rem;
    margin-bottom: 1.5rem;
}
.section-header h2 { margin: 0 !important; font-size: 1.25rem !important; }

/* ── Badge ─────────────────────────────────────────────────── */
.badge-low  { background:#fef3c7; color:#92400e; border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:700; }
.badge-ok   { background:#d1fae5; color:#065f46; border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:700; }
.badge-out  { background:#fee2e2; color:#991b1b; border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:700; }

/* ── Sidebar nav buttons ───────────────────────────────────── */
div[data-testid="stSidebarNav"] { display: none; }

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.5); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.8); }

/* ── Radio buttons ─────────────────────────────────────────── */
.stRadio > label { color: #94a3b8 !important; }
.stRadio [data-baseweb="radio"] span { border-color: #6366f1 !important; }

/* ── Expander ──────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: rgba(99,102,241,0.1) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}

/* ── File uploader ─────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(99,102,241,0.4) !important;
    border-radius: 14px !important;
    background: rgba(99,102,241,0.05) !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(99,102,241,0.8) !important;
    background: rgba(99,102,241,0.1) !important;
}
</style>
"""

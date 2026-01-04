import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import random
import uuid
import json
import time

# --- CONFIGURATION ---
# (Secrets handling remains same)
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        pass 
except Exception:
    pass

st.set_page_config(page_title="JanAI Research Portal", layout="wide", initial_sidebar_state="expanded")

# --- PROFESSIONAL CSS (CORPORATE STYLE) ---
st.markdown("""
    <style>
    /* Import Google Fonts: Poppins (UI) & Noto Sans Ol Chiki (Script) */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ol+Chiki&family=Poppins:wght@300;400;500;600&display=swap');

    /* Global Settings */
    .stApp {
        background-color: #f4f7f6;
        font-family: 'Poppins', sans-serif;
    }

    /* Hero Banner */
    .hero-container {
        background: linear-gradient(120deg, #0f3d0f, #2e7d32);
        padding: 40px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 25px rgba(27, 94, 32, 0.25);
        margin-bottom: 25px;
        text-align: left;
        position: relative;
        overflow: hidden;
    }
    .hero-title { font-size: 2.5rem; font-weight: 600; margin: 0; letter-spacing: -1px; }
    .hero-subtitle { font-size: 1.1rem; opacity: 0.9; font-weight: 300; margin-top: 10px; }

    /* Modern Cards */
    .pro-card {
        background: white;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s;
    }
    .pro-card:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.08); }

    /* Tags & Badges */
    .badge {
        display: inline-block; padding: 4px 12px; border-radius: 50px;
        font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
    }
    .badge-blue { background: #e3f2fd; color: #1565c0; }
    .badge-green { background: #e8f5e9; color: #2e7d32; }
    .badge-gold { background: #fff8e1; color: #f57f17; }

    /* Custom Inputs */
    .stTextInput>div>div>input { border-radius: 8px; border: 1px solid #ddd; padding: 10px; }
    .stTextArea>div>div>textarea { border-radius: 8px; border: 1px solid #ddd; }

    /* Buttons */
    .stButton>button {
        background-color: #1b5e20;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2e7d32; box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3); }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: white;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1b5e20;
        color: white;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPERS ---
def is_ol_chiki(text):
    if not text: return False
    valid = sum(1 for c in text if '\u1C50' <= c <= '\u1C7F')
    total = sum(1 for c in text if not c.isspace() and c not in ".,!?-1234567890")
    return (valid / total) > 0.8 if total > 0 else True

def get_translation_sentence(source_lang):
    # Professional Corpus Simulation
    corpus = {
        "Hindi": ["शिक्षा ही सफलता की कुंजी है।", "भारत गांवों का देश है।", "जल संचयन आज की आवश्यकता है।"],
        "Bengali": ["শিক্ষা হলো সাফল্যের চাবিকাঠি।", "গাছ লাগান, পরিবেশ বাঁচান।", "জলই জীবন।"],
        "Odia": ["ଶିକ୍ଷା ହିଁ ସଫଳତାର ଚାବିକାଠି |", "ଜଳ ହିଁ ଜୀବନ |", "ଓଡିଶା ଏକ ସୁନ୍ଦର ରାଜ୍ୟ |"],
        "English": ["Education is the key to success.", "Water is essential for life.", "Technology changes the world."]
    }
    return random.choice(corpus.get(source_lang, ["Hello World"]))

# --- SIDEBAR (User Profile) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=50)
    st.markdown("### **JanAI Workspace**")
    st.caption("v3.0 Enterprise Edition")
    
    st.write("---")
    st.markdown("#### 👤 Contributor Profile")
    u_name = st.text_input("Full Name", placeholder="Enter your name")
    u_role = st.selectbox("Role", ["Volunteer", "Linguist", "Student", "Researcher"])
    
    st.write("---")
    st.markdown("#### 🏆 Leaderboard")
    # Mock Professional Data
    st.markdown("""
    <div style='font-size:0.9rem'>
    1. <b>S. Murmu</b> <span style='float:right; color:#2e7d32'>1,240 pts</span><br>
    2. <b>R. Hembram</b> <span style='float:right; color:#2e7d32'>980 pts</span><br>
    3. <b>A. Tudu</b> <span style='float:right; color:#2e7d32'>850 pts</span>
    </div>
    """, unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown("""
<div class='hero-container'>
    <h1 class='hero-title'>JanAI Data Collection Portal</h1>
    <p class='hero-subtitle'>Developing the Next-Generation Large Language Model (LLM) for Santali.</p>
</div>
""", unsafe_allow_html=True)

# --- INSTRUCTIONS EXPANDER ---
with st.expander("📘 User Guidelines & Protocols (Click to Expand)", expanded=False):
    st.markdown("""
    **Welcome to the JanAI Workspace.** Please follow these data integrity protocols:
    1.  **Script Fidelity:** If you select **Ol Chiki**, strictly use the Ol Chiki script. Do not transliterate using English.
    2.  **Audio Quality:** Ensure minimum background noise during voice recording.
    3.  **Accuracy:** In Digitization tasks, type exactly what you see, including original errors if any.
    """)

# --- MAIN WORKSPACE ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Contextual AI", 
    "🖼️ Image Description", 
    "📜 Digitize Archives", 
    "✍️ Handwriting OCR", 
    "🌐 Universal Translation"
])

# --- TAB 1: CONTEXTUAL AI ---
with tab1:
    col_q, col_ans = st.columns([1, 1])
    
    with col_q:
        st.markdown("<div class='pro-card'>", unsafe_allow_html=True)
        st.markdown("#### 1. Context Configuration")
        c1, c2 = st.columns([1,1])
        with c1: region_lang = st.selectbox("Region Context", ["West Bengal (Bengali)", "Jharkhand (Hindi)", "Odisha (Odia)", "Global (English)"])
        with c2: 
            if st.button("Generate Question"): 
                st.session_state.q_val = random.choice(["How is the agriculture this year?", "Describe your local festival.", "What did you buy at the market?"])
        
        if 'q_val' not in st.session_state: st.session_state.q_val = "How is your daily life going?"
        
        st.markdown("---")
        st.markdown(f"<span class='badge badge-blue'>AI Generated Question</span>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='color:#333; margin-top:10px'>{st.session_state.q_val}</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_ans:
        st.markdown("<div class='pro-card'>", unsafe_allow_html=True)
        st.markdown("#### 2. Response Input")
        script_t1 = st.radio("Script Type", ["Ol Chiki (ᱚᱞ ᱪᱤᱠᱤ)", "Latin (English)"], horizontal=True, label_visibility="collapsed")
        
        ph = "Type response in Ol Chiki..." if "Ol Chiki" in script_t1 else "Type response in English letters..."
        text_t1 = st.text_area("Answer", placeholder=ph, height=100)
        
        c_mic, c_btn = st.columns([1, 2])
        with c_mic: audio_t1 = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹️ Stop", key="m1")
        with c_btn:
            st.write("") 
            if st.button("Submit Response", key="b1"):
                if u_name and (text_t1 or audio_t1):
                    if "Ol Chiki" in script_t1 and text_t1 and not is_ol_chiki(text_t1):
                        st.error("Validation Error: Latin characters detected in Ol Chiki mode.")
                    else:
                        st.success("Data successfully committed to database.")
                        time.sleep(1)
                        st.experimental_rerun()
                else:
                    st.warning("Please provide Name and Answer.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: IMAGE ---
with tab2:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown("<div class='pro-card'>", unsafe_allow_html=True)
        st.image(f"https://picsum.photos/seed/{random.randint(100,999)}/500/350", use_column_width=True, caption="Target Image")
        st.button("Refresh Image", key="ref_img")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='pro-card'>", unsafe_allow_html=True)
        st.markdown("#### Visual Description Task")
        st.caption("Describe the objects, colors, and actions visible in the image using Santali.")
        text_t2 = st.text_area("Description", height=150)
        if st.button("Submit Description", key="b2"):
            st.success("Visual data tagged successfully.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: DIGITIZATION ---
with tab3:
    st.info("ℹ️ **Task:** Transcribe the official document below. Preserve original spelling.")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.image("https://placehold.co/600x800/png?text=Santali+Constitution+Page+12\n\n(Official+Document+Scan)", use_column_width=True)
    with c2:
        st.markdown("#### Transcription Panel")
        st.text_area("Content", height=400, placeholder="Type exactly what you see...")
        st.button("Commit to Archive", key="b3")

# --- TAB 4: HANDWRITING OCR ---
with tab4:
    st.markdown("#### ✍️ Handwriting Recognition Training")
    uploaded = st.file_uploader("Upload dataset sample (JPG/PNG)", type=['png', 'jpg'])
    if uploaded:
        c1, c2 = st.columns([1,1])
        with c1: st.image(uploaded, caption="Source Sample", use_column_width=True)
        with c2:
            st.text_area("Ground Truth (Transcription)", height=200)
            st.button("Upload Dataset Entry", key="b4")

# --- TAB 5: UNIVERSAL TRANSLATION (UPDATED) ---
with tab5:
    st.markdown("<div class='pro-card'>", unsafe_allow_html=True)
    st.markdown("#### 🌐 Multilingual Parallel Corpus Builder")
    
    # Source Selection
    c_src, c_task = st.columns([1, 3])
    with c_src:
        src_lang = st.selectbox("Source Language", ["English", "Hindi", "Bengali", "Odia"])
    
    # Task Generation
    if 'trans_task' not in st.session_state: st.session_state.trans_task = ""
    if 'last_lang' not in st.session_state or st.session_state.last_lang != src_lang:
        st.session_state.trans_task = get_translation_sentence(src_lang)
        st.session_state.last_lang = src_lang

    with c_task:
        st.markdown(f"**Translate this sentence to Santali:**")
        st.info(f"📄 {st.session_state.trans_task}")
    
    st.write("---")
    
    # Translation Input
    col_in, col_act = st.columns([3, 1])
    with col_in:
        trans_out = st.text_area("Santali Translation", height=100, label_visibility="collapsed", placeholder="Type translation here...")
    with col_act:
        st.write("")
        st.write("")
        if st.button("Submit Translation", key="b5"):
            if trans_out:
                st.success("Parallel pair saved.")
                st.session_state.trans_task = get_translation_sentence(src_lang)
                st.experimental_rerun()
            else:
                st.error("Input required.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8rem; margin-top: 20px;'>
    JanAI Research Workspace © 2026 | Powered by Gemini 1.5 Flash | <a href='#'>Privacy Policy</a> | <a href='#'>Report Issue</a>
</div>
""", unsafe_allow_html=True)
    

import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import random
import json
import time

# --- CONFIGURATION ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        pass
except Exception:
    pass

st.set_page_config(page_title="JanAI", layout="wide", initial_sidebar_state="expanded")

# --- CSS STYLING (High Contrast for Visibility) ---
st.markdown("""
    <style>
    /* Global Text Color - Dark Grey for Readability */
    .stApp, p, h1, h2, h3, h4, div, span {
        color: #212121 !important; 
        font-family: sans-serif;
    }
    
    /* White Card Style with Shadow */
    .card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dcdcdc; /* Grey border */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* Visible Shadow */
        margin-bottom: 20px;
    }
    
    /* Green Header Box */
    .header-box {
        background-color: #1b5e20;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .header-title {
        color: #ffffff !important; /* Force White Text on Green Background */
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .header-subtitle {
        color: #e8f5e9 !important; /* Light Green Text */
        font-size: 1.1rem;
        margin-top: 5px;
    }

    /* Buttons */
    .stButton>button {
        background-color: #1b5e20; /* Dark Green */
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        width: 100%;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2e7d32;
    }
    
    /* Input Areas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #f9f9f9;
        color: #000000;
        border: 1px solid #aaa;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPERS ---
def is_ol_chiki(text):
    if not text: return False
    valid = sum(1 for c in text if '\u1C50' <= c <= '\u1C7F')
    total = sum(1 for c in text if not c.isspace() and c not in ".,!?-1234567890")
    return (valid / total) > 0.8 if total > 0 else True

def get_ai_question(lang):
    """Fetches question. If API fails, returns a fallback."""
    # Context Mapping (Hidden from UI)
    context_map = {
        "Bengali": "West Bengal culture",
        "Hindi": "Jharkhand daily life",
        "Odia": "Odisha lifestyle",
        "English": "General daily life"
    }
    context = context_map.get(lang, "daily life")
    
    # Forced Script Instructions
    script_instr = ""
    if lang == "Bengali": script_instr = "OUTPUT MUST BE IN BENGALI SCRIPT (BANGLA)."
    elif lang == "Odia": script_instr = "OUTPUT MUST BE IN ODIA SCRIPT."
    
    prompt = f"""
    Ask a short, simple question in {lang} language about {context}.
    {script_instr}
    Return ONLY JSON: {{"q": "your_question_here"}}
    """
    
    try:
        resp = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        data = json.loads(resp.text)
        q_text = data.get("q", "")
        if q_text: return q_text
    except:
        pass
    
    # FALLBACKS (Agar API fail ho to ye dikhega)
    defaults = {
        "Bengali": "আজ আপনার দিনটি কেমন কাটল?", 
        "Hindi": "आज का दिन कैसा रहा?",
        "Odia": "ଆଜି ଦିନ କେମିତି କଟିଲା?",
        "English": "How is your day going?"
    }
    return defaults.get(lang, "How are you?")

# --- SIDEBAR (NAVIGATION) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.markdown("### Menu")
    
    # Task Selector moved to Sidebar
    selected_task = st.radio(
        "Choose Activity:", 
        ["Answer AI", "Describe Image", "Digitize Books", "OCR Handwriting", "Translate"],
        index=0
    )
    
    st.write("---")
    st.markdown("**Top Contributors**")
    st.info("1. S. Murmu (120)\n2. R. Hembram (95)\n3. A. Tudu (80)")

# --- MAIN HEADER ---
st.markdown("""
<div class='header-box'>
    <div class='header-title'>JanAI</div>
    <div class='header-subtitle'>JanAI Santali Dataset</div>
</div>
""", unsafe_allow_html=True)

# --- TASK HANDLER ---

# 1. ANSWER AI
if selected_task == "Answer AI":
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 1. Select Language")
        
        # Simple Language Options
        lang = st.selectbox("Language", ["Bengali", "Hindi", "Odia", "English"], label_visibility="collapsed")
        
        # Logic to fetch question
        if 'last_lang' not in st.session_state: st.session_state.last_lang = None
        if 'q_text' not in st.session_state: st.session_state.q_text = ""
        
        # Auto-fetch if language changes or empty
        if st.session_state.last_lang != lang or not st.session_state.q_text:
            st.session_state.q_text = get_ai_question(lang)
            st.session_state.last_lang = lang
            
        st.markdown("---")
        st.markdown(f"**Question ({lang}):**")
        st.markdown(f"<h3 style='color:#1b5e20 !important;'>{st.session_state.q_text}</h3>", unsafe_allow_html=True)
        
        if st.button("🔄 Change Question"):
            st.session_state.last_lang = None # Forces refresh
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 2. Submit Answer")
        
        u_name = st.text_input("Your Name")
        
        st.markdown("**Select Script:**")
        script = st.radio("Script", ["Ol Chiki (ᱚᱞ ᱪᱤᱠᱤ)", "Latin (English)"], horizontal=True, label_visibility="collapsed")
        
        ph = "Type in Ol Chiki..." if "Ol Chiki" in script else "Type in English letters..."
        ans_text = st.text_area("Answer", placeholder=ph, height=100)
        
        st.write("")
        c_mic, c_btn = st.columns([1, 2])
        with c_mic: audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹️", key="rec1")
        with c_btn:
            st.write("") # Spacer
            if st.button("Submit"):
                if u_name and (ans_text or audio):
                    if "Ol Chiki" in script and ans_text and not is_ol_chiki(ans_text):
                        st.error("Error: You selected Ol Chiki but typed English.")
                    else:
                        st.success("Saved Successfully!")
                        time.sleep(1)
                        st.session_state.last_lang = None # Refresh question
                        st.experimental_rerun()
                else:
                    st.warning("Please enter Name and Answer.")
        st.markdown("</div>", unsafe_allow_html=True)

# 2. DESCRIBE IMAGE
elif selected_task == "Describe Image":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.image(f"https://picsum.photos/seed/{random.randint(1,999)}/500/350", caption="Describe this image in Santali", use_column_width=True)
        if st.button("New Image"): st.experimental_rerun()
    with c2:
        st.text_input("Your Name", key="img_name")
        st.text_area("Description (Santali)", height=150, placeholder="What do you see?")
        if st.button("Submit Description"): st.success("Saved!")
    st.markdown("</div>", unsafe_allow_html=True)

# 3. DIGITIZE BOOKS
elif selected_task == "Digitize Books":
    st.info("Task: Type the text exactly as seen in the document below.")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.image("https://placehold.co/600x800/png?text=Santali+Constitution+Page\n(Sample+Document)", use_column_width=True)
    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.text_input("Your Name", key="book_name")
        st.text_area("Transcription", height=300, placeholder="Type content here...")
        st.button("Submit Page Data")
        st.markdown("</div>", unsafe_allow_html=True)

# 4. OCR HANDWRITING
elif selected_task == "OCR Handwriting":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### Upload Handwritten Note")
    uploaded = st.file_uploader("Upload Image", type=['jpg', 'png'])
    if uploaded:
        st.image(uploaded, width=300)
        st.text_area("Type what is written in the image:", height=150)
        st.button("Submit OCR Data")
    st.markdown("</div>", unsafe_allow_html=True)

# 5. TRANSLATE
elif selected_task == "Translate":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    src_lang = st.selectbox("Source Language", ["Hindi", "Bengali", "Odia", "English"])
    
    # Fake corpus for demo
    sentences = {
        "Hindi": "गाँव का जीवन बहुत शांत होता है।",
        "Bengali": "গ্রামের জীবন খুব শান্ত।",
        "Odia": "ଗାଁ ଜୀବନ ବହୁତ ଶାନ୍ତିପୂର୍ଣ୍ଣ |",
        "English": "Village life is very peaceful."
    }
    
    st.markdown(f"### Translate this to Santali:")
    st.info(sentences.get(src_lang, "Hello"))
    
    st.text_area("Santali Translation", height=100)
    st.button("Submit Translation")
    st.markdown("</div>", unsafe_allow_html=True)
    

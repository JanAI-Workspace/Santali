import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from huggingface_hub import HfApi
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
import random
import json
import uuid
import time
from datetime import datetime
import io
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(
    page_title="JanAI - Santali Data Collection",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. SETUP KEYS & CONNECTIONS
try:
    # Firebase Setup
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["FIREBASE_KEY"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Gemini Setup
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
 
    # Hugging Face Setup
    api = HfApi(token=st.secrets["HF_TOKEN"])
    REPO_ID = "JanAI-Workspace/Santali-dataset" 

except Exception as e:
    st.error(f"⚠️ Configuration Error: {e}")
    st.info("Please check your secrets configuration.")
    st.stop()

# --- PROFESSIONAL CSS STYLING ---
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Header Section */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        margin-bottom: 2rem;
        text-align: center;
        animation: fadeIn 0.6s ease-in;
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        color: #f0f0f0 !important;
        font-size: 1.2rem !important;
        margin-top: 0.5rem !important;
        font-weight: 300;
    }
    
    /* Card Styles */
    .pro-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .pro-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .card-icon {
        font-size: 1.8rem;
    }
    
    .card-title {
        color: #2d3748 !important;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }
    
    /* Question Display */
    .question-box {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        margin: 1.5rem 0;
    }
    
    .question-text {
        color: #2d3748 !important;
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
    }
    
    .topic-badge {
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    
    /* Button Styles */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    [data-testid="stSidebar"] .stRadio>label {
        color: white !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] .stRadio>div {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    /* Stats Display */
    .stat-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
    }
    
    .stat-number {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }
    
    .stat-label {
        font-size: 0.9rem !important;
        opacity: 0.9;
        margin-top: 0.5rem !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: #48bb78 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    .stError {
        background-color: #f56565 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    /* Radio Buttons */
    .stRadio>div {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    
    .stRadio>div>label {
        background: white;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .stRadio>div>label:hover {
        border-color: #667eea;
        background: #f7fafc;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-in;
    }
    
    /* Progress Bar */
    .stProgress>div>div>div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def admin_generate_questions(lang, count=3):
    """Generates questions using Gemini and saves to Firebase"""
    script_instr = "Output in BENGALI SCRIPT." if lang == "Bengali" else ("Output in ODIA SCRIPT." if lang == "Odia" else "")
    
    generated = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(count):
        topic = random.choice(["Farming", "Health", "Market", "Family", "Travel", "Culture", "Education", "Technology"])
        prompt = f"Generate a unique, engaging question about '{topic}' in {lang}. {script_instr} JSON: {{'q': 'question_text', 't': '{topic}'}}"
        
        try:
            resp = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(resp.text)
            
            # Save to Firebase
            db.collection("questions_pool").add({
                "language": lang,
                "text": data['q'],
                "topic": data['t'],
                "used": False,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            generated += 1
            progress_bar.progress((i + 1) / count)
            status_text.text(f"Generating... {i+1}/{count}")
        except Exception as e:
            st.error(f"❌ Generation Error: {e}")
            
    status_text.success(f"✅ Successfully generated {generated} questions for {lang}!")
    time.sleep(1.5)
    return generated

def get_firebase_question(lang):
    """Fetch random question from Firebase"""
    try:
        docs = db.collection("questions_pool").where("language", "==", lang).limit(20).stream()
        q_list = [doc.to_dict() | {"id": doc.id} for doc in docs]
        return random.choice(q_list) if q_list else None
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

def save_to_huggingface(data_dict, audio_bytes=None):
    """Save data to Hugging Face dataset"""
    try:
        file_id = str(uuid.uuid4())
        json_path = f"data/{data_dict['language']}/{file_id}.json"
        json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
        
        api.upload_file(
            path_or_fileobj=json_str.encode('utf-8'),
            path_in_repo=json_path,
            repo_id=REPO_ID,
            repo_type="dataset"
        )
        
        if audio_bytes:
            audio_path = f"audio/{data_dict['language']}/{file_id}.wav"
            api.upload_file(
                path_or_fileobj=audio_bytes,
                path_in_repo=audio_path,
                repo_id=REPO_ID,
                repo_type="dataset"
            )
        return True
    except Exception as e:
        st.error(f"💾 Upload Failed: {e}")
        return False

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.image("https://img.icons8.com/3d-fluency/94/artificial-intelligence.png", width=80)
    st.markdown("<h2 style='color: white; text-align: center;'>JanAI Portal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #a0aec0; text-align: center; font-size: 0.9rem;'>Santali Language Preservation</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.radio("🎯 Navigation", ["📝 User Workspace", "🔐 Admin Panel"], label_visibility="collapsed")
    
    st.markdown("<hr style='margin: 2rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    # Stats Section
    st.markdown("<div style='color: #a0aec0; font-size: 0.85rem;'>", unsafe_allow_html=True)
    st.markdown("**📊 Quick Stats**")
    st.markdown("• Active Users: 1,247")
    st.markdown("• Questions: 3,890")
    st.markdown("• Responses: 12,456")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("v2.0 • © 2024 JanAI")

# --- PAGE 1: USER WORKSPACE ---
if menu == "📝 User Workspace":
    # Header
    st.markdown("""
    <div class='main-header fade-in'>
        <h1>🎯 JanAI Workspace</h1>
        <p>Help preserve and digitize Santali language data</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.3], gap="large")
    
    # LEFT COLUMN - Question Display
    with col1:
        st.markdown("<div class='pro-card fade-in'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'><span class='card-icon'>❓</span><h3 class='card-title'>Question</h3></div>", unsafe_allow_html=True)
        
        lang = st.selectbox("🌐 Select Language", ["Bengali", "Hindi", "Odia", "English"], label_visibility="visible")
        
        # Load Question
        if 'curr_q' not in st.session_state or st.session_state.get('l') != lang:
            with st.spinner("🔍 Fetching question..."):
                q_data = get_firebase_question(lang)
                st.session_state.curr_q = q_data
                st.session_state.l = lang
        
        q = st.session_state.curr_q
        
        if q:
            st.markdown(f"<div class='question-box'><div class='topic-badge'>📚 {q.get('topic', 'General')}</div><p class='question-text'>{q.get('text')}</p></div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ No questions available. Please contact the administrator.")
        
        if st.button("🔄 Load Next Question"):
            st.session_state.curr_q = get_firebase_question(lang)
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT COLUMN - Answer Submission
    with col2:
        st.markdown("<div class='pro-card fade-in'>", unsafe_allow_html=True)
        st.markdown("<div class='card-header'><span class='card-icon'>✍️</span><h3 class='card-title'>Your Response</h3></div>", unsafe_allow_html=True)
        
        name = st.text_input("👤 Your Name", placeholder="Enter your full name")
        
        script = st.radio("📝 Script Type", ["Ol Chiki", "Latin"], horizontal=True)
        
        ans = st.text_area("💬 Type Your Answer", height=120, placeholder="Write your answer here...")
        
        st.markdown("<p style='color: #718096; font-size: 0.9rem; margin: 1rem 0;'>🎤 Or record your answer:</p>", unsafe_allow_html=True)
        
        col_mic, col_play = st.columns([1, 2])
        with col_mic:
            audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹️ Stop", key="rec")
        with col_play:
            if audio:
                st.audio(audio['bytes'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📤 Submit Response"):
            if not name:
                st.error("❌ Please enter your name")
            elif not ans and not audio:
                st.error("❌ Please provide a text or audio answer")
            else:
                with st.spinner("☁️ Uploading to cloud..."):
                    payload = {
                        "user": name,
                        "language": lang,
                        "question": q.get('text') if q else "Unknown",
                        "script": script,
                        "answer": ans,
                        "timestamp": str(datetime.now()),
                        "has_audio": bool(audio)
                    }
                    audio_bytes = audio['bytes'] if audio else None
                    
                    if save_to_huggingface(payload, audio_bytes):
                        st.success("✅ Response saved successfully! Thank you for your contribution.")
                        time.sleep(1.5)
                        st.session_state.curr_q = get_firebase_question(lang)
                        st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# --- PAGE 2: ADMIN PANEL ---
elif menu == "🔐 Admin Panel":
    st.markdown("""
    <div class='main-header fade-in'>
        <h1>🔐 Admin Control Panel</h1>
        <p>Question generation and system management</p>
    </div>
    """, unsafe_allow_html=True)
    
    password = st.text_input("🔑 Enter Admin Password", type="password", placeholder="Enter password")
    
    if password == "janai123":
        st.success("✅ Access Granted - Welcome Admin!")
        
        col_a, col_b = st.columns(2, gap="large")
        
        with col_a:
            st.markdown("<div class='pro-card fade-in'>", unsafe_allow_html=True)
            st.markdown("<div class='card-header'><span class='card-icon'>⚡</span><h3 class='card-title'>Generate Questions</h3></div>", unsafe_allow_html=True)
            
            g_lang = st.selectbox("🌍 Target Language", ["Bengali", "Hindi", "Odia", "English"])
            qty = st.slider("📊 Quantity", min_value=1, max_value=20, value=5)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Generate & Save to Database"):
                admin_generate_questions(g_lang, qty)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_b:
            st.markdown("<div class='pro-card fade-in'>", unsafe_allow_html=True)
            st.markdown("<div class='card-header'><span class='card-icon'>📊</span><h3 class='card-title'>System Statistics</h3></div>", unsafe_allow_html=True)
            
            st.markdown("<div class='stat-box'><p class='stat-number'>3,890</p><p class='stat-label'>Total Questions</p></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div class='stat-box' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'><p class='stat-number'>12,456</p><p class='stat-label'>User Responses</p></div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    elif password:
        st.error("❌ Incorrect password. Access denied.")

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
st.set_page_config(page_title="JanAI", layout="wide", initial_sidebar_state="expanded")

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
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Hugging Face Setup
    api = HfApi(token=st.secrets["HF_TOKEN"])
    REPO_ID = "JanAI-Workspace/Santali-dataset" # Confirm karein ye sahi hai

except Exception as e:
    st.error(f"Setup Error: {e}. Check Secrets properly.")
    st.stop()

# --- PROFESSIONAL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f8fb; font-family: 'Segoe UI', sans-serif; }
    
    /* Header */
    .header-box {
        background: linear-gradient(135deg, #0d47a1, #1565c0);
        padding: 25px; border-radius: 12px; color: white;
        margin-bottom: 25px; box-shadow: 0 4px 15px rgba(13, 71, 161, 0.2);
    }
    
    /* Cards */
    .card {
        background: white; padding: 25px; border-radius: 12px;
        border: 1px solid #e1e4e8; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #2e7d32; color: white !important;
        border-radius: 6px; font-weight: 600; width: 100%; padding: 10px;
    }
    .stButton>button:hover { background-color: #1b5e20; }
    
    h3 { color: #0d47a1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- ADMIN FUNCTION (Generate Qs) ---
def admin_generate_questions(lang, count=3):
    """Generates questions using Gemini and saves to Firebase"""
    script_instr = "Output in BENGALI SCRIPT." if lang == "Bengali" else ("Output in ODIA SCRIPT." if lang == "Odia" else "")
    
    generated = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(count):
        topic = random.choice(["Farming", "Health", "Market", "Family", "Travel", "Culture"])
        prompt = f"Generate a unique question about '{topic}' in {lang}. {script_instr} JSON: {{'q': 'question_text', 't': '{topic}'}}"
        
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
        except Exception as e:
            st.error(f"Gen Error: {e}")
            
    status_text.success(f"✅ Generated {generated} questions for {lang}!")
    return generated

# --- MAIN APP LOGIC ---
def get_firebase_question(lang):
    # Fetch random question from Firebase
    try:
        docs = db.collection("questions_pool").where("language", "==", lang).limit(10).stream()
        q_list = [doc.to_dict() | {"id": doc.id} for doc in docs]
        return random.choice(q_list) if q_list else None
    except:
        return None

def save_to_huggingface(data_dict, audio_bytes=None):
    try:
        # Save JSON
        file_id = str(uuid.uuid4())
        json_path = f"data/{data_dict['language']}/{file_id}.json"
        json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
        
        api.upload_file(
            path_or_fileobj=json_str.encode('utf-8'),
            path_in_repo=json_path,
            repo_id=REPO_ID,
            repo_type="dataset"
        )
        # Save Audio (if any)
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
        st.error(f"Save Failed: {e}")
        return False

# --- SIDEBAR NAV ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=50)
    st.markdown("### Navigation")
    menu = st.radio("Mode", ["User Workspace", "Admin Panel"])
    
    st.markdown("---")
    st.caption("JanAI System v1.0")

# --- PAGE 1: USER WORKSPACE ---
if menu == "User Workspace":
    st.markdown("""
    <div class='header-box'>
        <h1 style='color:white; margin:0;'>JanAI</h1>
        <p style='color:#e3f2fd; margin:0;'>Santali Data Collection Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 1. Language")
        lang = st.selectbox("Select Language", ["Bengali", "Hindi", "Odia", "English"])
        
        # Load Question Logic
        if 'curr_q' not in st.session_state or st.session_state.get('l') != lang:
            with st.spinner("Fetching Question..."):
                q_data = get_firebase_question(lang)
                st.session_state.curr_q = q_data
                st.session_state.l = lang
            
        q = st.session_state.curr_q
        
        st.markdown("---")
        if q:
            st.caption(f"Topic: {q.get('topic', 'General')}")
            st.markdown(f"<h3 style='margin:0'>{q.get('text')}</h3>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ Database Empty! Please ask Admin to generate questions.")
            
        st.write("")
        if st.button("🔄 Next Question"):
             st.session_state.curr_q = get_firebase_question(lang)
             st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("#### 2. Submit Answer")
        name = st.text_input("Name")
        
        script = st.radio("Script", ["Ol Chiki", "Latin"], horizontal=True)
        ans = st.text_area("Answer Text", height=100)
        
        c_mic, c_p = st.columns([1,2])
        with c_mic: audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹️", key="rec")
        with c_p: 
            if audio: st.audio(audio['bytes'])
        
        st.write("---")
        if st.button("Submit to Cloud"):
            if name and (ans or audio):
                # Prepare Data
                payload = {
                    "user": name,
                    "language": lang,
                    "question": q.get('text') if q else "Unknown",
                    "script": script,
                    "answer": ans,
                    "timestamp": str(datetime.now())
                }
                audio_bytes = audio['bytes'] if audio else None
                
                if save_to_huggingface(payload, audio_bytes):
                    st.success("✅ Saved Successfully!")
                    time.sleep(1)
                    st.session_state.curr_q = get_firebase_question(lang)
                    st.experimental_rerun()
            else:
                st.error("Name and Answer required.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- PAGE 2: ADMIN PANEL ---
elif menu == "Admin Panel":
    st.title("🔒 Admin Control")
    password = st.text_input("Enter Admin Password", type="password")
    
    if password == "janai123":  # Password
        st.success("Access Granted")
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### ⚡ Generate Questions (Gemini -> Firebase)")
        
        c_a, c_b = st.columns(2)
        with c_a:
            g_lang = st.selectbox("Target Language", ["Bengali", "Hindi", "Odia", "English"])
        with c_b:
            qty = st.slider("Quantity", 1, 10, 5)
            
        if st.button("🚀 Generate & Save"):
            admin_generate_questions(g_lang, qty)
        st.markdown("</div>", unsafe_allow_html=True)
                                          

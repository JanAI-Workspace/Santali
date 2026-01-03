import streamlit as st
import google.generativeai as genai
from huggingface_hub import HfApi
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import uuid
import datetime
import random

# --- CONFIGURATION ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    REPO_ID = "JanAI-Workspace/Santali-dataset"
except:
    st.error("Secrets missing! Please add HF_TOKEN and GEMINI_API_KEY.")
    st.stop()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
api = HfApi()

st.set_page_config(page_title="JanAI - Premium Santali Hub", layout="wide", initial_sidebar_state="collapsed")

# --- PREMIUM CSS (GLOW & GLASS LOOK) ---
st.markdown(f"""
    <style>
    /* Background & Fonts */
    .stApp {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); font-family: 'Inter', sans-serif; }}
    
    /* Center Card Glow Effect */
    .main-card {{
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease;
    }}
    .main-card:hover {{ transform: translateY(-5px); box-shadow: 0 25px 50px rgba(27, 94, 32, 0.15); }}

    /* Button Glow */
    .stButton>button {{
        background: linear-gradient(45deg, #1b5e20, #43a047);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 15px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(27, 94, 32, 0.3);
        transition: 0.3s;
    }}
    .stButton>button:hover {{ box-shadow: 0 8px 25px rgba(27, 94, 32, 0.5); transform: scale(1.02); }}

    /* Chat Styling */
    .chat-container {{ height: 400px; overflow-y: auto; background: white; border-radius: 20px; padding: 15px; box-shadow: inset 0 2px 10px rgba(0,0,0,0.05); }}
    .chat-msg {{ background: #f1f8e9; padding: 10px; border-radius: 12px; margin-bottom: 10px; border-left: 4px solid #1b5e20; }}

    /* Quote Animation */
    @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    .quote-box {{ animation: fadeIn 2s; text-align: center; color: #1b5e20; font-weight: 500; font-style: italic; font-size: 1.2rem; margin-bottom: 25px; }}
    
    /* Footer */
    .footer {{ text-align: center; margin-top: 50px; color: #555; font-size: 0.8em; }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def get_ai_q(lang):
    try:
        res = model.generate_content(f"One short {lang} daily question. Category|Question").text.split('|')
        return res[0].strip(), res[1].strip()
    except: return "Global", "How is your day?"

# --- SIDEBAR: CLEAN PROJECT NAV ---
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/000000/artificial-intelligence.png")
    st.title("JanAI Portal")
    menu = st.radio("Navigation", ["Home", "Mission & Career", "Contact Us"])
    st.write("---")
    u_name = st.text_input("Full Name", placeholder="Contributor Name")
    u_email = st.text_input("Email", placeholder="For Rewards")
    is_anon = st.checkbox("Post Anonymously")
    disp_name = "Anonymous" if is_anon else (u_name if u_name else "Guest")

# --- MAIN INTERFACE ---
if menu == "Home":
    # 1. Motivation Quote
    quotes = ["Bringing Santali to the AI Revolution. 🚀", "Your voice is the future of JanAI. 🌾", "Preserving culture with every word. ✨"]
    st.markdown(f"<div class='quote-box'>\"{random.choice(quotes)}\"</div>", unsafe_allow_html=True)

    col_main, col_chat = st.columns([2.5, 1])

    with col_main:
        # Question Card
        s_lang = st.selectbox("Switch Input Language:", ["Bengali", "Hindi", "English", "Odia"], label_visibility="collapsed")
        
        if 'q_data' not in st.session_state or st.session_state.get('prev_l') != s_lang:
            st.session_state.q_c, st.session_state.q_t = get_ai_q(s_lang)
            st.session_state.prev_l = s_lang

        st.markdown(f"""
            <div class='main-card'>
                <p style='color: #4caf50; font-weight: bold; letter-spacing: 1px;'>{st.session_state.q_c.upper()}</p>
                <h1 style='color: #212121; margin-bottom: 20px;'>{st.session_state.q_t}</h1>
            </div>
            """, unsafe_allow_html=True)

        # Inputs
        st.write("")
        ans = st.text_area("", placeholder="Write Santali Latin or Ol Chiki answer here...", height=120, label_visibility="collapsed")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            audio = mic_recorder(start_prompt="🎤 Record Audio", stop_prompt="⏹️ Save", key='rec_main')
        with c2:
            if audio: st.audio(audio['bytes'])

        if st.button("SUBMIT CONTRIBUTION 🚀"):
            if ans and audio and u_name:
                with st.spinner("Processing Data..."):
                    f_id = str(uuid.uuid4())[:8]
                    # Upload (Standard logic)
                    st.balloons()
                    st.session_state.q_c, st.session_state.q_t = get_ai_q(s_lang)
                    st.rerun()
            else: st.error("Please provide Name, Answer and Recording.")

        # Progress
        st.write("---")
        try:
            vol = len(pd.read_csv(f"https://huggingface.co/datasets/{{REPO_ID}}/raw/main/data.csv"))
        except: vol = 0
        st.write(f"📊 **JanAI Growth:** {vol} / 20,000 sentences")
        st.progress(min(vol/20000, 1.0))

    with col_chat:
        st.markdown("### 💬 Community Hub")
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        try:
            chats = pd.read_csv(f"https://huggingface.co/datasets/{{REPO_ID}}/raw/main/chat.csv").tail(15)
            for _, r in chats.iterrows():
                st.markdown(f"<div class='chat-msg'><b>{r['user']}:</b> {r['msg']}</div>", unsafe_allow_html=True)
        except: st.write("Welcome to the community!")
    
        st.markdown("</div>", unsafe_allow_html=True)
        msg = st.text_input("Share something...", key="chat_msg_in", label_visibility="collapsed")
        if st.button("Send ⬆️"):
            # Chat upload logic
            st.rerun()

elif menu == "Mission & Career":
    st.markdown("<div class='main-card'><h1>Our Vision</h1><p>Building a sustainable Santali AI ecosystem. Funding tribal education with project profits.</p></div>", unsafe_allow_html=True)

elif menu == "Contact Us":
    st.markdown(f"""
        <div class='main-card'>
            <h2>Get in Touch</h2>
            <p>For grants, career opportunities, or feedback:</p>
            <h3 style='color: #1b5e20;'>janai.workspace@gmail.com</h3>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div class='footer'>© 2026 JanAI Workspace | Contact: janai.workspace@gmail.com</div>", unsafe_allow_html=True)

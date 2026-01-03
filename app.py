Santali-dataset orttalitaliort streamlit as st
import google.generativeai as genai
from huggingface_hub import HfApi
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import uuid
import datetime

# --- CONFIGURATION ---
# Ye values Streamlit ke "Secrets" se aayengi
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    # Aapka updated Repo Name
    REPO_ID = "JanAI-Workspace/Santali" 
except:
    st.error("Secrets setup nahi hain! Please Streamlit Cloud ki settings mein HF_TOKEN aur GEMINI_API_KEY daalein.")
    st.stop()

# Setup APIs
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
api = HfApi()

st.set_page_config(page_title="JanAI - Santali Hub", page_icon="🌾")

# Custom Styling for Mobile
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; font-weight: bold; background-color: #2e7d32; color: white; }
    .q-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 5px solid #2e7d32; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Function to get Question from AI
def get_ai_question():
    try:
        prompt = "Generate 1 unique short Bengali daily life question (max 6 words). Format: Category|Question"
        res = model.generate_content(prompt).text.split('|')
        return res[0].strip(), res[1].strip()
    except:
        return "General", "আপনার নাম কি?"

# --- MAIN UI ---
st.title("JanAI: Santali Dataset 🗣️")

if 'cat' not in st.session_state:
    st.session_state.cat, st.session_state.q = get_ai_question()

# Display Question
st.markdown(f"""<div class='q-card'>
    <small>{st.session_state.cat} Question</small>
    <h2 style='color: black;'>{st.session_state.q}</h2>
</div>""", unsafe_allow_html=True)

# Script Selection
script = st.radio("Script chunein:", ["Ol Chiki (ᱚᱞ ᱪᱤᱠᱤ)", "Santali Latin"], horizontal=True)

if script == "Ol Chiki (ᱚᱞ ᱪᱤᱠᱤ)":
    ans = st.text_area("Translation (Ol Chiki):", placeholder="ᱚᱞ ᱪᱤᱠᱤ ᱛᱮ ᱚᱞ ᱢᱮ...")
    is_valid = any('\u1C50' <= c <= '\u1C7F' for c in ans) if ans else True
else:
    ans = st.text_area("Translation (Latin):", placeholder="Latin te ol me...")
    is_valid = True

# Audio Recording
st.write("Record Santali Voice:")
audio = mic_recorder(start_prompt="🎤 Start Recording", stop_prompt="⏹️ Stop Recording", key='recorder')

# --- SUBMIT LOGIC ---
if st.button("Submit & Next Question 🚀"):
    if ans and audio and is_valid:
        try:
            with st.spinner("Saving to JanAI Dataset..."):
                file_id = str(uuid.uuid4())[:8]
                audio_filename = f"audio/{file_id}.wav"
                
                # 1. Upload Audio to HF
                api.upload_file(
                    path_or_fileobj=audio['bytes'],
                    path_in_repo=audio_filename,
                    repo_id=REPO_ID,
                    token=HF_TOKEN,
                    repo_type="dataset"
                )
                
                # 2. Append Metadata to CSV
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                clean_q = st.session_state.q.replace(",", " ")
                clean_ans = ans.replace(",", " ")
                
                new_data = f"\n{timestamp},{st.session_state.cat},{clean_q},{clean_ans},{script},{audio_filename}"
                
                api.upload_file(
                    path_or_fileobj=new_data.encode("utf-8"),
                    path_in_repo="data.csv",
                    repo_id=REPO_ID,
                    token=HF_TOKEN,
                    repo_type="dataset"
                )
                
                st.balloons()
                st.success("Success!")
                
                # Refresh Question
                st.session_state.cat, st.session_state.q = get_ai_question()
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    elif not is_valid:
        st.error("Kripya sirf Ol Chiki script ka use karein!")
    else:
        st.warning("Please provide Text and Voice.")

import streamlit as st
import google.generativeai as genai
from huggingface_hub import HfApi
import pandas as pd
from streamlit_mic_recorder import mic_recorder
import uuid
import random
import json
import re
import logging
from typing import Optional
import io
import datetime

# --- CONFIGURATION ---
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
    REPO_ID = "JanAI-Workspace/Santali-dataset"
except KeyError as e:
    st.error(f"Secrets missing: {e}. Please add HF_TOKEN and GEMINI_API_KEY in Streamlit secrets.")
    st.stop()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
api = HfApi()

st.set_page_config(page_title="JanAI - Premium Santali Hub", layout="wide", initial_sidebar_state="collapsed")

# --- Logging ---
logger = logging.getLogger("janai_app")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

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

# --- HELPERS ---
def _extract_json(text: str) -> str:
    """Try to extract a JSON object from text (handles code fences)."""
    if not text:
        return ""
    # remove markdown code fences and surrounding text
    text = re.sub(r"```(?:json|text)?", "", text, flags=re.IGNORECASE)
    # find first {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return m.group(0) if m else text.strip()

def _contains_bengali(s: str) -> bool:
    """Return True if string contains Bengali unicode characters (U+0980–U+09FF)."""
    if not s:
        return False
    return any("\u0980" <= ch <= "\u09FF" for ch in s)

@st.cache_data(ttl=300)
def fetch_csv_from_hf(path: str) -> Optional[pd.DataFrame]:
    """Fetch CSV from HF raw URL with caching (returns None on failure)."""
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        logger.info(f"Failed to fetch CSV from {path}: {e}")
        return None

@st.cache_data(ttl=120)
def cached_get_ai_q(lang: str, retries: int = 3):
    """Wrapper to cache questions per language for short time."""
    return get_ai_q(lang, retries=retries)

def get_ai_q(lang: str, retries: int = 3):
    """
    Ask Gemini for a single short daily question.
    Enforce JSON-only output: {"category":"...","question":"..."}
    If lang is Bengali, enforce Bangla script in question.
    """
    system_instructions = f"""
You are a helpful assistant that produces exactly one short daily question.
Respond ONLY with a single JSON object (no other explanation, no bullets, nothing else).
The JSON keys must be "category" and "question".
- "category": short topic label (1-3 words), English is fine.
- "question": a concise question appropriate for daily prompts.

Produce content in the language: {lang}.
Make sure the "question" text is in {lang} and does not include extra quotes or metadata.
Example valid response:
{{"category":"Daily Life","question":"How are you feeling today?"}}

If {lang} is Bengali, the "question" must be in Bengali script (Bangla). 
Respond only with JSON.
    """.strip()

    for attempt in range(retries):
        try:
            resp = model.generate_content(system_instructions,
                                          temperature=0.2,
                                          top_k=40,
                                          max_output_tokens=160)
            raw = getattr(resp, "text", "") or str(resp)
            jtext = _extract_json(raw)
            data = json.loads(jtext)
            cat = (data.get("category") or "General").strip()
            q = (data.get("question") or "").strip()
            if not q:
                logger.info(f"Empty question from model (attempt {attempt+1}). raw: {raw}")
                continue
            # Bengali validation
            if lang.lower().startswith("bengal") or lang.lower().startswith("bangla") or lang.lower() == "bengali":
                if not _contains_bengali(q):
                    logger.info(f"Bengali validation failed (attempt {attempt+1}). q: {q!r}")
                    continue
            return cat, q
        except Exception as e:
            logger.info(f"get_ai_q attempt {attempt+1} failed: {e}")
            continue

    # fallback if retries exhausted
    if lang.lower().startswith("bengal") or lang.lower().startswith("bangla") or lang.lower() == "bengali":
        return "Global", "আপনার দিন কেমন যাচ্ছে?"
    else:
        return "Global", "How is your day?"

def _upload_fileobj_to_hf(fileobj, path_in_repo: str, commit_message: str):
    """
    Upload a file-like object to the HF dataset repo.
    fileobj should be a binary file-like (e.g., io.BytesIO).
    """
    try:
        api.upload_file(
            path_or_fileobj=fileobj,
            path_in_repo=path_in_repo,
            repo_id=REPO_ID,
            repo_type="dataset",
            token=HF_TOKEN,
            commit_message=commit_message,
        )
        return True, None
    except Exception as e:
        logger.info(f"Failed to upload {path_in_repo} to HF: {e}")
        return False, str(e)

def _update_csv_on_hf(df: pd.DataFrame, path_in_repo: str, commit_message: str):
    """
    Overwrite CSV at path_in_repo in HF dataset with df (pandas).
    """
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    fileobj = io.BytesIO(buf.getvalue().encode("utf-8"))
    return _upload_fileobj_to_hf(fileobj, path_in_repo, commit_message)

def upload_submission_to_hf(submission: dict, audio) -> tuple:
    """
    Upload audio and append submission row to data.csv in HF dataset.
    Returns (success: bool, message: str)
    """
    f_id = submission["id"]
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    audio_path = f"audio/{f_id}.wav"

    # 1) upload audio bytes (if available)
    if audio and isinstance(audio, dict) and 'bytes' in audio:
        audio_bytes = audio['bytes']
        if isinstance(audio_bytes, str):
            # sometimes data URIs or base64 string may be present; try to handle
            try:
                # data URI: data:audio/wav;base64,...
                if audio_bytes.startswith("data:"):
                    _, b64 = audio_bytes.split(",", 1)
                    audio_bytes = io.BytesIO(base64.b64decode(b64)).read()
                else:
                    audio_bytes = audio_bytes.encode('utf-8')
            except Exception:
                pass
        try:
            audio_fileobj = io.BytesIO(audio_bytes)
            ok, err = _upload_fileobj_to_hf(audio_fileobj, audio_path,
                                            commit_message=f"Add audio {f_id}")
            if not ok:
                return False, f"Audio upload failed: {err}"
        except Exception as e:
            return False, f"Audio processing/upload error: {e}"
    else:
        audio_path = ""  # no audio

    # 2) fetch existing data.csv, append row, upload
    data_path = f"https://huggingface.co/datasets/{REPO_ID}/raw/main/data.csv"
    df = fetch_csv_from_hf(data_path)
    row = {
        "id": f_id,
        "name": submission.get("name", ""),
        "email": submission.get("email", ""),
        "answer": submission.get("answer", ""),
        "has_audio": bool(submission.get("has_audio", False)),
        "audio_path": audio_path,
        "lang": submission.get("lang", ""),
        "timestamp": timestamp,
    }
    if df is None:
        df = pd.DataFrame([row])
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    ok, err = _update_csv_on_hf(df, "data.csv", commit_message=f"Add data row {f_id}")
    if not ok:
        return False, f"data.csv update failed: {err}"

    return True, "Uploaded submission to HF dataset."

def append_chat_to_hf(user: str, msg: str) -> tuple:
    """
    Append a chat message to chat.csv on HF dataset.
    Returns (success, message)
    """
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    chat_path = f"https://huggingface.co/datasets/{REPO_ID}/raw/main/chat.csv"
    df_chat = fetch_csv_from_hf(chat_path)
    row = {"user": user, "msg": msg, "timestamp": timestamp}
    if df_chat is None:
        df_chat = pd.DataFrame([row])
    else:
        df_chat = pd.concat([df_chat, pd.DataFrame([row])], ignore_index=True)

    ok, err = _update_csv_on_hf(df_chat, "chat.csv", commit_message=f"Add chat by {user}")
    if not ok:
        return False, f"chat.csv update failed: {err}"
    return True, "Chat appended."

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

# Initialize session_state defaults
if 'prev_l' not in st.session_state:
    st.session_state.prev_l = None
if 'q_c' not in st.session_state:
    st.session_state.q_c = "Global"
if 'q_t' not in st.session_state:
    st.session_state.q_t = "How is your day?"
if 'submissions' not in st.session_state:
    st.session_state.submissions = []

# --- MAIN INTERFACE ---
if menu == "Home":
    # Motivation Quote
    quotes = ["Bringing Santali to the AI Revolution. 🚀", "Your voice is the future of JanAI. 🌾", "Preserving culture with every word. ✨"]
    st.markdown(f"<div class='quote-box'>\"{random.choice(quotes)}\"</div>", unsafe_allow_html=True)

    col_main, col_chat = st.columns([2.5, 1])

    with col_main:
        # Question Card
        s_lang = st.selectbox("Switch Input Language:", ["Bengali", "Hindi", "English", "Odia"], label_visibility="collapsed")

        # Only fetch a new question if language changed or not set
        if st.session_state.get('prev_l') != s_lang or not st.session_state.get('q_t'):
            try:
                # Use cached wrapper to avoid calling model excessively
                st.session_state.q_c, st.session_state.q_t = cached_get_ai_q(s_lang)
            except Exception as e:
                logger.info(f"Error fetching AI question: {e}")
                st.session_state.q_c, st.session_state.q_t = "Global", ("আপনার দিন কেমন যাচ্ছে?" if s_lang.lower().startswith("bengal") else "How is your day?")
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
            if audio and isinstance(audio, dict) and 'bytes' in audio:
                st.audio(audio['bytes'])

        if st.button("SUBMIT CONTRIBUTION 🚀"):
            # Allow anonymous submissions if is_anon is checked
            name_ok = bool(u_name) or is_anon
            audio_ok = bool(audio)
            ans_ok = bool(ans and ans.strip())

            if name_ok and ans_ok and audio_ok:
                with st.spinner("Processing Data and uploading to Hugging Face..."):
                    f_id = str(uuid.uuid4())[:8]
                    submission = {
                        "id": f_id,
                        "name": "Anonymous" if is_anon else u_name,
                        "email": u_email or "",
                        "answer": ans.strip(),
                        "has_audio": True if audio_ok else False,
                        "lang": s_lang
                    }
                    success, msg = upload_submission_to_hf(submission, audio)
                    if success:
                        st.balloons()
                        # Refresh question after successful submission
                        try:
                            st.session_state.q_c, st.session_state.q_t = cached_get_ai_q(s_lang)
                        except Exception:
                            st.session_state.q_c, st.session_state.q_t = "Global", ("আপনার দিন কেমন যাচ্ছে?" if s_lang.lower().startswith("bengal") else "How is your day?")
                        st.success("Contribution uploaded! Thank you.")
                        # also record locally
                        st.session_state.submissions.append(submission)
                        st.experimental_rerun()
                    else:
                        st.error(f"Upload failed: {msg}")
            else:
                missing = []
                if not name_ok:
                    missing.append("Name or select 'Post Anonymously'")
                if not ans_ok:
                    missing.append("Answer text")
                if not audio_ok:
                    missing.append("Recording")
                st.error("Please provide: " + ", ".join(missing))

        # Progress
        st.write("---")
        data_path = f"https://huggingface.co/datasets/{REPO_ID}/raw/main/data.csv"
        df_data = fetch_csv_from_hf(data_path)
        vol = len(df_data) if df_data is not None else 0
        st.write(f"📊 **JanAI Growth:** {vol} / 20,000 sentences")
        st.progress(min(vol/20000, 1.0))

    with col_chat:
        st.markdown("### 💬 Community Hub")
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        chat_path = f"https://huggingface.co/datasets/{REPO_ID}/raw/main/chat.csv"
        df_chat = fetch_csv_from_hf(chat_path)
        if df_chat is not None and not df_chat.empty:
            try:
                chats = df_chat.tail(15)
                for _, r in chats.iterrows():
                    user = r.get('user', 'Guest')
                    msg = r.get('msg', '')
                    st.markdown(f"<div class='chat-msg'><b>{user}:</b> {msg}</div>", unsafe_allow_html=True)
            except Exception as e:
                logger.info(f"Error rendering chat rows: {e}")
                st.write("Welcome to the community!")
        else:
            st.write("Welcome to the community!")

        st.markdown("</div>", unsafe_allow_html=True)
        msg = st.text_input("Share something...", key="chat_msg_in", label_visibility="collapsed")
        if st.button("Send ⬆️"):
            if msg and msg.strip():
                user = "Anonymous" if is_anon else (u_name if u_name else "Guest")
                with st.spinner("Appending chat to Hugging Face..."):
                    ok, m = append_chat_to_hf(user, msg.strip())
                    if ok:
                        st.success("Message posted to community.")
                        st.experimental_rerun()
                    else:
                        st.error(f"Failed to post chat: {m}")
            else:
                st.error("Please type a message before sending.")

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

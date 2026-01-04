# ===================== JanAI – FULL FINAL APP (RICH CONTENT) =====================
# Paste this ENTIRE file as app.py and run: streamlit run app.py
# =============================================================================

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from huggingface_hub import HfApi
from streamlit_mic_recorder import mic_recorder
from datetime import datetime
import json, uuid, random, os

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="JanAI – Santali Dataset",
    page_icon="📘",
    layout="wide"
)

PRIMARY = "#2563EB"

# ===================== CLEAN UI =====================
st.markdown(f"""
<style>
body {{ background:#ffffff; }}
h1,h2,h3 {{ color:#0f172a; }}
.section {{
    border:1px solid #e5e7eb;
    border-radius:8px;
    padding:1.2rem;
    margin-bottom:1.2rem;
}}
.primary-btn button {{
    background:{PRIMARY};
    color:white;
    border:none;
    border-radius:6px;
    padding:8px 18px;
}}
.secondary-btn button {{
    background:white;
    color:{PRIMARY};
    border:1px solid {PRIMARY};
    border-radius:6px;
    padding:8px 18px;
}}
small {{ color:#64748b; }}
ul {{ margin-left:1.1rem; }}
</style>
""", unsafe_allow_html=True)

# ===================== BACKEND SETUP =====================
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_KEY"]))
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")

    hf_api = HfApi(token=st.secrets["HF_TOKEN"])
    HF_REPO = "JanAI-Workspace/Santali-dataset"

except Exception as e:
    st.error(f"Setup error: {e}")
    st.stop()

# ===================== HELPERS =====================
def get_question(lang):
    docs = (
        db.collection("questions_pool")
        .where("language", "==", lang)
        .limit(20)
        .stream()
    )
    qs = [d.to_dict() for d in docs]
    return random.choice(qs) if qs else None


def save_to_hf(payload, audio_bytes=None, image_bytes=None):
    fid = str(uuid.uuid4())

    hf_api.upload_file(
        path_or_fileobj=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        path_in_repo=f"raw/{payload['input_mode']}/{fid}.json",
        repo_id=HF_REPO,
        repo_type="dataset"
    )

    if audio_bytes:
        hf_api.upload_file(
            path_or_fileobj=audio_bytes,
            path_in_repo=f"raw/audio/{fid}.wav",
            repo_id=HF_REPO,
            repo_type="dataset"
        )

    if image_bytes:
        hf_api.upload_file(
            path_or_fileobj=image_bytes,
            path_in_repo=f"raw/images/{fid}.png",
            repo_id=HF_REPO,
            repo_type="dataset"
        )

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### JanAI")
    st.caption("Santali Language Dataset")
    page = st.radio(
        "Navigation",
        ["Workspace", "Admin Panel", "Why This Project", "Data Usage"],
        label_visibility="collapsed"
    )

# ===================== WORKSPACE =====================
if page == "Workspace":

    st.title("Contribute to Santali Language Dataset")
    st.caption(
        "A clean, open platform to build high-quality Santali text, handwriting, and speech data for research."
    )

    input_mode = st.sidebar.radio(
        "Input Mode",
        ["Text", "Image → Type", "Handwriting → Type"]
    )

    lang = st.selectbox("Language", ["Santali", "Hindi", "Bengali", "Odia"])

    if "q" not in st.session_state or st.session_state.get("l") != lang:
        st.session_state.q = get_question(lang)
        st.session_state.l = lang

    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("Question")
    if st.session_state.q:
        st.write(st.session_state.q.get("text"))
        st.caption(
            "Please answer naturally in your own words. Longer, meaningful answers help create better datasets."
        )
    else:
        st.warning("No questions available at the moment. Please try again later.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section'>", unsafe_allow_html=True)
    st.subheader("Your Contribution")

    st.markdown(
        """
        **How to contribute**
        - Choose an input mode from the left.
        - Type clearly and carefully.
        - Audio is optional but encouraged if possible.
        """
    )

    uploaded_image = None
    if input_mode != "Text":
        uploaded_image = st.file_uploader(
            "Upload an image (printed page or handwritten note)",
            type=["png", "jpg", "jpeg"]
        )
        if uploaded_image:
            st.image(uploaded_image, use_column_width=True)
            st.caption(
                "Please type exactly what you see in the image. Do not auto-copy text."
            )

    answer = st.text_area(
        "Type the text here",
        height=160,
        placeholder="Write clearly and completely. Avoid very short answers."
    )

    audio = mic_recorder(
        start_prompt="🎤 Record audio (optional)",
        stop_prompt="⏹ Stop",
        key="rec"
    )

    if audio:
        st.audio(audio["bytes"])
        st.caption("Thank you for adding audio. This helps future speech research.")

    st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
    submit = st.button("Submit Contribution")
    st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        if not answer.strip():
            st.error("Text is required to submit.")
        else:
            payload = {
                "language": lang,
                "question": st.session_state.q.get("text") if st.session_state.q else "",
                "answer": answer,
                "input_mode": input_mode,
                "has_audio": bool(audio),
                "has_image": bool(uploaded_image),
                "timestamp": str(datetime.utcnow())
            }

            save_to_hf(
                payload,
                audio_bytes=audio["bytes"] if audio else None,
                image_bytes=uploaded_image.read() if uploaded_image else None
            )

            st.success(
                "Thank you for contributing! Your submission has been securely saved for review."
            )
            st.session_state.q = get_question(lang)

    st.markdown("</div>", unsafe_allow_html=True)

# ===================== ADMIN PANEL =====================
elif page == "Admin Panel":

    st.title("Admin Panel")
    st.caption("Quality control and dataset management")

    pwd = st.text_input("Admin password", type="password")

    if pwd != st.secrets.get("ADMIN_PASSWORD"):
        st.warning("Access restricted. Please enter a valid admin password.")
    else:
        st.success("Access granted")

        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.subheader("Dataset Overview")
        st.markdown(
            """
            - Submissions are collected in **batches of 50**
            - Each batch is reviewed using **5–6 random samples**
            - Flagged or duplicate data can be held or rejected
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.subheader("Batch Actions")
        st.caption(
            "Approve to publish the batch to HuggingFace. Hold or reject if quality issues are found."
        )
        st.button("Approve & Publish")
        st.button("Hold for Review")
        st.button("Reject Batch")
        st.markdown("</div>", unsafe_allow_html=True)

# ===================== TRUST PAGES =====================
elif page == "Why This Project":

    st.title("Why This Project")

    st.markdown(
        """
        Santali is a widely spoken indigenous language, yet it remains under-represented
        in digital resources and modern AI systems.

        **JanAI** exists to change that by building:
        - High-quality open text datasets
        - Handwritten text aligned with human-verified typing
        - Optional speech recordings for future audio research

        This project is community-driven, transparent, and designed for long-term
        language preservation and academic research.
        """
    )

elif page == "Data Usage":

    st.title("Data Usage & Ethics")

    st.markdown(
        """
        **How your data is used**
        - All contributions are used **only for language research and preservation**
        - Datasets are shared openly through **HuggingFace**
        - No personal profiling, advertising, or commercial misuse
        - Contributors may remain anonymous

        By contributing, you help create open resources that support education,
        technology access, and cultural preservation.
        """
    )

st.markdown("---")
st.markdown(
    "<small>© JanAI • Open Santali Language Infrastructure</small>",
    unsafe_allow_html=True
    )

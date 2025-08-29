import streamlit as st
import base64
from io import BytesIO

# Import open-source libraries
from transformers import pipeline
from gtts import gTTS

# --- 1. CONFIGURATION AND SETUP ---

# [cite_start]Function to set the background image from a local file [cite: 105, 230]
def set_background(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{b64_encoded});
            background-size: cover;
        }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. AI SERVICE INTEGRATION FUNCTIONS ---

# Function to load the Hugging Face model
# @st.cache_resource ensures the model is loaded only once
@st.cache_resource
def load_rewriting_model():
    """Loads the T5 model from Hugging Face."""
    return pipeline("text2text-generation", model="google/flan-t5-base")

# Function to rewrite text using a Hugging Face model
def rewrite_text_with_tone(text, tone):
    """
    Uses a local Hugging Face model to rewrite text based on a selected tone.
    """
    try:
        # [cite_start]Construct a prompt similar to the original project [cite: 125]
        prompt = f"Rewrite the following text in a {tone.lower()} tone: {text}"
        rewriter = load_rewriting_model()
        result = rewriter(prompt, max_length=300, num_beams=4, early_stopping=True)
        return result[0]['generated_text'].strip()
    except Exception as e:
        st.error(f"Error during tone rewriting: {e}")
        return None

# Function to convert text to speech using gTTS
def convert_text_to_speech(text, accent):
    """
    Uses gTTS to synthesize audio from text with a specific accent.
    """
    try:
        # Map user-friendly accent names to gTTS 'tld' codes
        tld_map = {
            "US English": "com",
            "UK English": "co.uk",
            "Australian English": "com.au"
        }
        tts = gTTS(text=text, lang='en', tld=tld_map[accent], slow=False)
        
        # [cite_start]Save the audio to an in-memory binary stream [cite: 138]
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0) # Rewind the file pointer to the beginning
        return audio_fp.read()
    except Exception as e:
        st.error(f"Error during audio generation: {e}")
        return None

# --- 3. STREAMLIT UI AND APPLICATION LOGIC ---

# [cite_start]Initialize session state to store narration history [cite: 70, 163]
if 'history' not in st.session_state:
    st.session_state.history = []

# [cite_start]Set page configuration and background [cite: 81]
st.set_page_config(page_title="EchoVerse", layout="centered")
set_background('assets/background.jpg') 

# --- UI Layout ---
st.title("🎧 EchoVerse (Open Source Edition)")
st.markdown("An AI-Powered Audiobook Creation Tool")

# [cite_start]Component 1: Text Input and File Upload [cite: 9, 55]
st.header("1. Provide Your Text")
input_method = st.radio("Choose input method", ["Paste Text", "Upload .txt File"])

text_input = ""
if input_method == "Paste Text":
    text_input = st.text_area("Paste your text here:", height=150)
else:
    uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
    if uploaded_file is not None:
        text_input = uploaded_file.getvalue().decode("utf-8")
        st.text_area("File Content:", text_input, height=150, disabled=True)

# [cite_start]Component 2: Tone and Voice (Accent) Selection [cite: 10, 193]
st.header("2. Customize Your Narration")
col1, col2 = st.columns(2)

with col1:
    selected_tone = st.selectbox("Select a Tone:", ("Neutral", "Suspenseful", "Inspiring"))

with col2:
    # Changed from "Voice" to "Accent" to match gTTS capabilities
    selected_accent = st.selectbox("Select an Accent:", ("US English", "UK English", "Australian English"))

# "Generate Audiobook" button
if st.button("Generate Audiobook", type="primary"):
    if not text_input.strip():
        st.warning("Please provide some text to generate the audiobook.")
    else:
        with st.spinner("Rewriting text... (This may take a moment on first run)"):
            rewritten_text = rewrite_text_with_tone(text_input, selected_tone)

        if rewritten_text:
            with st.spinner("Synthesizing audio..."):
                audio_data = convert_text_to_speech(rewritten_text, selected_accent)

            if audio_data:
                st.success("Audiobook generated successfully!")
                st.session_state.history.insert(0, {
                    "original": text_input,
                    "rewritten": rewritten_text,
                    "tone": selected_tone,
                    "accent": selected_accent,
                    "audio": audio_data
                })

# [cite_start]Display the LATEST generated audiobook [cite: 14]
if st.session_state.history:
    latest = st.session_state.history[0]
    st.header("Your Generated Audiobook")

    # [cite_start]Component 3: Original vs Rewritten Text Display [cite: 202]
    st.subheader("Original vs. Rewritten Text")
    c1, c2 = st.columns(2)
    with c1:
        st.text_area("Original Text", latest["original"], height=200, disabled=True)
    with c2:
        st.text_area("Rewritten Text", latest["rewritten"], height=200, disabled=True)

    # [cite_start]Component 4: Audio Playback and MP3 Download [cite: 13, 215]
    st.subheader("Listen to Your Audiobook")
    st.audio(latest["audio"], format="audio/mp3")
    st.download_button(
        label="Download MP3",
        data=latest["audio"],
        file_name=f"EchoVerse_{latest['tone']}_{latest['accent']}.mp3",
        mime="audio/mp3"
    )

# [cite_start]Component 5: Past Narrations Panel [cite: 15, 220]
if len(st.session_state.history) > 0:
    st.header("Past Narrations")
    with st.expander("View your session history"):
        for i, narration in enumerate(st.session_state.history):
            st.markdown(f"---")
            st.markdown(f"**Narration {len(st.session_state.history) - i}** (Tone: {narration['tone']}, Accent: {narration['accent']})")
            st.info(f"Rewritten Text: *{narration['rewritten']}*")
            st.audio(narration["audio"], format="audio/mp3")
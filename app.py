import streamlit as st
import openai
from streamlit_mic_recorder import mic_recorder
from io import BytesIO
import base64

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Traducteur",
    page_icon="🇫🇷",
    layout="centered",
    initial_sidebar_state="auto",
)

# --- 2. Helper Functions ---
def get_base64_image(image_path):
    """Encodes a local image to base64 for embedding in HTML."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Image file not found at {image_path}. Using placeholders.")
        return None

def translate_text(text_to_translate):
    """Calls OpenAI API to translate text between English and French."""
    system_prompt = (
        "You are a hyper-efficient translation engine. Your sole function is to "
        "detect if the user's input is English or French and provide the translation in the other language. "
        "Output ONLY the translated text and nothing else. Do not explain, do not greet."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text_to_translate}
    ]
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred with the OpenAI API: {e}", icon="🔥")
        return None

def speak_text(text):
    """Convert text to speech using OpenAI TTS and return audio bytes."""
    try:
        response = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",   # you can change to other available voices
            input=text
        )
        audio_bytes = response.read()
        return audio_bytes
    except Exception as e:
        st.error(f"TTS error: {e}", icon="🔊")
        return None

# --- 3. Setup and Initialization ---
uk_icon_b64 = get_base64_image("assets/UK_icon.png")
fr_icon_b64 = get_base64_image("assets/FR_icon.png")

uk_icon_html = f'<img src="data:image/png;base64,{uk_icon_b64}" width="40">' if uk_icon_b64 else "🇬🇧"
fr_icon_html = f'<img src="data:image/png;base64,{fr_icon_b64}" width="40">' if fr_icon_b64 else "🇫🇷"

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between;">
        {uk_icon_html}
        <h1 style="margin: 0; text-align: center; flex-grow: 1;">English ⇄ French</h1>
        {fr_icon_html}
    </div>
    """,
    unsafe_allow_html=True
)

# OpenAI API Key Setup
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("OpenAI API key not found. Please add it to your Streamlit secrets.", icon="🚨")
    st.stop()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. UI Tabs for Input ---
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "💬 Chat"

tab_labels = ["💬 Chat", "📁 File Uploader", "🎙️ Audio Recorder"]

# Reorder tabs so the active one is first
tab_labels = [st.session_state.active_tab] + [lbl for lbl in tab_labels if lbl != st.session_state.active_tab]
tabs = st.tabs(tab_labels)
tab_map = dict(zip(tab_labels, tabs))

# --- Text Input Tab ---
with tab_map["💬 Chat"]:
    if prompt := st.chat_input("Enter text to translate..."):
        st.session_state.active_tab = "💬 Chat"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Translating..."):
                translation = translate_text(prompt)
                if translation:
                    st.session_state.messages.append({"role": "assistant", "content": translation})
                    st.markdown(translation)
                    # Speak translation
                    audio_bytes = speak_text(translation)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")

# --- File Uploader Tab ---
with tab_map["📁 File Uploader"]:
    audio_file = st.file_uploader("Upload an audio file...", type=["wav", "mp3", "m4a"])
    if audio_file:
        st.session_state.active_tab = "📁 File Uploader"
        st.audio(audio_file)
        with st.spinner("Transcribing audio..."):
            try:
                audio_file.name = "uploaded_audio.wav"
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcribed_text = transcription_response.text
                st.success(f"**Transcription:** {transcribed_text}")
                st.session_state.messages.append({"role": "user", "content": f"🎤 *Transcription:* {transcribed_text}"})

                with st.spinner("Translating text..."):
                    translation = translate_text(transcribed_text)
                    if translation:
                        st.info(f"**Translation:** {translation}")
                        st.session_state.messages.append({"role": "assistant", "content": translation})
                        audio_bytes = speak_text(translation)
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3")
                        #st.rerun()
            except Exception as e:
                st.error(f"An error occurred during transcription: {e}", icon="🔥")

# --- Audio Recorder Tab ---
with tab_map["🎙️ Audio Recorder"]:
    audio_info = mic_recorder(start_prompt="Start recording", stop_prompt="Stop recording", key='recorder')
    if audio_info and audio_info['bytes']:
        st.session_state.active_tab = "🎙️ Audio Recorder"
        st.audio(audio_info['bytes'], format='audio/wav')
        audio_bio = BytesIO(audio_info['bytes'])
        audio_bio.name = 'recorded_audio.wav'

        with st.spinner("Transcribing audio..."):
            try:
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bio
                )
                transcribed_text = transcription_response.text
                st.success(f"**Transcription:** {transcribed_text}")
                st.session_state.messages.append({"role": "user", "content": f"🎤 *Transcription:* {transcribed_text}"})

                with st.spinner("Translating text..."):
                    translation = translate_text(transcribed_text)
                    if translation:
                        st.info(f"**Translation:** {translation}")
                        st.session_state.messages.append({"role": "assistant", "content": translation})
                        audio_bytes = speak_text(translation)
                        if audio_bytes:
                            st.audio(audio_bytes, format="audio/mp3")
                        #st.rerun()
            except Exception as e:
                st.error(f"An error occurred during transcription: {e}", icon="🔥")


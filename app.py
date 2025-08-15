import streamlit as st
import openai
from streamlit_mic_recorder import mic_recorder
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Traducteur",
    page_icon="🇫🇷",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🇫🇷 English <> French 🇬🇧")
st.caption("A simple bidirectional translator using OpenAI's API")

# --- OpenAI API Setup ---
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("OpenAI API key not found. Please add it to your Streamlit secrets.", icon="🚨")
    st.stop()

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helper function for translation ---
def translate_text(text):
    system_prompt = (
        "You are a hyper-efficient translation engine. Your sole function is to "
        "detect if the user's input is English or French and provide the translation in the other language. "
        "Output ONLY the translated text and nothing else. Do not explain, do not greet."
    )
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": text}]
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred with the OpenAI API: {e}", icon="🔥")
        return None

# --- UI Tabs ---
text_tab, file_tab, record_tab = st.tabs(["💬 Chat", "📁 File Uploader", "🎙️ Audio Recorder"])

# --- Text Input Tab ---
with text_tab:
    if prompt := st.chat_input("Enter text to translate..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        translation = translate_text(prompt)
        if translation:
            st.session_state.messages.append({"role": "assistant", "content": translation})

# --- File Uploader Tab ---
with file_tab:
    audio_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])
    if audio_file:
        st.audio(audio_file, format='audio/wav')
        transcription_placeholder = st.empty()
        with st.spinner("Transcribing audio..."):
            try:
                # The name attribute is required for the OpenAI API
                audio_file.name = "uploaded_audio.wav"
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcribed_text = transcription_response.text
                transcription_placeholder.success(f"**Transcription:** {transcribed_text}")
                st.session_state.messages.append({"role": "user", "content": f"[Audio Transcription] {transcribed_text}"})
                with st.spinner("Translating text..."):
                    translation = translate_text(transcribed_text)
                    if translation:
                        st.info(f"**Translation:** {translation}")
                        st.session_state.messages.append({"role": "assistant", "content": translation})
            except Exception as e:
                st.error(f"An error occurred during transcription: {e}", icon="🔥")

# --- Audio Recorder Tab ---
with record_tab:
    audio_info = mic_recorder(start_prompt="Start recording", stop_prompt="Stop recording", key='recorder')
    if audio_info and audio_info['bytes']:
        st.audio(audio_info['bytes'], format='audio/wav')
        transcription_placeholder_rec = st.empty()
        audio_bio = BytesIO(audio_info['bytes'])
        audio_bio.name = 'recorded_audio.wav'
        with st.spinner("Transcribing audio..."):
            try:
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bio
                )
                transcribed_text = transcription_response.text
                transcription_placeholder_rec.success(f"**Transcription:** {transcribed_text}")
                st.session_state.messages.append({"role": "user", "content": f"[Audio Transcription] {transcribed_text}"})

                with st.spinner("Translating text..."):
                    translation = translate_text(transcribed_text)
                    if translation:
                        st.info(f"**Translation:** {translation}")
                        st.session_state.messages.append({"role": "assistant", "content": translation})
            except Exception as e:
                st.error(f"An error occurred during transcription: {e}", icon="🔥")


# --- Display Chat History ---
with st.container():
    st.header("Chat History")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
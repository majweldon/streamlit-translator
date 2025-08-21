import streamlit as st
import openai
from streamlit_mic_recorder import mic_recorder
from io import BytesIO
import base64

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Traducteur",
    page_icon="🇫🇷", # Using an emoji as an icon is simpler if the asset path is an issue
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

# --- 3. Setup and Initialization ---

# Custom Title with Icons
uk_icon_b64 = get_base64_image("assets/UK_icon.png")
fr_icon_b64 = get_base64_image("assets/FR_icon.png")

# Fallback in case images aren't found
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

# --- 4. Display Chat History (This runs on every interaction) ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. UI Tabs for Input ---
text_tab, file_tab, record_tab = st.tabs(["💬 Chat", "📁 File Uploader", "🎙️ Audio Recorder"])

# --- Text Input Tab ---
with text_tab:
    if prompt := st.chat_input("Enter text to translate..."):
        # Add user message to state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get and display assistant's response
        with st.chat_message("assistant"):
            with st.spinner("Translating..."):
                translation = translate_text(prompt)
                if translation:
                    st.session_state.messages.append({"role": "assistant", "content": translation})
                    st.markdown(translation)

# --- File Uploader Tab ---
with file_tab:
    audio_file = st.file_uploader("Upload an audio file to transcribe and translate", type=["wav", "mp3", "m4a"])
    if audio_file:
        st.audio(audio_file)
        
        with st.spinner("Transcribing audio..."):
            try:
                # The file needs a name for the API call
                audio_file.name = "uploaded_audio.wav"
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcribed_text = transcription_response.text
                st.success(f"**Transcription:** {transcribed_text}")
                
                # Add transcription to history as the "user" message
                st.session_state.messages.append({"role": "user", "content": f"🎤 *Transcription:* {transcribed_text}"})
                
                with st.spinner("Translating text..."):
                    translation = translate_text(transcribed_text)
                    if translation:
                        st.info(f"**Translation:** {translation}")
                        # Add translation to history as the "assistant" message
                        st.session_state.messages.append({"role": "assistant", "content": translation})
                        # Use st.rerun() to immediately update the main chat display above
                        st.rerun()

            except Exception as e:
                st.error(f"An error occurred during transcription: {e}", icon="🔥")

# --- Audio Recorder Tab ---
with record_tab:
    audio_info = mic_recorder(start_prompt="Start recording", stop_prompt="Stop recording", key='recorder')

    if audio_info and audio_info['bytes']:
        st.audio(audio_info['bytes'], format='audio/wav')
        audio_bio = BytesIO(audio_info['bytes'])
        audio_bio.name = 'recorded_audio.wav' # Give the in-memory file a name

        with st.spinner("Transcribing audio..."):
            try:
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bio
                )
                transcribed_text = transcription_response.text
                st.success(f"**Transcription:** {transcribed_text}")
                
                # Add transcription to history as the "user" message
                st.session_state.messages.append({"role": "user", "content": f"🎤 *Transcription:* {transcribed_text}"})

                with st.spinner("Translating text..."):
                    translation = translate_text(transcribed_text)
                    if translation:
                        st.info(f"**Translation:** {translation}")
                        # Add translation to history as the "assistant" message
                        st.session_state.messages.append({"role": "assistant", "content": translation})
                        # Use st.rerun() to immediately update the main chat display above
                        st.rerun()

            except Exception as e:
                st.error(f"An error occurred during transcription: {e}", icon="🔥")
import streamlit as st
import openai
import base64

# --- Page Configuration ---
st.set_page_config(
    page_title="Traducteur",
    page_icon="assets/FR_icon.png",
    layout="centered",
    initial_sidebar_state="auto",
)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{encoded}"

uk_icon = get_base64_image("assets/UK_icon.png")
fr_icon = get_base64_image("assets/FR_icon.png")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <img src="{uk_icon}" width="40">
        <h1 style="margin: 0; text-align: center; flex-grow: 1;">English ⇄ French</h1>
        <img src="{fr_icon}" width="40">
    </div>
    """,
    unsafe_allow_html=True
)


# --- OpenAI API Setup ---
# Attempt to get the API key from Streamlit secrets
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("OpenAI API key not found. Please add it to your Streamlit secrets.", icon="🚨")
    st.stop()


# --- Session State Initialization ---
# This is crucial for keeping the chat history persistent
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat History ---
# Loop through the existing messages in the session state and display them
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input and Logic ---
if prompt := st.chat_input("Enter text to translate..."):
    # 1. Add user's message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Prepare the API call
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
    # And replace it with this new one
    system_prompt = (
        "You are a hyper-efficient translation engine. Your sole function is to "
        "detect if the user's input is English or French and provide the translation in the other language. "
        "Output ONLY the translated text and nothing else. Do not explain, do not greet."
    )

    # We create a new list for the API call to include the system prompt
    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    # 3. Call the OpenAI API
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
        )
        full_response = response.choices[0].message.content
        message_placeholder.markdown(full_response)
    except Exception as e:
        st.error(f"An error occurred with the OpenAI API: {e}", icon="🔥")
        st.stop()
    
    # 4. Add assistant's response to session state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
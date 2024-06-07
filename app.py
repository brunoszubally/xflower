import pickle
from pathlib import Path
from dotenv import load_dotenv
import os
import streamlit as st
from openai import OpenAI
import streamlit_authenticator as stauth

class Config:
    """Singleton configuration class for environment variables."""
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    ASSISTANT_KEY = os.getenv("ASSISTANT_KEY")
    PAGE_TITLE = os.getenv("PAGE_TITLE")
    WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE")
    INSTRUCTIONS = os.getenv("INSTRUCTIONS")
    USER_PROMPT = os.getenv("USER_PROMPT")
    BEGIN_MESSAGE = os.getenv("BEGIN_MESSAGE")
    EXIT_MESSAGE = os.getenv("EXIT_MESSAGE")
    START_CHAT_BUTTON = os.getenv("START_CHAT_BUTTON")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL")
    DISCLAIMER = os.getenv("DISCLAIMER")
    LOGO = os.getenv("LOGO")


def initialize_openai_client():
    """Initializes and returns the OpenAI client along with the assistant object."""
    client = OpenAI(api_key=Config.API_KEY)
    assistant = client.beta.assistants.retrieve(Config.ASSISTANT_KEY)
    return client, assistant

def setup_streamlit_ui():
    """Configures Streamlit's page and displays initial UI components."""
    st.set_page_config(page_title=Config.PAGE_TITLE, page_icon=":speech_balloon:")
    apply_custom_css()
    if os.path.isfile(Config.LOGO):
        st.sidebar.image(Config.LOGO, use_column_width=True)  # Use full width for better resolution
    st.markdown("<h1 style='font-size:30px; font-weight:500;'>Miben segíthetek ma?</h1>", unsafe_allow_html=True)

def apply_custom_css():
    """Applies custom CSS to hide default Streamlit elements and adjust the layout."""
    custom_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700&display=swap');

            * {
                font-family: 'Montserrat', sans-serif;
            }

            .reportview-container {margin-top: -2em;}
            #MainMenu, header {visibility: hidden;}
            footer {visibility: hidden;}

            /* Custom style for header */
            h1 {
                font-family: 'Montserrat', sans-serif;
                font-weight: 500;
                font-size: 30px;
            }

            /* Style for input prompts */
            input, textarea, select, button {
                font-family: 'Montserrat', sans-serif;
            }
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def display_markdown_content(file_path):
    """Reads and displays markdown content from a specified file."""
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        st.markdown(content, unsafe_allow_html=True)

def initialize_chat_variables():
    """Initializes necessary chat variables in Streamlit's session state."""
    defaults = {"start_chat": False, "thread_id": None, "messages": []}
    for key, default in defaults.items():
        st.session_state.setdefault(key, default)

def handle_chat_interaction(client, assistant):
    """Manages user interactions and chat logic."""
    if 'start_chat' in st.session_state and st.session_state.start_chat:  
        display_chat_messages()
        user_input = st.chat_input(Config.USER_PROMPT)
        if user_input:
            process_and_display_chat_interaction(user_input, client, assistant)
    else:
        st.write(Config.BEGIN_MESSAGE)
      
def start_new_chat_session(client: OpenAI):
    """Begins a new chat session by creating a new thread."""
    st.session_state.start_chat = True
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []  # Clear previous messages
    st.session_state.start_chat = True  # Ensure chat is marked as started

def reset_chat_session():
    """Resets the chat session to its initial state."""
    st.session_state["messages"] = []
    st.session_state["start_chat"] = False
    st.session_state["thread_id"] = None

def display_chat_messages():
    """Displays all chat messages stored in the session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_and_display_chat_interaction(user_input, client: OpenAI, assistant):
    """Processes the user input, fetches the assistant's response, and displays both in the chat."""
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    if st.session_state.thread_id is None:
        st.error("Thread ID is None. Starting a new chat session.")
        start_new_chat_session(client)
        return

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=user_input
    )

    with client.beta.threads.runs.create_and_stream(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant.id,
        model=Config.OPENAI_MODEL,
        instructions=Config.INSTRUCTIONS,
        # event_handler=EventHandler(streamlit),
    ) as stream:
        with st.chat_message("assistant"):
            response = st.write_stream(stream.text_deltas)
            stream.until_done()

    st.session_state.messages.append({"role": "assistant", "content": response})

# Main
if __name__ == "__main__":
    client, assistant = initialize_openai_client()
    setup_streamlit_ui()

    # --- USER AUTHENTICATION ---
    names = ["Peter Parker", "Rebecca Miller"]
    usernames = ["bruno", "zsolt"]

    # load hashed passwords
    file_path = Path(__file__).parent / "hashed_pw.pkl"
    with file_path.open("rb") as file:
        hashed_passwords = pickle.load(file)

    credentials = {
        "usernames": {
            usernames[0]: {"name": names[0], "password": hashed_passwords[0]},
            usernames[1]: {"name": names[1], "password": hashed_passwords[1]},
        }
    }

    authenticator = stauth.Authenticate(
        credentials,
        "flowergpt",
        "abcdef",
        cookie_expiry_days=30
    )

    # Update the login method to the latest API
    name, authentication_status, username = authenticator.login('main', fields={'Form name': 'Belépés', 'Username': 'Felhasználónév',
        'Password': 'Jelszó',
        'Login': 'Belépés'})

    if authentication_status == False:
        st.error("Username/password is incorrect")

    if authentication_status == None:
        st.warning("Írja be a felhasználónevét és jelszavát!")

    if authentication_status:
        st.sidebar.title(f"Üdvözlünk az xFLOWer AI Tudásbázisában!")
        authenticator.logout("Kilépés", "sidebar")
        initialize_chat_variables()
        start_new_chat_session(client)  # Ensure a new chat session starts
        handle_chat_interaction(client, assistant)

import streamlit as st
from llm.graph.workflow import get_initial_state, run_single_turn
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv() # Call load_dotenv at the very beginning

# IMPORTANT: Ensure your .env file is in the project root directory
# and contains ANTHROPIC_API_KEY=YOUR_API_KEY


st.markdown(
    """
    <style>
    /* Main title */
    h1 {
        font-size: 64px !important;
    }

    /* Sidebar elements */
    .st-emotion-cache-vk33as, .st-emotion-cache-vk33as > div, .st-emotion-cache-vk33as > div > label, .st-emotion-cache-vk33as > div > p { /* Targeting the sidebar radio buttons container and its children */
        font-size: 18px !important;
    }
    .st-emotion-cache-vk33as > h2 { /* Targeting st.sidebar.title */
        font-size: 14px !important;
    }

    /* General body font size (can be adjusted later if needed) */
    body, p, [class*="st-emotion-cache"] {
        font-size: 20px; /* A reasonable default for general text */
    }

    /* Chat messages - can be refined */
    .st-chat-message p {
        font-size: 20px !important; /* Adjust chat message font size */
    }

    /* Removed chat history container border and flexible height styling */

    </style>
    """,
    unsafe_allow_html=True
)

st.title("🛡️ Voice Guardian")

# st.write("Welcome to Voice Guardian! This application allows you to chat with a large language model (LLM) and keep track of your conversation history.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Chatting", "History"])

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if page == "Chatting":
    st.subheader("Chat with the LLM")

    # Initialize LLM state and get welcome message on first run
    if "llm_state" not in st.session_state:
        initial_state = get_initial_state()
        first_turn_state = run_single_turn(initial_state)
        st.session_state.llm_state = first_turn_state
        
        # Extract messages and update session state
        llm_messages = first_turn_state.get("messages", [])
        st.session_state.messages = []
        for msg in llm_messages:
            role = "assistant" if msg.type == "ai" else "user"
            st.session_state.messages.append({"role": role, "content": msg.content})

    # Display chat messages from session state
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Say something"):
        # Add user message to chat history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get the current LLM state
        current_state = st.session_state.llm_state
        
        # Run a turn with the user's input
        new_state = run_single_turn(current_state, user_input=prompt)
        
        # Store the updated LLM state
        st.session_state.llm_state = new_state
        
        # Extract the new assistant message
        all_messages = new_state.get("messages", [])
        last_message = all_messages[-1] if all_messages else None
        
        if last_message and last_message.type == "ai":
            response = last_message.content
            # Add assistant response to chat history and display it
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

elif page == "History":
    st.subheader("Conversation History")
    st.write("This page will display your past conversations.")
    st.write("Current implementation is a placeholder. Future development will include loading and viewing past chat logs.")
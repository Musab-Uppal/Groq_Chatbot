import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv
from memory_manager import MemoryManager
from streamlit_cookies_manager import EncryptedCookieManager
import uuid
# Load environment
load_dotenv()

# Initialize clients
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Page config
st.set_page_config(
    page_title="AI Chat with Memory",
    page_icon="🧠",
    layout="wide"
)
cookies = EncryptedCookieManager(
    prefix="ai_chatbot",
    password=os.getenv("COOKIE_SECRET", "dev-secret")
)
if not cookies.ready():
    st.stop()
# Get or create user_id
if "user_id" not in cookies:
    cookies["user_id"] = str(uuid.uuid4())
    cookies.save()
user_id = cookies["user_id"]
if "user_id" not in st.session_state:
    st.session_state.user_id = user_id

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = MemoryManager(st.session_state.user_id)

# UI Header
st.title("🤖 Smart Chatbot with Memory")

# Sidebar
with st.sidebar:
    st.header("Settings")

   

    if st.button("Clear Memory & Chat History"):
        st.session_state.memory_manager.delete_user_memories()
        st.session_state.chat_history = []
        st.rerun()

    model = "llama-3.3-70b-versatile"

    st.divider()
# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to chat about?"):
    # Add user message to chat
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.chat_history.append(
        {"role": "user", "content": prompt}
    )

    # STEP 1: Get relevant memories from Mem0
    with st.spinner("🔍 Searching memories..."):
        relevant_memories = (
            st.session_state.memory_manager.get_relevant_memories(prompt)
        )

    # STEP 2: Build context with memories
    system_prompt = """
    You are a helpful assistant.
    Use the user's saved factual memory when relevant.
    If memory is provided, treat it as true.
    """

    if relevant_memories:
        system_prompt += "\nKnown facts about the user:\n"
        for m in relevant_memories:
            system_prompt += f"- {m}\n"

    # STEP 3: Prepare messages for Groq
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add chat history (last 6 messages)
    for msg in st.session_state.chat_history[-6:]:
        messages.append(
            {"role": msg["role"], "content": msg["content"]}
        )

    # STEP 4: Get response from Groq
    with st.chat_message("assistant"):
        with st.spinner("💭 Thinking..."):
            try:
                response = groq.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )

                reply = response.choices[0].message.content
                st.markdown(reply)

                # Add to chat history
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": reply}
                )

                # Check if user shared a personal fact
                if any(
                    x in prompt.lower()
                    for x in ["i am", "i'm", "my name", "i live", "i like"]
                ):
                    st.session_state.memory_manager.store_user_fact(prompt)
                    st.toast("Saved to memory 🧠")

            except Exception as e:
                st.error(f"Error: {e}")

    

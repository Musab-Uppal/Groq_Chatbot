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
# Get or create user_id and user_name
if "user_id" not in cookies:
    cookies["user_id"] = str(uuid.uuid4())
    cookies.save()
if "user_name" not in cookies:
    cookies["user_name"] = ""
    cookies.save()
user_id = cookies["user_id"]
user_name = cookies["user_name"]
if "user_id" not in st.session_state:
    st.session_state.user_id = user_id
if "user_name" not in st.session_state:
    st.session_state.user_name = user_name

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Determine effective user_id for memory
effective_user_id = st.session_state.user_name if st.session_state.user_name else st.session_state.user_id

if "memory_manager" not in st.session_state or st.session_state.get("memory_user_id", "") != effective_user_id:
    st.session_state.memory_manager = MemoryManager(effective_user_id)
    st.session_state.memory_user_id = effective_user_id

# UI Header
st.title("🤖 Smart Chatbot with Memory")

# Sidebar
with st.sidebar:
    st.header("User Settings")
    user_name_input = st.text_input("Your Name (for personalized memory)", value=st.session_state.user_name, key="user_name_input")
    if user_name_input != st.session_state.user_name:
        cookies["user_name"] = user_name_input
        cookies.save()
        st.session_state.user_name = user_name_input
        st.rerun()
    
    st.header("Chat Settings")
    personality = st.selectbox(
        "Chatbot Personality",
        ["General", "Traveler", "Chef", "Psychologist"]
    )

    st.divider()

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
       # STEP 2: Build context with memories and personality

    personality_prompts = {
        "General": """
You are a helpful general-purpose assistant.
Answer any question normally.
""",
        "Traveler": """
You are a travel expert.
Only answer questions related to travel, destinations, culture, visas, food, safety, or itineraries.
If the user's question is NOT about travel, say:
"❌ This question is outside my travel expertise."
""",
        "Chef": """
You are a professional chef.
Only answer questions related to cooking, recipes, ingredients, food techniques, or cuisine.
If the user's question is NOT about food or cooking, say:
"❌ This question is outside my cooking expertise."
""",
        "Psychologist": """
You are a psychologist.
Only answer questions related to mental health, emotions, behavior, relationships, or self-improvement.
Do NOT give medical diagnoses.
If the user's question is NOT psychological in nature, say:
"❌ This question is outside my psychology expertise."
"""
    }

    system_prompt = personality_prompts.get(personality, personality_prompts["General"])

    system_prompt += """
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

    

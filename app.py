import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="Groq AI Chatbot",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .personality-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        font-weight: bold;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Available models from Groq
AVAILABLE_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct","llama-3.1-8b-instant",
 "qwen/qwen3-32b",
 
 "openai/gpt-oss-120b"
]

# Personality configurations with strict boundaries
PERSONALITIES = {
    "Math Teacher": {
        "system_prompt": """You are a Math Teacher. You ONLY answer questions related to mathematics, 
        calculations, algebra, geometry, calculus, statistics, and mathematical concepts. 
        
        STRICT RULES:
        1. ONLY respond to math-related questions
        2. If asked about non-math topics, politely decline and redirect to math
        3. Explain concepts clearly with examples
        4. Use mathematical notation when helpful
        
        Examples of allowed topics:
        - Algebra equations
        - Geometry proofs
        - Calculus problems
        - Statistics analysis
        - Mathematical theory
        
        Response to non-math: "I'm your Math Teacher! I specialize in mathematics. Please ask me about math problems, equations, or mathematical concepts!" """,
        "color": "#4CAF50",
        "icon": "📐"
    },
    "Doctor": {
        "system_prompt": """You are a Medical Doctor. You ONLY answer questions related to health, 
        medicine, symptoms, treatments, and medical advice (general information only).
        
        IMPORTANT DISCLAIMER: This is for informational purposes only. Not a substitute for professional medical advice.
        
        STRICT RULES:
        1. ONLY respond to health/medical questions
        2. Always include disclaimer about consulting real doctors
        3. Never diagnose specific conditions
        4. Provide general health information only
        
        Examples of allowed topics:
        - General health tips
        - Symptom explanations (general)
        - Medication information (general)
        - Lifestyle advice for health
        - Basic first aid
        
        Response to non-medical: "I'm a Doctor! I can only discuss health and medical topics. For non-medical questions, please select a different personality or consult the appropriate specialist." """,
        "color": "#2196F3",
        "icon": "🏥"
    },
    "Travel Guide": {
        "system_prompt": """You are a Travel Guide. You ONLY answer questions related to travel, 
        destinations, tourism, accommodations, transportation, and travel tips.
        
        STRICT RULES:
        1. ONLY respond to travel-related questions
        2. Provide practical travel advice
        3. Suggest destinations based on preferences
        4. Include safety tips when relevant
        
        Examples of allowed topics:
        - Destination recommendations
        - Travel planning
        - Cultural information
        - Packing tips
        - Local attractions
        
        Response to non-travel: "I'm your Travel Guide! I specialize in travel advice. Please ask me about destinations, itineraries, or travel tips!" """,
        "color": "#FF9800",
        "icon": "✈️"
    },
    "Chef": {
        "system_prompt": """You are a Professional Chef. You ONLY answer questions related to cooking, 
        recipes, ingredients, techniques, and culinary advice.
        
        STRICT RULES:
        1. ONLY respond to cooking/food questions
        2. Provide clear recipes and instructions
        3. Suggest ingredient substitutions
        4. Explain cooking techniques
        
        Examples of allowed topics:
        - Recipe instructions
        - Cooking methods
        - Ingredient information
        - Meal planning
        - Kitchen tips
        
        Response to non-cooking: "I'm a Chef! I only discuss cooking, recipes, and culinary topics. Please ask me about food preparation or recipes!" """,
        "color": "#F44336",
        "icon": "👨‍🍳"
    },
    "Tech Support": {
        "system_prompt": """You are a Tech Support Specialist. You ONLY answer questions related to 
        technology, software, hardware, troubleshooting, and technical issues.
        
        STRICT RULES:
        1. ONLY respond to technical questions
        2. Provide step-by-step troubleshooting
        3. Explain technical concepts simply
        4. Suggest solutions for common issues
        
        Examples of allowed topics:
        - Software problems
        - Hardware troubleshooting
        - Network issues
        - Device setup
        - Tech recommendations
        
        Response to non-tech: "I'm Tech Support! I can only help with technical issues and technology questions. For other topics, please select a different personality." """,
        "color": "#9C27B0",
        "icon": "💻"
    },
    "Psychologist": {
        "system_prompt": """You are a Psychologist. You ONLY answer questions related to mental health, 
        emotional well-being, coping strategies, and psychological concepts.
        
        IMPORTANT DISCLAIMER: This is for informational purposes only. Not a substitute for professional therapy or counseling.
        
        STRICT RULES:
        1. ONLY respond to mental health/psychology questions
        2. Always include disclaimer about consulting real therapists
        3. Never provide specific diagnoses
        4. Offer general advice on coping and well-being
        
        Examples of allowed topics:
        - Stress management
        - Emotional coping strategies
        - Psychological theories
        - Mental health tips
        - Self-care practices
        
        Response to non-psychology: "I'm a Psychologist! I specialize in mental health and psychology. Please ask me about emotional well-being or psychological concepts!" """,
        "color": "#E91E63",
        "icon": "🧠"
    }
}


# Initialize session state for chat memory
if "messages" not in st.session_state:
    st.session_state.messages = {}
if "current_personality" not in st.session_state:
    st.session_state.current_personality = "Math Teacher"
if "current_model" not in st.session_state:
    st.session_state.current_model = AVAILABLE_MODELS[0]


def get_conversation_key():
    """Create a unique key for the current conversation based on personality and model"""
    return f"{st.session_state.current_personality}_{st.session_state.current_model}"

def initialize_conversation():
    """Initialize or reset the conversation for current settings"""
    conversation_key = get_conversation_key()
    
    if conversation_key not in st.session_state.messages:
        # Initialize with system message for the selected personality
        personality_data = PERSONALITIES[st.session_state.current_personality]
        st.session_state.messages[conversation_key] = [
            {
                "role": "system",
                "content": personality_data["system_prompt"],
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    return st.session_state.messages[conversation_key]

def get_groq_response(user_input, conversation_history):
    """Get response from Groq API with better error handling"""
    try:
        # Prepare messages for API (excluding timestamp)
        api_messages = []
        for msg in conversation_history:
            # Only include role and content for API
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add user's new message
        api_messages.append({"role": "user", "content": user_input})
        
        # Debug: Show what's being sent to API
        print(f"Sending to API: {api_messages[-2:]}")  # Last 2 messages
        
        # Call Groq API
        response = client.chat.completions.create(
            model=st.session_state.current_model,
            messages=api_messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=True
        )
        
        # Debug: Show raw response
        print(f"Raw response: {response}")
        
        # Get the assistant's response
        if hasattr(response.choices[0].message, 'content'):
            assistant_response = response.choices[0].message.content
        else:
            assistant_response = str(response.choices[0].message)
        
        # Update conversation history with timestamps
        conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        conversation_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        return assistant_response
        
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        print(f"Error details: {str(e)}")
        return f"Sorry, I encountered an error: {str(e)}. Please check your API key and try again."

def main():
    # Header
    st.title("🤖 Groq AI Chatbot with Personalities")
    st.markdown("---")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        st.subheader("Select AI Model")
        selected_model = st.selectbox(
            "Choose a model:",
            AVAILABLE_MODELS,
            index=AVAILABLE_MODELS.index(st.session_state.current_model)
        )
        
        # Personality selection
        st.subheader("🎭 Choose Personality")
        selected_personality = st.selectbox(
            "Select chatbot personality:",
            list(PERSONALITIES.keys()),
            index=list(PERSONALITIES.keys()).index(st.session_state.current_personality)
        )
        
        # Display personality info
        if selected_personality in PERSONALITIES:
            personality_data = PERSONALITIES[selected_personality]
            st.markdown(f"""
            <div style="background-color:{personality_data['color']}20; padding:10px; border-radius:10px; border-left:4px solid {personality_data['color']};">
                <h4>{personality_data['icon']} {selected_personality}</h4>
                <p><small>Specializes in: {selected_personality.split()[-1].lower()}-related topics only</small></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            conversation_key = get_conversation_key()
            if conversation_key in st.session_state.messages:
                # Keep only system message
                st.session_state.messages[conversation_key] = [
                    msg for msg in st.session_state.messages[conversation_key] 
                    if msg["role"] == "system"
                ]
            st.rerun()
        
        # Info section
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This chatbot uses Groq's fast inference engine.
        
        **Features:**
        - Multiple AI models
        - Personality-enforced responses
        - Session memory per personality/model
        - Real-time responses
        
        **Note:** Each personality has strict boundaries and will only answer questions within its specialty.
        """)
    
    # Check if settings changed
    if (selected_model != st.session_state.current_model or 
        selected_personality != st.session_state.current_personality):
        st.session_state.current_model = selected_model
        st.session_state.current_personality = selected_personality
        st.rerun()
    
    # Initialize conversation for current settings
    conversation_history = initialize_conversation()
    
    # Display current settings
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Model:** {st.session_state.current_model}")
    with col2:
        personality_data = PERSONALITIES[st.session_state.current_personality]
        st.info(f"**Personality:** {personality_data['icon']} {st.session_state.current_personality}")
    
    st.markdown("---")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display only non-system messages
        for message in conversation_history:
            if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    # Chat input
    user_input = st.chat_input(f"Ask the {st.session_state.current_personality}...")
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner(f"{st.session_state.current_personality} is thinking..."):
                response = get_groq_response(user_input, conversation_history)
                st.markdown(response)
        
        # Rerun to update display
        st.rerun()
    
    # Display conversation statistics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        user_msgs = len([m for m in conversation_history if m["role"] == "user"])
        st.metric("User Messages", user_msgs)
    with col2:
        assistant_msgs = len([m for m in conversation_history if m["role"] == "assistant"])
        st.metric("AI Responses", assistant_msgs)
    with col3:
        total_tokens = sum(len(str(m["content"]).split()) for m in conversation_history)
        st.metric("Approx. Tokens", total_tokens)

if __name__ == "__main__":
    main()
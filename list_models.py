import os
from groq import Groq
from dotenv import load_dotenv

# Load your API key
load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

print("Fetching available models from Groq...")
try:
    models = client.models.list()
    print("\n✅ Models you have access to:")
    for model in models.data:
        print(f" - {model.id}")
except Exception as e:
    print(f"❌ Error: {e}")
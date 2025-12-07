import google.generativeai as genai
import os
from dotenv import load_dotenv

# Environment variables load karo
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY nahi mili .env file me.")
else:
    print(f"✅ Key Found: {api_key[:5]}...*****")
    
    try:
        genai.configure(api_key=api_key)
        print("\n🔍 Available Models for your Key:")
        
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
                found = True
        
        if not found:
            print("❌ Koi model nahi mila! API Key ki limits check karo.")
            
    except Exception as e:
        print(f"❌ Error connecting to Google AI: {e}")
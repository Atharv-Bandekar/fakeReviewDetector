import requests
import json
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# 🔴 CONFIGURATION
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = os.getenv('OPENROUTER_URL')

# 🚀 FREE MODEL LIST (Optimized for SPEED & RELIABILITY)
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",       # ⚡ FASTEST (Primary) - Great for short explanations
    "google/gemini-2.0-flash-lite-preview-02-05:free", # 🧠 SMART & FAST (Secondary)
    "microsoft/phi-3-mini-128k-instruct:free",     # ⚡ FAST BACKUP
    "mistralai/mistral-7b-instruct:free"           # 🛡️ RELIABLE FALLBACK
]

# 🧠 CACHING
@lru_cache(maxsize=100)
def get_cached_explanation(review_snippet, label, confidence):
    return generate_explanation_with_fallback(review_snippet, label, confidence)

import requests
import json
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# 🔴 CONFIGURATION
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 🚀 FREE MODEL LIST (Optimized for SPEED & RELIABILITY)
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",       # ⚡ FASTEST (Primary) - Great for short explanations
    "google/gemini-2.0-flash-lite-preview-02-05:free", # 🧠 SMART & FAST (Secondary)
    "microsoft/phi-3-mini-128k-instruct:free",     # ⚡ FAST BACKUP
    "mistralai/mistral-7b-instruct:free"           # 🛡️ RELIABLE FALLBACK
]

# 🧠 CACHING
@lru_cache(maxsize=100)
def get_cached_explanation(review_snippet, label, confidence):
    return generate_explanation_with_fallback(review_snippet, label, confidence)

def generate_explanation_with_fallback(review_text, label, confidence):
    """
    Tries multiple free models to generate a short, human-like explanation.
    """
    # 1. Human-Centric Prompting
    if label == "FAKE":
        prompt = (
            f"You are a helpful shopping assistant. This review is flagged as FAKE ({confidence:.0%} certainty). "
            "Explain why in 1 simple, conversational sentence. "
            "Point out what feels off (like it's too generic, repeats words, or sounds like an ad). "
            "Don't use bullet points. Speak naturally."
        )
    else:
        prompt = (
            f"You are a helpful shopping assistant. This review looks GENUINE ({confidence:.0%} certainty). "
            "Explain why in 1 simple, conversational sentence. "
            "Mention how the user gives specific details or balanced pros/cons that feel real. "
            "Don't use bullet points. Speak naturally."
        )

    # 2. Try Models in Loop
    for model in FREE_MODELS:
        print(f"🔄 Trying XAI with model: {model}...") 
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a concise, helpful assistant. You speak in plain English, avoiding jargon."}, # Added System Persona
                    {"role": "user", "content": f"{prompt}\n\nREVIEW:\n{review_text[:300]}"}
                ],
                "temperature": 0.8, # Increased creativity (0.7 -> 0.8) for more natural phrasing
                "max_tokens": 60,   # slightly more room for a sentence
            }
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "ReviewGuard"
            }

            response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=6)
            
            if response.status_code != 200:
                print(f"❌ Failed {model} | Code: {response.status_code}")
                continue
            
            return response.json()['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"⚠️ Exception on {model}: {e}")
            continue

    return "AI is busy right now, but this review shows clear signs of being " + ("fake." if label == "FAKE" else "real.")
def get_explanation(review_text, label, confidence):
    # Cache key: First 100 chars
    return get_cached_explanation(review_text[:100], label, confidence)

def get_explanation(review_text, label, confidence):
    # Cache key: First 100 chars
    return get_cached_explanation(review_text[:100], label, confidence)

if __name__ == "__main__":
    test_text = "I bought this and it broke immediately. Worst product ever."
    print("\nFINAL RESULT:", get_explanation(test_text, "FAKE", 0.99))
import requests
import json
import os
import random
from functools import lru_cache
from dotenv import load_dotenv
from textblob import TextBlob  # 📦 NEW LIBRARY

load_dotenv()

# 🔴 CONFIGURATION
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 🚀 FREE MODEL LIST
FREE_MODELS = [
    "meta-llama/llama-3.2-3b-instruct:free",      #  FASTEST (Primary)
    "google/gemini-2.0-flash-exp:free",           #  SMARTEST (Secondary)
    "google/gemma-3-12b-it:free",                 #  NEW & CAPABLE
    "mistralai/mistral-small-3.1-24b-instruct:free" #  RELIABLE BACKUP           
]

@lru_cache(maxsize=100)
def get_cached_explanation(review_snippet, label, confidence):
    return generate_explanation_with_fallback(review_snippet, label, confidence)

# 🧠 SMART LOCAL ENGINE (The "Lightweight Library" Solution)
def analyze_locally(text, label):
    """
    Uses TextBlob to generate a dynamic explanation based on actual text properties.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity         # -1.0 (Negative) to 1.0 (Positive)
    subjectivity = blob.sentiment.subjectivity # 0.0 (Objective) to 1.0 (Subjective)
    word_count = len(text.split())

    # --- FAKE REVIEW LOGIC ---
    if label == "FAKE":
        if polarity > 0.8:
            return f"This review is suspiciously enthusiastic ({int(polarity*100)}% positive) and lacks the balanced critique usually found in genuine feedback."
        elif subjectivity < 0.2:
            return "The writing style feels robotic and overly objective, lacking the personal emotional touch of a real user experience."
        elif word_count < 15:
            return "The review is extremely short and generic, making it difficult to verify as a genuine user experience."
        else:
            return "It uses generic praising language without mentioning specific scenarios or usage details typical of an owner."

    # --- REAL REVIEW LOGIC ---
    else:
        if 0.3 < subjectivity < 0.7:
            return "The review shows a natural balance of facts and personal feelings, which is a strong sign of authenticity."
        elif polarity < 0.5 and polarity > -0.5:
            return "The user provides a balanced perspective (neither purely glowing nor hateful), suggesting a real, unbiased experience."
        elif word_count > 50:
            return "The review contains specific details and depth that would be difficult for a bot to hallucinate convincingly."
        else:
            return "The writing style feels natural and consistent with a verified purchase."

def generate_explanation_with_fallback(review_text, label, confidence):
    """
    Tries AI models first. If they fail, uses TextBlob for local analysis.
    """
    # 1. AI Prompt
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

    # 2. Try Models
    for model in FREE_MODELS:
        print(f"🔄 Trying XAI with model: {model}...") 
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": f"You are a helpful assistant. {prompt}\n\nREVIEW:\n{review_text[:300]}"}],
                "temperature": 0.7, 
            }
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "ReviewGuard"
            }

            response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=8)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                if content: return content
            
        except Exception as e:
            print(f"⚠️ Exception on {model}: {e}")
            continue

    # 3. LOCAL FALLBACK (TextBlob)
    print("⚠️ AI models failed. Using TextBlob Local Analysis.")
    return analyze_locally(review_text, label)

def get_explanation(review_text, label, confidence):
    return get_cached_explanation(review_text[:100], label, confidence)

if __name__ == "__main__":
    test_text = "Best product ever! I love it so much. It is amazing and perfect in every way."
    print("\nFINAL RESULT:", get_explanation(test_text, "FAKE", 0.99))
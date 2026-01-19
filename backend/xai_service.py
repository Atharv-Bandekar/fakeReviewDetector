import requests
import json
import time
from functools import lru_cache

# 🔴 CONFIGURATION
OPENROUTER_API_KEY = "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"  # 
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# 🚀 FREE MODEL CASCADE (The "Relay Race")
# If the first one fails, we automatically switch to the next.
# 🚀 FREE MODEL LIST (Optimized for your findings)
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",           # FAST & SMART (Primary)
    "meta-llama/llama-3.3-70b-instruct:free",     # VERY SMART (Backup)
    "meta-llama/llama-3.2-3b-instruct:free",      # VERY FAST (Safety net)
    "mistralai/mistral-small-3.1-24b-instruct:free" # Final Resort
]

# 🧠 CACHING (The "Memory")
# Stores the last 100 explanations in RAM. 
# If a user clicks "Why?" on a review we've already seen, it costs 0 API calls.
@lru_cache(maxsize=100)
def get_cached_explanation(review_snippet, label, confidence):
    return generate_explanation_with_fallback(review_snippet, label, confidence)

def generate_explanation_with_fallback(review_text, label, confidence):
    """
    Tries multiple free models to generate a short explanation.
    """
    # 1. Define the Prompt
    if label == "FAKE":
        prompt = (
            f"Analyze this review flagged as FAKE ({confidence:.0%} confidence). "
            "Identify 2 specific flaws (e.g., generic praise, lack of detail, robotic tone). "
            "Keep it under 30 words."
        )
    else:
        prompt = (
            f"Analyze this review verified as GENUINE ({confidence:.0%} confidence). "
            "Identify 2 signs of authenticity (e.g., specific usage details, balanced pros/cons). "
            "Keep it under 30 words."
        )

    # 2. Try Models in Loop
    for model in FREE_MODELS:
        print(f"🔄 Trying XAI with model: {model}...") # DEBUG PRINT
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": f"{prompt}\n\nREVIEW:\n{review_text[:500]}"}
                ],
                # 'temperature' helps creativity, remove 'max_tokens' if it causes issues
            }
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "ReviewGuard"
            }

            response = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=10)
            
            # 3. DEBUGGING: Print the error if it fails
            if response.status_code != 200:
                print(f"❌ Failed {model} | Code: {response.status_code}")
                print(f"   Response: {response.text}") # <--- THIS TELLS US THE REASON
                continue
            
            # If success:
            return response.json()['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"⚠️ Exception on {model}: {e}")
            continue

    return "Could not generate explanation (Service Busy)."

# Wrapper function called by app.py
def get_explanation(review_text, label, confidence):
    # We use a snippet of the text for the cache key to save memory
    # (First 100 chars + label is usually unique enough for a session)
    return get_cached_explanation(review_text[:100], label, confidence)

# Test Block
if __name__ == "__main__":
    test_text = "I bought this and it broke immediately. Worst product ever."
    print("\nFINAL RESULT:", get_explanation(test_text, "FAKE", 0.99))
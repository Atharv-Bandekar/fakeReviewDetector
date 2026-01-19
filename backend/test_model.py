import os
# Force CPU mode to match your laptop
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from transformers import DebertaV2Tokenizer, TFDebertaV2ForSequenceClassification

# 1. SETUP PATHS
BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, 'model')

print(f"📂 Loading model from: {MODEL_DIR}")

try:
    # 2. LOAD MODEL (The DeBERTa Brain)
    tokenizer = DebertaV2Tokenizer.from_pretrained(MODEL_DIR)
    model = TFDebertaV2ForSequenceClassification.from_pretrained(MODEL_DIR)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("TIP: Did you rename 'spam_model' to 'spm.model'?")
    exit()

# 3. DEFINE TEST CASES
reviews = [
    "I absolutely love this product! It works exactly as described.",  # Likely Real
    "Excellent item. Fast shipping. A++++ seller. Highly recommend.",  # Likely Fake/Bot
    "The item arrived broken and the seller refused to refund me."     # Likely Real (Negative)
]

print("\n📊 --- THRESHOLD TEST ---")
print(f"{'REVIEW TEXT':<50} | {'REAL %':<8} | {'FAKE %':<8} | {'DECISION'}")
print("-" * 90)

for text in reviews:
    # Tokenize
    inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=128)
    
    # Predict
    logits = model(inputs).logits
    probs = tf.nn.softmax(logits, axis=1).numpy()[0]
    
    real_score = probs[0]
    fake_score = probs[1]
    
    # Apply Logic (0.60 Threshold)
    if fake_score > 0.60:
        decision = "FAKE 🔴"
    elif real_score > 0.60:
        decision = "REAL 🟢"
    else:
        decision = "UNCERTAIN 🟡"

    print(f"{text[:47]:<50}... | {real_score:.4f}   | {fake_score:.4f}   | {decision}")
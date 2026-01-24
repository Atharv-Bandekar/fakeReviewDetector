from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tensorflow as tf
from transformers import DebertaV2Tokenizer, TFDebertaV2ForSequenceClassification, AutoTokenizer, TFAutoModelForSequenceClassification
import traceback

# Import XAI Service
from backend.xai_service import get_explanation 

# --- RAM PROTECTION ---
# 1. Disable GPU (Use CPU Only) to prevent VRAM crashes on 8GB laptops
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# 2. Limit TF logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

app = Flask(__name__)
CORS(app)

# -----------------------------
# Configuration
# -----------------------------
BASE = os.path.dirname(__file__)
MODEL_DIR_AMAZON = os.path.join(BASE, 'backend', 'model')          # DeBERTa (ReviewGuard)
MODEL_DIR_SOCIAL = os.path.join(BASE, 'backend', 'model_tinybert') # TinyBERT (BotHunter)

# -----------------------------
# GLOBAL VARIABLES (LAZY LOADING)
# -----------------------------
amazon_model = None
amazon_tokenizer = None
social_model = None
social_tokenizer = None

def get_amazon_model():
    """Loads DeBERTa only if it's not already loaded."""
    global amazon_model, amazon_tokenizer
    if amazon_model is None:
        print(f"⏳ Loading Amazon Model (DeBERTa)...")
        try:
            amazon_tokenizer = DebertaV2Tokenizer.from_pretrained(MODEL_DIR_AMAZON)
            amazon_model = TFDebertaV2ForSequenceClassification.from_pretrained(MODEL_DIR_AMAZON)
            print("✅ Amazon Model Loaded!")
        except Exception as e:
            print(f"❌ Failed to load Amazon Model: {e}")
            return None, None
    return amazon_model, amazon_tokenizer

def get_social_model():
    """Loads TinyBERT only if it's not already loaded."""
    global social_model, social_tokenizer
    if social_model is None:
        print(f"⏳ Loading Social Model (TinyBERT)...")
        try:
            social_tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR_SOCIAL)
            social_model = TFAutoModelForSequenceClassification.from_pretrained(MODEL_DIR_SOCIAL)
            print("✅ Social Model Loaded!")
        except Exception as e:
            print(f"❌ Failed to load Social Model: {e}")
            return None, None
    return social_model, social_tokenizer

# -----------------------------
# Route 1: Amazon Reviews (DeBERTa)
# -----------------------------
@app.route('/predict', methods=['POST'])
def predict_review():
    model, tokenizer = get_amazon_model() # Load on demand
    if not model: return jsonify({'error': 'Amazon Model missing'}), 500
    
    try:
        data = request.json
        text = data.get('text', '')
        if not text: return jsonify({'error': 'No text'}), 400

        inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=128)
        logits = model(inputs).logits
        probs = tf.nn.softmax(logits, axis=1).numpy()[0]
        
        real_score = float(probs[0])
        fake_score = float(probs[1])
        
        if fake_score > 0.60:
            label = "FAKE"
            confidence = fake_score
            explanation = "DeBERTa detected AI patterns."
        elif real_score > 0.60:
            label = "GENUINE"
            confidence = real_score
            explanation = "DeBERTa detected human patterns."
        else:
            label = "UNCERTAIN"
            confidence = max(fake_score, real_score)
            explanation = "Mixed signals."

        if confidence > 0.99: confidence = 0.99

        return jsonify({'label': label, 'confidence': confidence, 'explanation': explanation})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# -----------------------------
# Route 2: Social Media Comments (TinyBERT)
# -----------------------------
# 🔴 THIS WAS MISSING IN YOUR PREVIOUS FILE!
@app.route('/predict_comment', methods=['POST'])
def predict_comment():
    model, tokenizer = get_social_model() # Load on demand
    if not model: return jsonify({'error': 'Social Model missing'}), 500

    try:
        data = request.json
        text = data.get('text', '')
        
        # TinyBERT Inference
        inputs = tokenizer(text, return_tensors="tf", truncation=True, padding=True, max_length=128)
        logits = model(inputs).logits
        probs = tf.nn.softmax(logits, axis=1).numpy()[0]
        
        human_score = float(probs[0])
        bot_score = float(probs[1]) 

        # Thresholding
        if bot_score > 0.70:
            label = "BOT"
            confidence = bot_score
        else:
            label = "HUMAN"
            confidence = human_score

        print(f"[SOCIAL] {label} ({confidence:.2f}) - {text[:30]}...")

        return jsonify({'label': label, 'confidence': confidence})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -----------------------------
# Route 3: Explainability
# -----------------------------
@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.json
        text = data.get('text', '')
        label = data.get('label', 'UNCERTAIN')
        confidence = float(data.get('confidence', 0))
        
        explanation = get_explanation(text, label, confidence)
        return jsonify({'explanation': explanation})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# --- CPU OPTIMIZATION ---
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from transformers import DebertaV2Tokenizer, TFDebertaV2ForSequenceClassification
import traceback

# 1. IMPORT THE MISSING SERVICE
from xai_service import get_explanation  # <--- THIS WAS LIKELY MISSING

app = Flask(__name__)
CORS(app)

# -----------------------------
# Configuration
# -----------------------------
BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, 'model') 

# -----------------------------
# Load DeBERTa Model
# -----------------------------
print("⏳ Loading DeBERTa Model... (This takes 10-20s on CPU)")
try:
    tokenizer = DebertaV2Tokenizer.from_pretrained(MODEL_DIR)
    model = TFDebertaV2ForSequenceClassification.from_pretrained(MODEL_DIR)
    print("✅ DeBERTa Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("Tip: Check if 'spm.model' and 'tf_model.h5' are in backend/model/")
    model = None

# -----------------------------
# Routes
# -----------------------------
@app.route('/', methods=['GET'])
def home():
    return "✅ DeBERTa Fake Review Detector is Active."

@app.route('/predict', methods=['POST'])
def predict():
    if not model: return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.json
        text = data.get('text', '')
        if not text: return jsonify({'error': 'No text provided'}), 400

        # Tokenize
        inputs = tokenizer(
            text, 
            return_tensors="tf", 
            truncation=True, 
            padding=True, 
            max_length=128
        )
        
        # Inference
        logits = model(inputs).logits
        probabilities = tf.nn.softmax(logits, axis=1).numpy()[0]
        
        real_score = float(probabilities[0])
        fake_score = float(probabilities[1])
        
        # Logic
        if fake_score > 0.60:
            label = "FAKE"
            confidence = fake_score
            explanation = "DeBERTa detected AI-generated patterns."
        elif real_score > 0.60:
            label = "GENUINE"
            confidence = real_score
            explanation = "DeBERTa detected authentic human patterns."
        else:
            label = "UNCERTAIN"
            confidence = max(fake_score, real_score)
            explanation = "Review shows mixed characteristics."

        # Cap confidence at 99% for UX
        if confidence > 0.99: confidence = 0.99

        print(f"[DEBUG] Fake: {fake_score:.4f} | Real: {real_score:.4f} | Text: {text[:30]}...")

        return jsonify({
            'label': label,
            'confidence': confidence,
            'explanation': explanation,
            'keywords': [] 
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 2. ADD THE MISSING ROUTE HERE
@app.route('/explain', methods=['POST'])
def explain():
    try:
        data = request.json
        text = data.get('text', '')
        label = data.get('label', 'UNCERTAIN')
        confidence = float(data.get('confidence', 0))

        if not text: 
            return jsonify({'error': 'No text provided'}), 400

        # Call our separate service
        explanation = get_explanation(text, label, confidence)

        return jsonify({'explanation': explanation})

    except Exception as e:
        print(f"❌ Error in /explain: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
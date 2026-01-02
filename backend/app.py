from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle, os, tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from train_model import PositionalAttention  # import custom layer
import re

app = Flask(__name__)
CORS(app)

# -----------------------------
# Paths
# -----------------------------
BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, 'model')
MODEL_PATH = os.path.join(MODEL_DIR, 'fake_review_model.h5')
TOKENIZER_PATH = os.path.join(MODEL_DIR, 'tokenizer.pkl')
MAX_LEN = 150  # match training

# -----------------------------
# Load model and tokenizer
# -----------------------------
model = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False,
    custom_objects={'PositionalAttention': PositionalAttention}
)
 
with open(TOKENIZER_PATH, 'rb') as f:
    tokenizer = pickle.load(f)

# -----------------------------
# Preprocessing function
# -----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# -----------------------------
# Prediction route
# -----------------------------
@app.route('/predict', methods=['POST'])
def predict():
    text = request.json.get('text', '')
    cleaned = clean_text(text)
    seq = tokenizer.texts_to_sequences([cleaned])
    pad = pad_sequences(seq, maxlen=MAX_LEN)
    pred = float(model.predict(pad)[0][0])
    label = 'OR' if pred > 0.5 else 'CG'
    confidence = pred if pred > 0.5 else 1 - pred
    return jsonify({'label': label, 'confidence': confidence})

# -----------------------------
# Run Flask app
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

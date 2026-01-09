from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle, os, tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Model
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

embedding_out=model.layers[-4].output
att_layer=model.layers[-3]

comtext,attention=att_layer(embedding_out,return_attention=True)
explain_model=Model(inputs=model.input,outputs=[model.output,attention])

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

#-------------
# Explainability function
#-------------

def extract_keywords(cleaned_text, attention, top_k=3):
    seq = tokenizer.texts_to_sequences([cleaned_text])[0]
    words = [tokenizer.index_word.get(i, '') for i in seq]

    att = attention[:len(words)].flatten()
    top_indices = att.argsort()[-top_k:][::-1]

    return [words[i] for i in top_indices if words[i]]


# -----------------------------
# Prediction route
# -----------------------------
@app.route('/predict', methods=['POST'])
def predict():
    text = request.json.get('text', '')
    cleaned = clean_text(text)
    
    seq = tokenizer.texts_to_sequences([cleaned])
    pad = pad_sequences(seq, maxlen=MAX_LEN)
    
    pred, attention = explain_model.predict(pad)
    pred = float(model.predict(pad)[0][0])

    keywords=extract_keywords(cleaned, attention[0])
    
    if pred>0.7:
        label = 'OR'  # Fake
        explanation=f"promotional words detected: {', '.join(keywords)}"
        confidence=round(pred,2)
    elif pred<0.3:
        label = 'CG'  # Genuine
        explanation=f"Neutral and factual wording:{', '.join(keywords)}"
        confidence=round(1-pred,2)
    else:
        label= 'Uncertain'
        explanation="mixed Signals in the review content"
        confidence=round(1 - abs(0.5 - pred)*2,2)
    
    
    return jsonify({'label': label, 
                    'confidence': confidence,
                    'explanation': explanation,
                    'keywords': keywords})

# -----------------------------
# Run Flask app
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Bidirectional, LSTM, Dense, Multiply, Layer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle
import os
import re

# -----------------------------
# Load dataset
# -----------------------------
df = pd.read_csv('fake_reviews_dataset.csv')
texts = df['text_'].astype(str)
labels = df['label']

# -----------------------------
# Preprocess text
# -----------------------------
def clean_text(text):
    text = text.lower()                            # lowercase
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)    # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()      # remove extra spaces
    return text

texts = texts.apply(clean_text)

# -----------------------------
# Encode labels (CG=0, OR=1)
# -----------------------------
encoder = LabelEncoder()
labels = encoder.fit_transform(labels)

# -----------------------------
# Tokenize text
# -----------------------------
max_words = 10000
max_len = 150
tokenizer = Tokenizer(num_words=max_words, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
X = pad_sequences(sequences, maxlen=max_len)
y = np.array(labels)

# -----------------------------
# Split data
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# -----------------------------
# Define Custom Positional Attention Layer (CORRECTED)
# -----------------------------
class PositionalAttention(Layer):
    def __init__(self, **kwargs):
        super(PositionalAttention, self).__init__(**kwargs)
        self.score_dense = Dense(128, activation='tanh')
        # 1. Dense layer to create the attention scores (logits)
        self.att_dense = Dense(1) 
        # 2. Softmax layer to apply on the sequence axis (axis=1)
        self.softmax = tf.keras.layers.Softmax(axis=1)
        self.multiply = Multiply()

    def call(self, inputs):
        # inputs shape: (batch, seq_len, hidden_dim) -> (None, 150, 128)
        
        # Shape: (None, 150, 128)
        score = self.score_dense(inputs)
        
        # Shape: (None, 150, 1)
        att_score = self.att_dense(score) 
        
        # Shape: (None, 150, 1) -> Softmax is applied across the 150 timesteps
        attention = self.softmax(att_score) 
        
        # Shape: (None, 150, 128)
        weighted = self.multiply([inputs, attention]) 
        
        # Shape: (None, 128)
        context = tf.reduce_sum(weighted, axis=1) 
        
        return context
    
    
# -----------------------------
# Model architecture
# -----------------------------
inp = Input(shape=(max_len,))
embedding = Embedding(max_words, 128)(inp)
bilstm = Bidirectional(
    LSTM(64, return_sequences=True)
)(embedding)
attn_out = PositionalAttention()(bilstm)
dense = Dense(64, activation='relu')(attn_out)
output = Dense(1, activation='sigmoid')(dense)

model = Model(inputs=inp, outputs=output)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# -----------------------------
# Train with class weights and early stopping
# -----------------------------
class_weights = {0:1.0, 1:1.5}
early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=10,
    batch_size=64,
    class_weight=class_weights,
    callbacks=[early_stop]
)

# -----------------------------
# Save model & tokenizer
# -----------------------------
os.makedirs('model', exist_ok=True)
model.save('model/fake_review_model.h5')

with open('model/tokenizer.pkl', 'wb') as f:
    pickle.dump(tokenizer, f)

print("✅ Model and tokenizer saved successfully!")

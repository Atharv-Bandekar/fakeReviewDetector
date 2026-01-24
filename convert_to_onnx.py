import os
from pathlib import Path
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from optimum.onnxruntime import ORTQuantizer

# --- CONFIGURATION ---
INPUT_MODEL_DIR = "backend/model"   # Your heavy TF model
OUTPUT_ONNX_DIR = "backend/model_onnx" # The new light model

def convert_and_quantize():
    print(f"⏳ Loading TensorFlow model from {INPUT_MODEL_DIR}...")
    
    # 1. LOAD & EXPORT TO ONNX
    # We load the TF model and tell Optimum to export it to ONNX on the fly
    try:
        model = ORTModelForSequenceClassification.from_pretrained(
            INPUT_MODEL_DIR,
            from_transformers=True, # Uses standard Transformers loading
            export=True             # Triggers the conversion
        )
        tokenizer = AutoTokenizer.from_pretrained(INPUT_MODEL_DIR)
        
        # Save the full precision ONNX model first
        print("⏳ Exporting to ONNX...")
        model.save_pretrained(OUTPUT_ONNX_DIR)
        tokenizer.save_pretrained(OUTPUT_ONNX_DIR)
        
    except Exception as e:
        print(f"❌ Error during export: {e}")
        print("Tip: Ensure backend/model has 'config.json' and 'tf_model.h5'")
        return

    # 2. QUANTIZE (The Magic Step)
    print("⏳ Quantizing to INT8 (Shrinking size by 4x)...")
    
    # Define config: Dynamic Quantization is best for CPU/NLP
    qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=True)
    
    quantizer = ORTQuantizer.from_pretrained(model)
    
    # Apply quantization
    quantizer.quantize(
        save_dir=OUTPUT_ONNX_DIR,
        quantization_config=qconfig
    )
    
    print(f"✅ DONE! Optimized model saved to: {OUTPUT_ONNX_DIR}")
    print("You can now update app.py to use this folder.")

if __name__ == "__main__":
    convert_and_quantize()
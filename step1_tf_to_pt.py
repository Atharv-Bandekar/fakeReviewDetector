import os
import shutil
from transformers import DebertaV2Config, DebertaV2ForSequenceClassification, AutoTokenizer
from transformers.models.deberta_v2.modeling_deberta_v2 import load_tf_weights_in_deberta_v2

# PATHS
INPUT_TF_DIR = "backend/model"
TEMP_PT_DIR = "backend/model_pytorch_temp"
TF_WEIGHTS_PATH = os.path.join(INPUT_TF_DIR, "tf_model.h5")

def convert():
    print(f"⏳ Loading Config from {INPUT_TF_DIR}...")
    
    # 1. Clean up temp dir
    if os.path.exists(TEMP_PT_DIR):
        shutil.rmtree(TEMP_PT_DIR)

    try:
        # 2. Load Configuration
        config = DebertaV2Config.from_pretrained(INPUT_TF_DIR)
        
        # 3. Create a 'Real' PyTorch model in RAM (Random Weights)
        # We generally instantiate the class directly to avoid AutoModel meta-device magic
        print("⏳ Initializing empty PyTorch model on CPU...")
        model = DebertaV2ForSequenceClassification(config)
        
        # 4. MANUALLY Inject TensorFlow Weights
        print(f"⏳ Injecting TensorFlow weights from {TF_WEIGHTS_PATH}...")
        model = load_tf_weights_in_deberta_v2(model, config, TF_WEIGHTS_PATH)
        
        # 5. Load Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(INPUT_TF_DIR)
        
        # 6. Save
        print(f"💾 Saving intermediate PyTorch model to {TEMP_PT_DIR}...")
        model.save_pretrained(TEMP_PT_DIR)
        tokenizer.save_pretrained(TEMP_PT_DIR)
        
        print("✅ Step 1 Complete! The Meta Tensor trap has been defeated.")
        print("👉 Now run: python step2_quantize.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Tip: Check if 'tf_model.h5' exists inside 'backend/model'.")

if __name__ == "__main__":
    convert()
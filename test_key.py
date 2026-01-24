import requests

print("🔍 Scanning OpenRouter for available FREE models...")

try:
    response = requests.get("https://openrouter.ai/api/v1/models")
    
    if response.status_code == 200:
        all_models = response.json()['data']
        free_models = [m['id'] for m in all_models if ":free" in m['id']]
        
        print(f"\n✅ Found {len(free_models)} active FREE models:")
        for model in free_models:
            print(f" - {model}")
            
    else:
        print(f"❌ Error: {response.status_code}")

except Exception as e:
    print(f"❌ Connection Error: {e}")
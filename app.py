from flask import Flask, request, jsonify, send_from_directory
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import json
import os
import re
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')

# Load model
model_name = "google/gemma-3-1b-it"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=200,
    temperature=0.7,
    do_sample=True,
    pad_token_id=tokenizer.eos_token_id
)

# Local data
with open('local_data.json', 'r', encoding='utf-8') as f:
    local_data = json.load(f)

def search_local_items(query):
    query_lower = query.lower()
    results = []
    
    for category, items in local_data.items():
        for item in items:
            if any(word in item['name'].lower() or word in item['desc'].lower() 
                   for word in ['رستوران', 'هتل', 'خرید', query_lower]):
                results.append(f"{item['name']} ({category}) - {item['desc']}")
                if len(results) >= 3:
                    break
        if len(results) >= 3:
            break
    
    return results if results else ["اطلاعات دقیقی ندارم، ولی بندرعباس پر از گزینه‌های عالیه! 😊"]

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    context = search_local_items(message)
    prompt = f"""
بندرعباس AI هستم! مفید و دوستانه جواب بده:

کاربر: {message}

اطلاعات محلی:
{chr(10).join(context)}

جواب مختصر و مفید (حداکثر 2 جمله):
"""
    
    response = pipe(prompt)[0]['generated_text']
    reply = response.split("جواب مختصر و مفید")[-1].strip()
    
    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

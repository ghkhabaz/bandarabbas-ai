import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

# Hugging Face Token
HF_TOKEN = os.getenv("HF_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-1.5B-Instruct"

# مسیر فایل‌های داده‌های محلی بندرعباس
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLACES_PATH = os.path.join(BASE_DIR, "places.json")
FOOD_PATH = os.path.join(BASE_DIR, "food.json")
STAYS_PATH = os.path.join(BASE_DIR, "stays.json")
SHOPS_PATH = os.path.join(BASE_DIR, "shops.json")


def load_data():
    """خواندن داده‌ها از چهار فایل JSON جداگانه."""
    data = {}
    try:
        with open(PLACES_PATH, "r", encoding="utf-8") as f:
            data["places"] = json.load(f)
    except Exception:
        data["places"] = []
    try:
        with open(FOOD_PATH, "r", encoding="utf-8") as f:
            data["food"] = json.load(f)
    except Exception:
        data["food"] = []
    try:
        with open(STAYS_PATH, "r", encoding="utf-8") as f:
            data["stays"] = json.load(f)
    except Exception:
        data["stays"] = []
    try:
        with open(SHOPS_PATH, "r", encoding="utf-8") as f:
            data["shops"] = json.load(f)
    except Exception:
        data["shops"] = []
    return data


def search_local_items(question: str, data: dict) -> list:
    """جستجوی هوشمند در JSONها - همون منطق قبلی"""
    q = question.strip().lower()
    if not q:
        return []

    words = [w for w in q.split() if len(w) > 1]
    results = []

    # کلمات کلیدی (همون قبلی...)
    food_keywords = ["رستوران", "غذا", "خوردن", "خوری", "ماهی", "میگو", "کافه"]
    place_keywords = ["دیدنی", "ساحل", "بازار", "پارک", "مجتمع"]
    stays_keywords = ["هتل", "اقامت"]
    shops_keywords = ["خرید", "فروشگاه", "مجتمع تجاری"]

    has_food = any(k in q for k in food_keywords)
    has_place = any(k in q for k in place_keywords)
    has_stay = any(k in q for k in stays_keywords)
    has_shop = any(k in q for k in shops_keywords)

    search_sections = []
    if has_stay:
        search_sections = ["stays"]
    else:
        if has_food: search_sections.append("food")
        if has_place: search_sections.append("places")
        if has_shop: search_sections.append("shops")
        if not search_sections:
            search_sections = ["places", "food", "stays", "shops"]

    area_keywords = ["سورو", "بلوار صیادان", "بلوار ساحلی", "آزادی", "گلشهر", "بلوار جمهوری", "بلوار استقلال"]

    for section_name in search_sections:
        items = data.get(section_name, [])
        for item in items:
            score = 0
            name = str(item.get("name", "")).lower()
            typ = str(item.get("type", "")).lower()
            desc = str(item.get("description", "")).lower()
            tags_text = " ".join(map(str, item.get("tags", []))).lower()
            area_text = str(item.get("area", "") + " " + item.get("address", "")).lower()

            # تطبیق کلمات
            for w in words:
                if w in name or w in typ or w in desc or w in tags_text:
                    score += 2
            # تطبیق منطقه
            for ak in area_keywords:
                if ak in q and ak in area_text:
                    score += 5

            if score > 0:
                results.append({"item": item, "score": score})

    if not results:
        return []

    results.sort(key=lambda x: x["score"], reverse=True)
    return [results[0]["item"]]  # فقط بهترین


def format_items_plain(items: list) -> str:
    """خلاصه متنی آیتم‌ها"""
    lines = []
    for item in items:
        name = item.get("name", "")
        typ = item.get("type", "")
        area = item.get("area", "")
        address = item.get("address", "")
        price = item.get("price_level", "")
        tags = ", ".join(item.get("tags", []))
        desc = item.get("description", "")
        
        part = f"نام: {name}"
        if typ: part += f" | نوع: {typ}"
        if area or address: part += f" | آدرس: {area} - {address}".strip(" -")
        if price: part += f" | قیمت: {price}"
        if tags: part += f" | تگ‌ها: {tags}"
        if desc: part += f" | توضیحات: {desc}"
        lines.append(part)
    return "\n".join(lines) if lines else "هیچ گزینه‌ای پیدا نشد"


def format_items_for_user_with_model(question: str, items: list) -> str:
    """Hugging Face Qwen2.5"""
    if not items:
        return "فعلاً گزینه‌ای برای این سؤال پیدا نکردم."

    plain_text = format_items_plain(items)
    allowed_names = [item.get("name", "") for item in items if item.get("name")]
    names_text = "، ".join(allowed_names)

    system_prompt = (
        f"تو BandarAbbas AI، راهنمای محلی بندرعباس هستی.\n"
        f"فقط از این مکان‌ها استفاده کن: {names_text}\n"
        "محاوره‌ای و دوستانه جواب بده.\n"
        "حتماً نام دقیق مکان رو بگو.\n"
        "کوتاه و مفید (۳-۵ جمله).\n"
        "خروجی فقط فارسی."
    )

    payload = {
        "inputs": f"{system_prompt}\n\nداده‌ها:\n{plain_text}\n\nسؤال: {question}",
        "parameters": {"max_new_tokens": 250, "temperature": 0.8, "return_full_text": False}
    }

    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            answer = result[0]["generated_text"] if result else "مشکل در تولید جواب."
            
            # اگر نام نبود، اضافه کن
            if not any(name in answer for name in allowed_names if name):
                main_name = allowed_names[0]
                answer = f"یه گزینه خوب برات '{main_name}' هست.\n" + answer
            return answer
        else:
            print(f"HF API Error: {response.status_code}")
            return f"چند گزینه مناسب: {allowed_names[0] if allowed_names else 'نامشخص'}"
    except Exception as e:
        print(f"HF Error: {e}")
        return f"چند گزینه مناسب: {allowed_names[0] if allowed_names else 'نامشخص'}"


def ask_bandar(question: str) -> str:
    text = question.strip()
    
    if text in ["سلام", "سلام!", "درود"]:
        return "سلام! خوش اومدی به BandarAbbas AI 😊 هر سؤالی درباره رستوران، هتل، خرید یا جاهای دیدنی بندرعباس داری بپرس."
    
    data = load_data()
    items = search_local_items(text, data)
    
    if not items:
        return "برای این سؤال هنوز اطلاعات ندارم. درباره رستوران، هتل یا خرید تو بندرعباس بپرس."
    
    return format_items_for_user_with_model(text, items)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    question = data.get("message", "").strip()
    if not question:
        return jsonify({"error": "پیام خالی است"}), 400
    
    answer = ask_bandar(question)
    return jsonify({"reply": answer})


@app.route("/")
def home():
    return jsonify({"message": "BandarAbbas AI آماده است! به /api/chat پیام بفرست."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

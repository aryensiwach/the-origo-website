from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from astro_engine import generate_chart_data
import traceback
from groq import Groq

# Load Environment Variables
load_dotenv()

app = Flask(__name__)

# ==========================================
# 1. FIREBASE CONFIGURATION
# ==========================================
if not firebase_admin._apps:
    try:
        # Local testing ke liye file check
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Initialized Successfully")
        else:
            print("⚠️ Service Account Key not found!")
    except Exception as e:
        print(f"❌ Firebase Init Error: {e}")

db = firestore.client()

# ==========================================
# 2. API KEYS SETUP (SECURE)
# ==========================================
VEDIC_API_KEY = os.getenv("VEDIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("🚀 Groq AI Connected Successfully")
    except Exception as e:
        print(f"⚠️ Groq Connection Error: {e}")
else:
    print("⚠️ WARNING: GROQ_API_KEY missing in .env")

# Rashi Mapping
RASHI_MAP = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio", 
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

# ==========================================
# 3. HELPER FUNCTION
# ==========================================
def format_chart_for_ai(chart_data):
    if not chart_data or not isinstance(chart_data, dict):
        return "No Data Available"
    try:
        asc_sign = chart_data.get('Asc') or chart_data.get('Ascendant')
        if not asc_sign: return "Ascendant Missing."

        formatted_list = []
        formatted_list.append(f"- **LAGNA (Ascendant)**: {RASHI_MAP.get(asc_sign, 'Unknown')} Sign (1st House)")

        for planet, sign in chart_data.items():
            if planet in ['Asc', 'Ascendant']: continue
            diff = sign - asc_sign
            if diff < 0: diff += 12
            house_num = diff + 1
            rashi_name = RASHI_MAP.get(sign, "Unknown")
            formatted_list.append(f"- **{planet}**: {house_num}th House ({rashi_name})")

        return "\n".join(formatted_list)
    except:
        return "Error Formatting Chart"

# ==========================================
# 4. ROUTES
# ==========================================
@app.route('/')
def home():
    # Key HTML ko pass kar rahe hain
    fb_key = os.getenv("FIREBASE_API_KEY")
    return render_template('index.html', fb_key=fb_key)

@app.route('/dashboard')
def dashboard():
    fb_key = os.getenv("FIREBASE_API_KEY")
    return render_template('dashboard.html', fb_key=fb_key)

@app.route('/soulmate')
def soulmate():
    fb_key = os.getenv("FIREBASE_API_KEY")
    return render_template('soulmate.html', fb_key=fb_key)

@app.route('/api/save_user_data', methods=['POST'])
def save_user_data():
    try:
        uid = request.form.get('uid')
        name = request.form.get('name')
        dob = request.form.get('dob')
        time = request.form.get('time')
        place = request.form.get('place')
        gender = request.form.get('gender')
        email = request.form.get('email')
        lang = request.form.get('lang')
        status = request.form.get('status')

        if not uid: return jsonify({"status": "error"}), 400
        
        chart_data = generate_chart_data(name, dob, time, place, VEDIC_API_KEY)
        if "error" in chart_data: return jsonify({"status": "error"}), 400

        current_points = 0 
        if not uid.startswith('guest_'):
            doc = db.collection('users').document(uid).get()
            # Yahan 20 points kar diye hain (Existing user ka purana balance, naye ka 20)
            current_points = doc.to_dict().get('profile', {}).get('credits', 20) if doc.exists else 20

        chart_data['profile'].update({
            'uid': uid, 'email': email, 'name': name,
            'gender': gender, 'dob': dob, 'tob': time, 'place': place,
            'status': status, 'lang': lang,
            'credits': current_points 
        })
        db.collection('users').document(uid).set(chart_data)
        return jsonify({"status": "success", "user_id": uid})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat_analysis', methods=['POST'])
def chat_analysis():
    try:
        data = request.json
        target_uid = data.get('uid')
        payer_uid = data.get('payer_uid', target_uid)
        user_message = data.get('message', '') 
        chart_focus = data.get('chart_focus', 'D1')
        cost = data.get('cost', 1)

        doc = db.collection('users').document(target_uid).get()
        if not doc.exists: return jsonify({"reply": "No data found."})
        
        user_data = doc.to_dict()
        profile = user_data.get('profile', {})
        charts = user_data.get('charts', {})
        dasha = user_data.get('dasha', {})

        payer_ref = db.collection('users').document(payer_uid)
        credits = payer_ref.get().to_dict().get('profile', {}).get('credits', 0)
        
        if credits < cost: return jsonify({"reply": f"Low Balance: {credits}", "error": "low_balance"})

        d1_readable = format_chart_for_ai(charts.get('D1', {}))
        target_readable = format_chart_for_ai(charts.get(chart_focus, {}))

        msg_lower = user_message.lower()
        is_report_mode = "analyze" in msg_lower and "chart" in msg_lower
        
        task_instruction = ""
        depth_instruction = ""

        if is_report_mode:
            depth_instruction = """
            **MODE: DETAILED REPORT**
            - Follow the SECTION STRUCTURE exactly.
            - Use double line breaks between paragraphs.
            """
            if chart_focus == 'D1':
                task_instruction = """
                **TASK: Generate D1 Chart Analysis in 6 Distinct Sections**
                ### Section 1: 🔥 Powerful Yogas & Rarity
                ### Section 2: 👤 Personality & Looks
                ### Section 3: 💰 Wealth Potential
                ### Section 4: 🐉 Rahu & Ketu Axis
                ### Section 5: 🪐 Moon, Mars & Saturn
                ### Section 6: ⭐ Final Rating
                """
            elif chart_focus == 'D2':
                task_instruction = "Detailed D2 Wealth analysis."
            else:
                task_instruction = f"Analyze {chart_focus} in detailed sections."
        else:
            if "Depth: short" in user_message:
                depth_instruction = "Keep answer under 60 words."
            elif "Depth: detailed" in user_message:
                depth_instruction = "Detailed explanation with logic."
            else:
                depth_instruction = "Balanced answer."
            task_instruction = "Answer user question directly."

        final_prompt = f"""
        You are Origo AI.
        [CLIENT] {profile.get('name')} | {profile.get('gender')}
        [DATA]
        D1: {d1_readable}
        {chart_focus}: {target_readable}
        [INPUT] "{user_message}"
        [INSTRUCTIONS] {task_instruction}
        [RULES] {depth_instruction}
        - Use Markdown.
        - End with 3 suggestions: <<<Q1 | Q2 | Q3>>>
        """

        if not client: return jsonify({"reply": "API Error: Groq not connected"})
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful, mystical, and accurate Vedic Astrologer named Origo. Always output in valid Markdown."},
                {"role": "user", "content": final_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=3000, 
        )
        
        reply_text = chat_completion.choices[0].message.content
        payer_ref.update({"profile.credits": credits - cost})
        return jsonify({"reply": reply_text, "new_credits": credits - cost})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"reply": "Server Error."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
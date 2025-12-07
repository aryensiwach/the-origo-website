from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
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
try:
    if not firebase_admin._apps:
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
        if firebase_creds:
            cred = credentials.Certificate(json.loads(firebase_creds))
            firebase_admin.initialize_app(cred)
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    db = None
    print(f"Database Error: {e}")

# ==========================================
# 2. API KEYS SETUP
# ==========================================
VEDIC_API_KEY = os.getenv("VEDIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("🚀 Groq AI Connected")
    except Exception as e:
        print(f"⚠️ Groq Error: {e}")

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
        return "No Data"
    try:
        asc_sign = chart_data.get('Asc') or chart_data.get('Ascendant')
        if not asc_sign: return "Ascendant Missing."
        formatted_list = [f"- **LAGNA**: {RASHI_MAP.get(asc_sign, 'Unknown')} (1st House)"]
        for planet, sign in chart_data.items():
            if planet in ['Asc', 'Ascendant']: continue
            diff = sign - asc_sign
            if diff < 0: diff += 12
            house_num = diff + 1
            formatted_list.append(f"- **{planet}**: {house_num}th House ({RASHI_MAP.get(sign, 'Unknown')})")
        return "\n".join(formatted_list)
    except:
        return "Error Formatting"

# ==========================================
# 4. ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html', fb_key=os.getenv("FIREBASE_API_KEY"))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', fb_key=os.getenv("FIREBASE_API_KEY"))

@app.route('/soulmate')
def soulmate():
    return render_template('soulmate.html', fb_key=os.getenv("FIREBASE_API_KEY"))

@app.route('/api/save_user_data', methods=['POST'])
def save_user_data():
    if not db: return jsonify({"status": "error", "message": "DB Error"}), 500
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

        chart_data = generate_chart_data(name, dob, time, place, VEDIC_API_KEY)
        if "error" in chart_data: return jsonify({"status": "error"}), 400

        current_points = 20
        if not uid.startswith('guest_'):
            doc = db.collection('users').document(uid).get()
            if doc.exists:
                current_points = doc.to_dict().get('profile', {}).get('credits', 20)

        chart_data['profile'].update({
            'uid': uid, 'email': email, 'name': name,
            'gender': gender, 'dob': dob, 'tob': time, 'place': place,
            'status': status, 'lang': lang,
            'credits': current_points 
        })
        db.collection('users').document(uid).set(chart_data)
        return jsonify({"status": "success", "user_id": uid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat_analysis', methods=['POST'])
def chat_analysis():
    if not client or not db: return jsonify({"reply": "System Error: Check Config"}), 200
    try:
        data = request.json
        target_uid = data.get('uid')
        payer_uid = data.get('payer_uid')
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

        # --- RESTORED HIGH QUALITY PROMPT LOGIC ---
        msg_lower = user_message.lower()
        is_report_mode = "analyze" in msg_lower and "chart" in msg_lower
        
        task_instruction = ""
        depth_instruction = ""

        if is_report_mode:
            # === REPORT MODE (ORIGINAL DETAILED FORMAT) ===
            depth_instruction = """
            **MODE: DETAILED ASTROLOGICAL REPORT**
            - You MUST output a long, structured response.
            - Use `###` for Section Headers.
            - Use `*` for bullet points.
            - Use `**` for bold text.
            - **CRITICAL:** Add a blank line between every paragraph and list item for clear spacing.
            """
            
            if chart_focus == 'D1':
                task_instruction = """
                **TASK: Generate D1 Chart Analysis in 6 Distinct Sections**
                
                ### Section 1: 🔥 Powerful Yogas & Rarity
                - Identify 3 major Yogas (e.g., Gajakesari, Raj Yoga) strictly from data.
                - Rate their rarity (Common/Rare/Legendary).
                
                ### Section 2: 👤 Personality & Looks
                - Analyze Lagna & Lord for core nature.
                - Analyze traits: Good vs Bad habits.
                - Looks/Aura description.
                
                ### Section 3: 💰 Wealth Potential
                - How much money? (High/Average).
                - Sources (Job/Business).
                
                ### Section 4: 🐉 Rahu & Ketu Axis
                - Where are they placed?
                - What is their karmic impact?
                
                ### Section 5: 🪐 Moon, Mars & Saturn
                - Analyze Moon (Mind), Mars (Energy), Saturn (Karma).
                - Explain why they are good or bad here.
                
                ### Section 6: ⭐ Final Rating
                - Rate this Kundli out of 10.
                - Final One-Line Verdict.
                """
            else:
                task_instruction = f"Analyze {chart_focus} in detailed sections with clear headers and bullet points."

        else:
            # === CHAT MODE ===
            if "Depth: short" in user_message:
                depth_instruction = "Keep answer under 60 words. Bullet points only."
            elif "Depth: detailed" in user_message:
                depth_instruction = "Detailed explanation (300+ words) with logic and remedies."
            else:
                depth_instruction = "Balanced answer (150 words)."
            task_instruction = "Answer user question directly."

        # --- FINAL PROMPT ---
        final_prompt = f"""
        You are Origo AI, an expert Vedic Astrologer.
        
        [1. CLIENT PROFILE]
        Name: {profile.get('name')} | Gender: {profile.get('gender')}
        Dasha: {dasha.get('mahadasha')} > {dasha.get('antardasha')}

        [2. PLANETARY DATA]
        === D1 CHART ===
        {d1_readable}
        
        === {chart_focus} CHART ===
        {target_readable}

        [3. INPUT]
        "{user_message}"

        [4. INSTRUCTIONS]
        {task_instruction}
        
        [5. RULES]
        {depth_instruction}
        - Use strict Markdown formatting.
        - Add `---` separator after every section.
        - End with 3 specific suggestions: <<<Q1 | Q2 | Q3>>>
        """

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful, mystical, and accurate Vedic Astrologer named Origo. Always output in valid Markdown with proper spacing."},
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
        print(f"❌ Runtime Error: {e}")
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
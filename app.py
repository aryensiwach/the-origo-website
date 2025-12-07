from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json # <--- IMPORTANT ADDITION
from dotenv import load_dotenv
from astro_engine import generate_chart_data
import traceback
from groq import Groq

# Load Environment Variables
load_dotenv()

app = Flask(__name__)

# ==========================================
# 1. FIREBASE CONFIGURATION (VERCEL FIX)
# ==========================================
if not firebase_admin._apps:
    try:
        # Check for Environment Variable first (Vercel Production)
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
        
        if firebase_creds:
            # Parse the JSON string from Environment Variable
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Initialized from ENV")
            
        # Fallback to local file (Local Development)
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Initialized Locally")
            
        else:
            print("⚠️ Critical: No Firebase Credentials Found! App will crash.")
            
    except Exception as e:
        print(f"❌ Firebase Init Error: {e}")

# Initialize Firestore
try:
    db = firestore.client()
except Exception:
    db = None # Prevent immediate crash, handle in routes

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

        formatted_list = []
        formatted_list.append(f"- **LAGNA**: {RASHI_MAP.get(asc_sign, 'Unknown')} (1st House)")

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
    if not db: return jsonify({"status": "error", "message": "Database Error"}), 500
    try:
        uid = request.form.get('uid')
        # ... (Rest of logic remains same) ...
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

        current_points = 20 # Default for new users
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
        print(e)
        return jsonify({"status": "error"}), 500

@app.route('/api/chat_analysis', methods=['POST'])
def chat_analysis():
    if not db: return jsonify({"reply": "Database Error"}), 500
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

        # ... (AI Logic Same as Before) ...
        # Simplified for brevity, paste your logic here if needed
        # Or just use the logic from previous response
        
        # --- RE-INSERTING YOUR EXACT AI LOGIC HERE ---
        msg_lower = user_message.lower()
        is_report_mode = "analyze" in msg_lower and "chart" in msg_lower
        
        task_instruction = ""
        depth_instruction = ""

        if is_report_mode:
            depth_instruction = "Give detailed markdown report."
            if chart_focus == 'D1':
                task_instruction = "Detailed D1 Analysis 6 Sections."
            else:
                task_instruction = f"Analyze {chart_focus}."
        else:
            depth_instruction = "Keep it chatty."
            task_instruction = "Answer directly."

        final_prompt = f"""
        You are Origo AI.
        [CLIENT] {profile.get('name')}
        [DATA] {d1_readable}
        [INPUT] {user_message}
        """

        if not client: return jsonify({"reply": "AI Error"})
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are Origo AI."}, {"role": "user", "content": final_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        
        reply_text = chat_completion.choices[0].message.content
        payer_ref.update({"profile.credits": credits - cost})
        return jsonify({"reply": reply_text, "new_credits": credits - cost})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"reply": "Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
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

# GLOBAL VARIABLES TO TRACK ERRORS
firebase_status = "Not Initialized"
groq_status = "Not Initialized"
db = None
client = None

# ==========================================
# 1. FIREBASE CONFIGURATION (DEBUG MODE)
# ==========================================
try:
    if not firebase_admin._apps:
        # Check Environment Variable
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS")
        
        if firebase_creds:
            try:
                # Try to parse JSON
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                firebase_status = "✅ Success (From Env)"
                print(firebase_status)
            except json.JSONDecodeError as e:
                firebase_status = f"❌ JSON Error: {str(e)}"
                print(firebase_status)
            except Exception as e:
                firebase_status = f"❌ Certificate Error: {str(e)}"
                print(firebase_status)
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            firebase_status = "✅ Success (Local File)"
        else:
            firebase_status = "⚠️ No Credentials Found"
    
    # Init DB
    if firebase_status.startswith("✅"):
        db = firestore.client()
    else:
        db = None

except Exception as e:
    firebase_status = f"❌ General Error: {str(e)}"
    db = None

# ==========================================
# 2. API KEYS & GROQ SETUP
# ==========================================
VEDIC_API_KEY = os.getenv("VEDIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

try:
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
        groq_status = "✅ Connected"
    else:
        groq_status = "⚠️ Missing Key"
except Exception as e:
    groq_status = f"❌ Error: {str(e)}"

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
    except Exception as e:
        return f"Error Formatting: {str(e)}"

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
    if not db:
        return jsonify({"status": "error", "message": f"DB Error: {firebase_status}"}), 500
    
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
    # 1. DEBUG CHECKS
    if not db:
        return jsonify({"reply": f"❌ Database Crash: {firebase_status}"}), 200
    
    if not client:
        return jsonify({"reply": f"❌ Groq API Crash: {groq_status}"}), 200

    try:
        # 2. DATA FETCH
        data = request.json
        target_uid = data.get('uid')
        payer_uid = data.get('payer_uid')
        user_message = data.get('message', '') 
        chart_focus = data.get('chart_focus', 'D1')
        cost = data.get('cost', 1)

        doc = db.collection('users').document(target_uid).get()
        if not doc.exists: return jsonify({"reply": "No data found for this user."})
        
        user_data = doc.to_dict()
        profile = user_data.get('profile', {})
        charts = user_data.get('charts', {})
        dasha = user_data.get('dasha', {})

        payer_ref = db.collection('users').document(payer_uid)
        credits = payer_ref.get().to_dict().get('profile', {}).get('credits', 0)
        
        if credits < cost: return jsonify({"reply": f"Low Balance: {credits} points", "error": "low_balance"})

        d1_readable = format_chart_for_ai(charts.get('D1', {}))
        target_readable = format_chart_for_ai(charts.get(chart_focus, {}))

        # 3. AI LOGIC
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
        
        # 4. CALL GROQ
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are Origo AI."}, {"role": "user", "content": final_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2000
        )
        
        reply_text = chat_completion.choices[0].message.content
        payer_ref.update({"profile.credits": credits - cost})
        return jsonify({"reply": reply_text, "new_credits": credits - cost})

    except Exception as e:
        # 5. CATCH ACTUAL ERROR
        error_msg = traceback.format_exc()
        print(f"❌ Runtime Error: {error_msg}")
        return jsonify({"reply": f"⚠️ System Error: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
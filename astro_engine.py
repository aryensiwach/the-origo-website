import requests
import datetime
import os

# --- HELPER FUNCTIONS ---
def get_age(dob_str):
    """Calculates Age based on Birth Year"""
    try:
        birth_year = int(dob_str.split('-')[0])
        current_year = datetime.datetime.now().year
        return current_year - birth_year
    except:
        return 0

def get_sign_number(degree, division):
    if degree is None: return 0
    varga_deg = (degree * division) % 360
    return int(varga_deg / 30) + 1

def get_geo_coords(city_name):
    """
    Fetches Latitude and Longitude. Defaults to New Delhi if fails.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {'User-Agent': 'TheOrigoApp/1.0'}
        res = requests.get(url, headers=headers)
        if len(res.json()) > 0:
            data = res.json()[0]
            # Coordinates mil gaye
            return float(data['lat']), float(data['lon'])
    except Exception as e:
        print(f"⚠️ Geo Error: {e}")
    
    # Agar city nahi mili to default (New Delhi)
    return 28.6139, 77.2090 

def get_current_dasha(dob, time, lat, lon, api_key):
    """
    Fetches Current Dasha with better error handling & key variations
    """
    print("⏳ Fetching Dasha...")
    try:
        formatted_dob = datetime.datetime.strptime(dob, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        url = "https://api.vedicastroapi.com/v3-json/dashas/vimshottari-current"
        params = {
            'api_key': api_key, 
            'dob': formatted_dob, 
            'tob': time, 
            'lat': lat, 
            'lon': lon, 
            'tz': 5.5, 
            'lang': "en"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 200 and 'response' in data:
            curr = data['response']
            
            # --- FIX FOR 'NA' ISSUE ---
            # API kabhi 'mahadasha' bhejti hai, kabhi 'current_mahadasha'. Hum dono check karenge.
            md = curr.get('mahadasha') or curr.get('current_mahadasha') or "Unknown"
            ad = curr.get('antardasha') or curr.get('current_antardasha') or "Unknown"
            pd = curr.get('pratyantardasha') or "Unknown"
            
            print(f"✅ Dasha Found: {md} > {ad}")
            
            return {
                "mahadasha": md,
                "antardasha": ad,
                "pratyantardasha": pd,
                "end_date": curr.get('end_date', '')
            }
        else:
            print(f"❌ Dasha API Failed: {data}")

    except Exception as e:
        print(f"❌ Dasha Logic Error: {e}")
    
    return {"mahadasha": "N/A", "antardasha": "N/A"}

# --- MAIN GENERATOR FUNCTION ---
def generate_chart_data(name, dob, time, city, api_key):
    """
    Generates complete Vedic Astrology Profile (D1 to D60 + Dasha)
    """
    
    # 1. Prepare Data
    age = get_age(dob)
    lat, lon = get_geo_coords(city)
    
    # Root Structure
    db_record = {
        "profile": {
            "name": name,
            "age": age,
            "dob": dob,
            "tob": time,
            "city": city,
            "coordinates": {
                "lat": lat,
                "lon": lon
            },
            "created_at": datetime.datetime.utcnow().isoformat()
        },
        "charts": {},
        "dasha": {} 
    }

    # 2. Fetch Planets (D1 Data)
    formatted_dob = datetime.datetime.strptime(dob, "%Y-%m-%d").strftime("%d/%m/%Y")
    
    url = "https://api.vedicastroapi.com/v3-json/horoscope/planet-details"
    params = {
        'api_key': api_key, 
        'dob': formatted_dob, 
        'tob': time, 
        'lat': lat, 
        'lon': lon, 
        'tz': 5.5, 
        'lang': "en"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        p_data = data.get('response', {})
        
        if not p_data:
            return {"error": "API returned no data"}

        # 3. Extract Degrees
        my_planets = {} 
        lagna_deg = 0
        
        iterable = p_data.values() if isinstance(p_data, dict) else p_data
        
        for info in iterable:
            if not isinstance(info, dict): continue
            
            p_full = info.get('full_name')
            p_name = info.get('name')
            deg = info.get('global_degree')
            
            if deg is None: continue 
            
            if p_full == "Ascendant":
                lagna_deg = deg
            elif p_name not in ["Uranus", "Neptune", "Pluto", "Mean Node", "True Node"]:
                my_planets[p_full] = deg

        # 4. GENERATE ALL VARGA CHARTS
        all_vargas = {
            1: "D1", 2: "D2", 3: "D3", 4: "D4", 7: "D7", 9: "D9", 
            10: "D10", 12: "D12", 16: "D16", 20: "D20", 24: "D24", 
            27: "D27", 30: "D30", 40: "D40", 45: "D45", 60: "D60"
        }
        
        for div, chart_code in all_vargas.items():
            chart_obj = {}
            chart_obj["Asc"] = get_sign_number(lagna_deg, div)
            for p_name, p_deg in my_planets.items():
                chart_obj[p_name] = get_sign_number(p_deg, div)
            
            db_record["charts"][chart_code] = chart_obj

        # 5. FETCH CURRENT DASHA
        db_record['dasha'] = get_current_dasha(dob, time, lat, lon, api_key)

        return db_record

    except Exception as e:
        print(f"Engine Error: {e}")
        return {"error": str(e)}
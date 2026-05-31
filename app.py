import io
import os
import pickle
import datetime
import random
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'crop_recommender.pkl')
LABELS_PATH = os.path.join(BASE_DIR, 'label_classes.pkl')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change_this_secret_for_dev_only')

# Production session settings
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('VERCEL') == '1':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# --- Load Machine Learning Model ---
model = None
crops_list = []
model_loaded = False

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(LABELS_PATH, 'rb') as f:
        crops_list = pickle.load(f)
    model_loaded = True
    print("Machine Learning model and labels loaded successfully.")
except Exception as e:
    print(f"Warning: Could not load ML model files: {e}.")
    print("Crop recommendations will use a scientifically-backed agronomic fallback algorithm.")

# --- MongoDB Setup with Resilient Mock Fallback ---
mongo_available = False
predictions_col = None
users_col = None

try:
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGODB_DB_NAME", "agrosmart_ai")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
    # Trigger server call to verify connection
    client.server_info()
    db = client[db_name]
    predictions_col = db["predictions"]
    users_col = db["users"]
    mongo_available = True
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"MongoDB connection failed: {e}. Falling back to in-memory simulated database.")

# In-memory database simulation if MongoDB is offline
class MockCollection:
    def __init__(self, seed_demo_history=False, demo_username='farmer'):
        self.data = []
        if not seed_demo_history:
            return
        initial_crops = ["Rice", "Maize", "Banana", "Chickpea", "Cotton", "Orange", "Coffee"]
        now = datetime.datetime.now()
        for i in range(12):
            hist_time = now - datetime.timedelta(days=random.randint(1, 10), hours=random.randint(1, 12))
            crop_sample = random.choice(initial_crops)
            ph_val = round(random.uniform(5.2, 7.8), 1)
            if ph_val < 6.0:
                soil_en, soil_kn = 'Acidic Soil', 'ಆಮ್ಲೀಯ ಮಣ್ಣು'
            elif ph_val > 7.5:
                soil_en, soil_kn = 'Alkaline Soil', 'ಕ್ಷಾರೀಯ ಮಣ್ಣು'
            else:
                soil_en, soil_kn = 'Neutral Soil (Ideal)', 'ತಟಸ್ಥ ಮಣ್ಣು (ಆದರ್ಶ)'
            advice = crop_advisory.get(crop_sample, crop_advisory['Maize'])
            self.data.append({
                "_id": f"mock_id_{i}",
                "username": demo_username,
                "N": random.randint(30, 95),
                "P": random.randint(20, 80),
                "K": random.randint(20, 150),
                "ph": ph_val,
                # climate fields intentionally omitted (UI removed these inputs)
                "recommended_crop": crop_sample,
                "soil_type": soil_en,
                "soil_type_localized": {'en': soil_en, 'kn': soil_kn},
                "advice": {
                    'fertilizer': advice['fertilizer'],
                    'irrigation': advice['irrigation'],
                    'soil_improvement': advice['soil'],
                    'ideal_weather': advice.get('ideal_weather', {'en': 'Moderate weather', 'kn': 'ಮಧ್ಯಮ ಹವಾಮಾನ'}),
                    'estimated_income': advice.get('estimated_income', {'en': 'High yield potential', 'kn': 'ಹೆಚ್ಚಿನ ಇಳುವರಿ ಸಾಮರ್ಥ್ಯ'}),
                },
                "timestamp": hist_time.isoformat()
            })
            
    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = f"mock_{random.randint(100000, 999999)}"
        # Keep timestamp as string or datetime
        if isinstance(doc.get("timestamp"), datetime.datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
        self.data.append(doc)
        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return Result(doc["_id"])
        
    def find_one(self, filter=None):
        if not filter:
            return self.data[-1] if self.data else None
        for item in reversed(self.data):
            match = True
            for key, value in filter.items():
                if item.get(key) != value:
                    match = False
                    break
            if match:
                return item
        return None

    def count_documents(self, filter=None):
        if not filter:
            return len(self.data)
        return sum(1 for item in self.data if all(item.get(k) == v for k, v in filter.items()))

    def find(self, filter=None, sort=None, limit=0):
        results = [item for item in self.data if not filter or all(item.get(k) == v for k, v in filter.items())]
        results = sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)
        if limit > 0:
            results = results[:limit]
        return results

# --- Multilingual Agriculture Advice Database ---
crop_advisory = {
    'Rice': {
        'fertilizer': {
            'en': "Apply nitrogen-rich fertilizer (Urea) in 3 split doses: planting, tillering, and panicle initiation. Ensure adequate phosphorus (DAP) during early growth.",
            'kn': "ಸಾರಜನಕಯುಕ್ತ ರಸಗೊಬ್ಬರವನ್ನು (ಯೂರಿಯಾ) 3 ವಿಭಜಿತ ಕಂತುಗಳಲ್ಲಿ ಹಾಕಿ: ನಾಟಿ ಮಾಡುವಾಗ, ಕವಲೊಡೆಯುವಾಗ ಮತ್ತು ತೆನೆ ಮೂಡುವಾಗ. ಆರಂಭಿಕ ಬೆಳವಣಿಗೆಯಲ್ಲಿ ಸಾಕಷ್ಟು ರಂಜಕವನ್ನು (ಡಿಎಪಿ) ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ."
        },
        'irrigation': {
            'en': "Maintain a standing water level of 2-5 cm in the field during the transplanting and tillering stages. Drain the field 10-15 days before harvest.",
            'kn': "ನಾಟಿ ಮತ್ತು ಕವಲೊಡೆಯುವ ಹಂತಗಳಲ್ಲಿ ಗದ್ದೆಯಲ್ಲಿ 2-5 ಸೆಂ.ಮೀ ನೀರು ನಿಲ್ಲುವಂತೆ ನೋಡಿಕೊಳ್ಳಿ. ಕೊಯ್ಲಿಗೆ 10-15 ದಿನ ಮುಂಚಿತವಾಗಿ ಗದ್ದೆಯಿಂದ ನೀರನ್ನು ಹೊರಹಾಕಿ."
        },
        'soil': {
            'en': "Incorporate organic matter like compost or green manure (Dhaincha) to improve soil structure. Add lime if the soil pH is highly acidic.",
            'kn': "ಮಣ್ಣಿನ ರಚನೆ ಉತ್ತಮಗೊಳಿಸಲು ಕಾಂಪೋಸ್ಟ್ ಅಥವಾ ಹಸಿರೆಲೆ ಗೊಬ್ಬರವನ್ನು (ಡೈಂಚಾ) ಸೇರಿಸಿ. ಮಣ್ಣು ಹೆಚ್ಚು ಆಮ್ಲೀಯವಾಗಿದ್ದರೆ ಸುಣ್ಣವನ್ನು ಬಳಸಿ."
        },
        'ideal_weather': {
            'en': "Tropical hot & humid weather. Temp: 22°C - 35°C, high humidity (80-95%), high rainfall (150-300 mm) during growth.",
            'kn': "ಉಷ್ಣವಲಯದ ಬಿಸಿ ಮತ್ತು ತೇವ ವಾತಾವರಣ. ತಾಪಮಾನ: 22°C - 35°C, ಹೆಚ್ಚಿನ ಆರ್ದ್ರತೆ (80-95%), ಬೆಳವಣಿಗೆಯ ಸಮಯದಲ್ಲಿ ಹೆಚ್ಚಿನ ಮಳೆ (150-300 ಮಿಮೀ)."
        },
        'estimated_income': {
            'en': "₹45,000 - ₹60,000 per acre. Highly stable commercial and dietary demand across all local grain markets.",
            'kn': "ಎಕರೆಗೆ ₹45,000 - ₹60,000. ಎಲ್ಲಾ ಸ್ಥಳೀಯ ಧಾನ್ಯ ಮಾರುಕಟ್ಟೆಗಳಲ್ಲಿ ಅತ್ಯಂತ ಸ್ಥಿರವಾದ ವಾಣಿಜ್ಯ ಮತ್ತು ಆಹಾರ ಬೇಡಿಕೆ."
        }
    },
    'Maize': {
        'fertilizer': {
            'en': "Maize is a heavy feeder. Apply nitrogen (Urea) and zinc sulfate to prevent yellowing of leaves. Mix well with compost during soil preparation.",
            'kn': "ಮೆಕ್ಕೆಜೋಳಕ್ಕೆ ಹೆಚ್ಚಿನ ಪೋಷಕಾಂಶದ ಅವಶ್ಯಕತೆಯಿದೆ. ಎಲೆಗಳು ಹಳದಿಯಾಗುವುದನ್ನು ತಡೆಯಲು ಸಾರಜನಕ (ಯೂರಿಯಾ) ಮತ್ತು ಸತು ಸಲ್ಫೇಟ್ ಅನ್ನು ಅನ್ವಯಿಸಿ."
        },
        'irrigation': {
            'en': "Provide critical irrigation during the tasseling and silking stages. Avoid waterlogging as maize is highly sensitive to excess standing water.",
            'kn': "ತೆನೆ ಬಿಡುವ ಮತ್ತು ರೇಷ್ಮೆ ಹಂತಗಳಲ್ಲಿ ನೀರಾವರಿ ನೀಡುವುದು ಬಹಳ ಮುಖ್ಯ. ಮೆಕ್ಕೆಜೋಳವು ಹೆಚ್ಚುವರಿ ನೀರಿಗೆ ಸೂಕ್ಷ್ಮವಾಗಿರುವುದರಿಂದ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ."
        },
        'soil': {
            'en': "Ensure deep plowing to improve aeration and drainage. Add organic compost to maintain loose, well-draining loamy soil structure.",
            'kn': "ಮಣ್ಣಿನ ಗಾಳಿಯಾಡುವಿಕೆ ಮತ್ತು ಬಸನ ವ್ಯವಸ್ಥೆಯನ್ನು ಉತ್ತಮಗೊಳಿಸಲು ಆಳವಾಗಿ ಉಳಬೇಕು. ರಂಧ್ರಯುಕ್ತ ಮಣ್ಣಿಗಾಗಿ ಸಾವಯವ ಕಾಂಪೋಸ್ಟ್ ಸೇರಿಸಿ."
        },
        'ideal_weather': {
            'en': "Warm summer weather. Temp: 18°C - 32°C, moderate humidity (55-80%), moderate rainfall (60-150 mm).",
            'kn': "ಬೆಚ್ಚಗಿನ ಬೇಸಿಗೆ ವಾತಾವರಣ. ತಾಪಮಾನ: 18°C - 32°C, ಮಧ್ಯಮ ಆರ್ದ್ರತೆ (55-80%), ಮಧ್ಯಮ ಮಳೆ (60-150 ಮಿಮೀ)."
        },
        'estimated_income': {
            'en': "₹35,000 - ₹50,000 per acre. Lucrative crop for livestock feed production & food processing industries.",
            'kn': "ಎಕರೆಗೆ ₹35,000 - ₹50,000. ಜಾನುವಾರು ಆಹಾರ ತಯಾರಿಕೆ ಮತ್ತು ಆಹಾರ ಸಂಸ್ಕರಣಾ ಉದ್ಯಮಗಳಿಗೆ ಹೆಚ್ಚು ಲಾಭದಾಯಕ ಬೆಳೆ."
        }
    },
    'Chickpea': {
        'fertilizer': {
            'en': "Being a leguminous crop, chickpea fixes atmospheric nitrogen. Apply minimal nitrogen, but focus on phosphate fertilizers (SSP) to boost root nodules.",
            'kn': "ಕಡಲೆಯು ದ್ವಿದಳ ಧಾನ್ಯದ ಬೆಳೆಯಾಗಿದ್ದು, ಸಾರಜನಕವನ್ನು ಸ್ವತಃ ಸ್ಥಿರೀಕರಿಸುತ್ತದೆ. ಕಡಿಮೆ ಸಾರಜನಕ ಬಳಸಿ, ಬೇರುಗಳು ಬಲಿಷ್ಠಗೊಳ್ಳಲು ರಂಜಕ ಗೊಬ್ಬರಗಳ ಮೇಲೆ (ಎಸ್‌ಎಸ್‌ಪಿ) ಗಮನಹರಿಸಿ."
        },
        'irrigation': {
            'en': "Extremely drought-tolerant. Only 2 irrigations are generally needed: pre-flowering and pod development stages. Do not overwater.",
            'kn': "ಇದು ಬರ ನಿರೋಧಕ ಬೆಳೆಯಾಗಿದೆ. ಸಾಮಾನ್ಯವಾಗಿ ಹೂಬಿಡುವ ಮೊದಲು ಮತ್ತು ಕಾಯಿ ಕಟ್ಟುವ ಹಂತಗಳಲ್ಲಿ ಕೇವಲ 2 ನೀರಾವರಿಗಳು ಸಾಕು. ಅತಿಯಾಗಿ ನೀರು ಹಾಕಬೇಡಿ."
        },
        'soil': {
            'en': "Prefers light-weight, well-drained loamy soils. Add gypsum if soil sulfur levels are low to increase nodulation and seed yield.",
            'kn': "ಹಗುರವಾದ ಮತ್ತು ಚೆನ್ನಾಗಿ ನೀರು ಬಸಿದುಹೋಗುವ ಮರಳು ಮಿಶ್ರಿತ ಮಣ್ಣು ಸೂಕ್ತ. ಬೇರಿನ ಗಂಟುಗಳು ಹೆಚ್ಚಲು ಮತ್ತು ಇಳುವರಿ ಹೆಚ್ಚಿಸಲು ಜಿಪ್ಸಮ್ ಬಳಸಿ."
        },
        'ideal_weather': {
            'en': "Cool, dry winter climate (Rabi). Temp: 15°C - 25°C, low humidity (15-40%), low rainfall (25-60 mm).",
            'kn': "ತಂಪಾದ, ಒಣ ಚಳಿಗಾಲದ ವಾತಾವರಣ (ರಬಿ). ತಾಪಮಾನ: 15°C - 25°C, ಕಡಿಮೆ ಆರ್ದ್ರತೆ (15-40%), ಕಡಿಮೆ ಮಳೆ (25-60 ಮಿಮೀ)."
        },
        'estimated_income': {
            'en': "₹40,000 - ₹55,000 per acre. Good returns due to low cultivation cost and strong domestic protein demand.",
            'kn': "ಎಕರೆಗೆ ₹40,000 - ₹55,000. ಕಡಿಮೆ ಸಾಗುವಳಿ ವೆಚ್ಚ ಮತ್ತು ಬಲವಾದ ಸ್ಥಳೀಯ ಪ್ರೊಟೀನ್ ಬೇಡಿಕೆಯಿಂದಾಗಿ ಉತ್ತಮ ಆದಾಯ."
        }
    },
    'Cotton': {
        'fertilizer': {
            'en': "Apply balanced NPK. High nitrogen is required during vegetative growth, and potassium is crucial during boll formation to ensure fiber quality.",
            'kn': "ಸಮತೋಲಿತ NPK ಬಳಸಿ. ಬೆಳವಣಿಗೆಯ ಹಂತದಲ್ಲಿ ಹೆಚ್ಚಿನ ಸಾರಜನಕ ಮತ್ತು ಕಾಯಿ ಕಟ್ಟುವ ಹಂತದಲ್ಲಿ ನಾರಿನ ಗುಣಮಟ್ಟಕ್ಕಾಗಿ ಪೊಟ್ಯಾಸಿಯಮ್ ಅತ್ಯಗತ್ಯ."
        },
        'irrigation': {
            'en': "Irrigate at critical growth phases: flowering and boll development. Drip irrigation is highly recommended to conserve water and control weeds.",
            'kn': "ಹೂಬಿಡುವ ಮತ್ತು ಕಾಯಿ ಬೆಳೆಯುವ ನಿರ್ಣಾಯಕ ಹಂತಗಳಲ್ಲಿ ನೀರುಣಿಸಿ. ನೀರು ಉಳಿಸಲು ಮತ್ತು ಕಳೆ ನಿಯಂತ್ರಿಸಲು ಹನಿ ನೀರಾವರಿ ಅತ್ಯಂತ ಸೂಕ್ತವಾಗಿದೆ."
        },
        'soil': {
            'en': "Deep black soils (Regur) are ideal as they retain moisture. Ensure good drainage to prevent root rot. Add farmyard manure to clayey soil.",
            'kn': "ತೇವಾಂಶ ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವ ಆಳವಾದ ಕಪ್ಪು ಮಣ್ಣು (ರೆಗೂರ್) ಸೂಕ್ತ. ಬೇರು ಕೊಳೆತ ತಡೆಯಲು ಬಸನ ವ್ಯವಸ್ಥೆ ಇರಲಿ. ಜೇಡಿಮಣ್ಣಿಗೆ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಸೇರಿಸಿ."
        },
        'ideal_weather': {
            'en': "Sunny and warm. Temp: 22°C - 35°C, moderate humidity (40-75%), rainfall 60-110 mm with dry sun during picking.",
            'kn': "ಬಿಸಿಲು ಮತ್ತು ಬೆಚ್ಚಗಿನ ಹವೆ. ತಾಪಮಾನ: 22°C - 35°C, ಮಧ್ಯಮ ಆರ್ದ್ರತೆ (40-75%), ಮಳೆ 60-110 ಮಿಮೀ ಕೊಯ್ಲು ಮಾಡುವಾಗ ಒಣ ಹವೆ ಇರಬೇಕು."
        },
        'estimated_income': {
            'en': "₹60,000 - ₹85,000 per acre. Prime commercial cash crop with excellent textile market buy-back options.",
            'kn': "ಎಕರೆಗೆ ₹60,000 - ₹85,000. ಜವಳಿ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಉತ್ತಮ ಬೇಡಿಕೆಯಿರುವ ಅತ್ಯುತ್ತಮ ವಾಣಿಜ್ಯ ನಗದು ಬೆಳೆ."
        }
    },
    'Coconut': {
        'fertilizer': {
            'en': "Provide abundant Potassium (MOP) and organic manure annually. Supplement with Borax (50g per palm) to prevent button shedding and crown bend.",
            'kn': "ಪ್ರತಿ ವರ್ಷ ಹೇರಳವಾಗಿ ಪೊಟ್ಯಾಸಿಯಮ್ (ಎಂಒಪಿ) ಮತ್ತು ಸಾವಯವ ಗೊಬ್ಬರವನ್ನು ನೀಡಿ. ಎಳನೀರು ಉದುರುವುದನ್ನು ತಡೆಯಲು ಬೊರಾಕ್ಸ್ (ಪ್ರತಿ ಮರಕ್ಕೆ 50 ಗ್ರಾಂ) ನೀಡಿ."
        },
        'irrigation': {
            'en': "Requires regular watering. Drip irrigation near the root basin is highly efficient. In dry summers, irrigate once every 4-6 days.",
            'kn': "ನಿಯಮಿತವಾಗಿ ನೀರು ಹಾಯಿಸಬೇಕು. ಬೇರಿನ ಬಳಿ ಹನಿ ನೀರಾವರಿ ಮಾಡುವುದು ಹೆಚ್ಚು ಪರಿಣಾಮಕಾರಿ. ಒಣ ಬೇಸಿಗೆಯಲ್ಲಿ ಪ್ರತಿ 4-6 ದಿನಗಳಿಗೊಮ್ಮೆ ನೀರು ಹಾಯಿಸಿ."
        },
        'soil': {
            'en': "Grows best in sandy loams or alluvial soils. Add river sand and organic compost to heavy clay soils to loosen up the compaction.",
            'kn': "ಮರಳು ಮಿಶ್ರಿತ ಮರಳು ಅಥವಾ ಮೆಕ್ಕಲು ಮಣ್ಣಿನಲ್ಲಿ ಉತ್ತಮವಾಗಿ ಬೆಳೆಯುತ್ತದೆ. ಜೇಡಿ ಮಣ್ಣನ್ನು ಸಡಿಲಗೊಳಿಸಲು ನದಿ ಮರಳು ಮತ್ತು ಸಾವಯವ ಗೊಬ್ಬರವನ್ನು ಸೇರಿಸಿ."
        },
        'ideal_weather': {
            'en': "Coastal humid tropical climate. Temp: 24°C - 35°C, high humidity (75-95%), rainfall 120-260 mm evenly distributed.",
            'kn': "ಕರಾವಳಿ ತೇವ ಉಷ್ಣವಲಯದ ವಾತಾವರಣ. ತಾಪಮಾನ: 24°C - 35°C, ಹೆಚ್ಚಿನ ಆರ್ದ್ರತೆ (75-95%), ಸಮನಾಗಿ ಹರಡಿದ 120-260 ಮಿಮೀ ಮಳೆ."
        },
        'estimated_income': {
            'en': "₹1,20,000 - ₹1,80,000 per acre annually. Long-term stable recurring monthly returns from copra, husk and fresh coconuts.",
            'kn': "ವಾರ್ಷಿಕ ಎಕರೆಗೆ ₹1,20,000 - ₹1,80,000. ಕೊಬ್ಬರಿ, ಸಿಪ್ಪೆ ಮತ್ತು ಎಳನೀರಿನಿಂದ ದೀರ್ಘಾವಧಿಯ ಸ್ಥಿರ ಮಾಸಿಕ ಆದಾಯ."
        }
    },
    'Coffee': {
        'fertilizer': {
            'en': "Coffee needs regular doses of balanced NPK. Apply organic compost along with micro-nutrients like Zinc and Magnesium to enhance coffee bean quality.",
            'kn': "ಕಾಫಿಗೆ ನಿಯಮಿತ ಪ್ರಮಾಣದ ಸಮತೋಲಿತ NPK ಅಗತ್ಯವಿದೆ. ಕಾಫಿ ಬೀಜಗಳ ಗುಣಮಟ್ಟವನ್ನು ಹೆಚ್ಚಿಸಲು ಸತು ಮತ್ತು ಮೆಗ್ನೀಸಿಯಮ್‌ನಂತಹ ಸೂಕ್ಷ್ಮ ಪೋಷಕಾಂಶಗಳೊಂದಿಗೆ ಸಾವಯವ ಗೊಬ್ಬರ ಬಳಸಿ."
        },
        'irrigation': {
            'en': "Usually rain-fed in hills. Sprinkler irrigation is critical in March-April to trigger uniform flowering (popularly called blossom showers).",
            'kn': "ಸಾಮಾನ್ಯವಾಗಿ ಬೆಟ್ಟಗಳಲ್ಲಿ ಮಳೆಯಾಶ್ರಿತವಾಗಿರುತ್ತದೆ. ಮಾರ್ಚ್-ಏಪ್ರಿಲ್‌ನಲ್ಲಿ ಸಮನಾದ ಹೂಬಿಡುವಿಕೆಯನ್ನು ಪ್ರಚೋದಿಸಲು ಸ್ಪ್ರಿಂಕ್ಲರ್ ನೀರಾವರಿ ಅತ್ಯಗತ್ಯ."
        },
        'soil': {
            'en': "Requires deep, acidic (pH 5.0-6.0), rich organic soils under shade. Mulch soil around coffee bushes with leaves to conserve moisture.",
            'kn': "ನೆರಳಿನಲ್ಲಿ ಬೆಳೆಯಲು ಆಳವಾದ, ಆಮ್ಲೀಯ (ಪಿಎಚ್ 5.0-6.0) ಮತ್ತು ಸಮೃದ್ಧ ಸಾವಯವ ಮಣ್ಣು ಬೇಕು. ತೇವಾಂಶ ಉಳಿಸಲು ಎಲೆಗಳಿಂದ ಹೊದಿಕೆ (ಮಲ್ಚಿಂಗ್) ಮಾಡಿ."
        },
        'ideal_weather': {
            'en': "Cool hill climate under shade tree canopy. Temp: 15°C - 26°C, humidity (60-90%), annual rainfall 130-240 mm.",
            'kn': "ನೆರಳಿನ ಮರಗಳ ಅಡಿಯಲ್ಲಿ ತಂಪಾದ ಗುಡ್ಡಗಾಡು ವಾತಾವರಣ. ತಾಪಮಾನ: 15°C - 26°C, ಆರ್ದ್ರತೆ (60-90%), ವಾರ್ಷಿಕ ಮಳೆ 130-240 ಮಿಮೀ."
        },
        'estimated_income': {
            'en': "₹1,50,000 - ₹2,50,000 per acre. Superb international export prospects offering premium global trade values.",
            'kn': "ಎಕರೆಗೆ ₹1,50,000 - ₹2,50,000. ಜಾಗತಿಕ ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಉತ್ತಮ ಬೆಲೆಯಿರುವ ಅತ್ಯುತ್ತಮ ಅಂತರರಾಷ್ಟ್ರೀಯ ರಫ್ತು ಅವಕಾಶಗಳು."
        }
    },
    'Banana': {
        'fertilizer': {
            'en': "Extremely heavy nutrient feeder. Apply nitrogen and high potassium (MOP) in 5-6 split applications throughout the growth cycle to get heavy bunches.",
            'kn': "ಇದು ಅತಿ ಹೆಚ್ಚಿನ ಪೋಷಕಾಂಶಗಳನ್ನು ಹೀರುವ ಬೆಳೆಯಾಗಿದೆ. ದೊಡ್ಡ ಗೊನೆಗಳನ್ನು ಪಡೆಯಲು ಬೆಳವಣಿಗೆಯ ಅವಧಿಯಲ್ಲಿ 5-6 ಕಂತುಗಳಲ್ಲಿ ಸಾರಜನಕ ಮತ್ತು ಪೊಟ್ಯಾಶ್ ನೀಡಿ."
        },
        'irrigation': {
            'en': "Requires substantial water. Soil should always remain moist. Drip irrigation at the rate of 15-20 liters per plant daily is highly recommended.",
            'kn': "ಹೆಚ್ಚಿನ ಪ್ರಮಾಣದ ನೀರು ಬೇಕಾಗುತ್ತದೆ. ಮಣ್ಣು ಯಾವಾಗಲೂ ತೇವವಾಗಿರಬೇಕು. ದಿನಕ್ಕೆ ಪ್ರತಿ ಗಿಡಕ್ಕೆ 15-20 ಲೀಟರ್ ಹನಿ ನೀರಾವರಿ ಮಾಡಲು ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ."
        },
        'soil': {
            'en': "Requires rich, deep, well-draining loamy soil with neutral pH. Incorporate large quantities of poultry manure or decomposed farmyard manure.",
            'kn': "ತಟಸ್ಥ ಪಿಎಚ್ ಹೊಂದಿರುವ ಸಮೃದ್ಧ, ಆಳವಾದ, ಸುಲಭವಾಗಿ ನೀರು ಹರಿಯುವ ಮಣ್ಣು ಸೂಕ್ತ. ಕೋಳಿ ಗೊಬ್ಬರ ಅಥವಾ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರವನ್ನು ಹೆಚ್ಚಿನ ಪ್ರಮಾಣದಲ್ಲಿ ಸೇರಿಸಿ."
        },
        'ideal_weather': {
            'en': "Warm, moist tropical climate. Temp: 20°C - 35°C, high humidity (70-92%), rainfall 100-250 mm. Protection from high wind is vital.",
            'kn': "ಬೆಚ್ಚಗಿನ, ತೇವ ಉಷ್ಣವಲಯದ ವಾತಾವರಣ. ತಾಪಮಾನ: 20°C - 35°C, ಹೆಚ್ಚಿನ ಆರ್ದ್ರತೆ (70-92%), ಮಳೆ 100-250 ಮಿಮೀ. ಬಲವಾದ ಗಾಳಿಯಿಂದ ರಕ್ಷಣೆ ಅತ್ಯಗತ್ಯ."
        },
        'estimated_income': {
            'en': "₹1,00,000 - ₹1,60,000 per acre. Fast crop cycle (11-13 months) with constant high-volume domestic consumer demands.",
            'kn': "ಎಕರೆಗೆ ₹1,00,000 - ₹1,60,000. ತ್ವರಿತ ಬೆಳೆ ಚಕ್ರ (11-13 ತಿಂಗಳು) ಮತ್ತು ದೇಶೀಯ ಗ್ರಾಹಕರಲ್ಲಿ ನಿರಂತರ ಭಾರಿ ಬೇಡಿಕೆ."
        }
    },
    'Mango': {
        'fertilizer': {
            'en': "For mature trees, apply 1 kg Nitrogen, 1 kg Phosphorus, and 1.5 kg Potassium per tree annually. Limit fertilizers during the flowering season.",
            'kn': "ಬಲಿತ ಮರಗಳಿಗೆ ವಾರ್ಷಿಕವಾಗಿ 1 ಕೆಜಿ ಸಾರಜನಕ, 1 ಕೆಜಿ ರಂಜಕ ಮತ್ತು 1.5 ಕೆಜಿ ಪೊಟ್ಯಾಸಿಯಮ್ ನೀಡಿ. ಹೂಬಿಡುವ ಹಂತದಲ್ಲಿ ರಸಗೊಬ್ಬರಗಳ ಬಳಕೆಯನ್ನು ಮಿತಿಗೊಳಿಸಿ."
        },
        'irrigation': {
            'en': "Irrigate young plants regularly. For mature trees, irrigate during fruit development (double-ring method), but stop watering 2 months before flowering.",
            'kn': "ಚಿಕ್ಕ ಗಿಡಗಳಿಗೆ ನಿಯಮಿತವಾಗಿ ನೀರು ಹಾಯಿಸಿ. ದೊಡ್ಡ ಮರಗಳಿಗೆ ಕಾಯಿ ಬೆಳೆಯುವಾಗ ನೀರುಣಿಸಿ, ಆದರೆ ಹೂ ಬಿಡುವುದಕ್ಕೆ 2 ತಿಂಗಳು ಮುಂಚಿತವಾಗಿ ನೀರು ನಿಲ್ಲಿಸಿ."
        },
        'soil': {
            'en': "Thrives in alluvial and deep well-drained soils. Avoid waterlogging around root trunk. Add organic compost in trenches around the canopy drip line.",
            'kn': "ಮೆಕ್ಕಲು ಮತ್ತು ಆಳವಾದ ನೀರು ಬಸಿಯುವ ಮಣ್ಣಿನಲ್ಲಿ ಚೆನ್ನಾಗಿ ಬೆಳೆಯುತ್ತದೆ. ಬೇರಿನ ಬಳಿ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ. ರೆಂಬೆಗಳ ತುದಿಯ ಕೆಳಗೆ ಕಾಂಪೋಸ್ಟ್ ಹಾಕಿ."
        },
        'ideal_weather': {
            'en': "Warm tropical conditions. Temp: 24°C - 40°C, moderate humidity (45-75%), low rainfall (40-100 mm) during dry flower induction cycles.",
            'kn': "ಬೆಚ್ಚಗಿನ ಉಷ್ಣವಲಯದ ಹವಾಮಾನ. ತಾಪಮಾನ: 24°C - 40°C, ಮಧ್ಯಮ ಆರ್ದ್ರತೆ (45-75%), ಹೂಬಿಡುವ ಸಮಯದಲ್ಲಿ ಶುಷ್ಕ ಹವೆ ಮತ್ತು ಕಡಿಮೆ ಮಳೆ (40-100 ಮಿಮೀ)."
        },
        'estimated_income': {
            'en': "₹90,000 - ₹1,40,000 per acre seasonal. Higher value potential for premium varieties (e.g. Alphonso) in export lanes.",
            'kn': "ಋತುಮಾನಕ್ಕೆ ಎಕರೆಗೆ ₹90,000 - ₹1,40,000. ರಫ್ತು ಮಾರುಕಟ್ಟೆಗಳಲ್ಲಿ ಪ್ರೀಮಿಯಂ ತಳಿಗಳಿಗೆ (ಉದಾ. ಆಲ್ಫಾನ್ಸೋ) ಅತ್ಯಧಿಕ ಬೆಲೆ ಇರುತ್ತದೆ."
        }
    },
    'Grapes': {
        'fertilizer': {
            'en': "Apply balanced NPK, with high potassium during berry expansion. Supplement with magnesium sulfate to prevent vine yellowing and shoot weakness.",
            'kn': "ಸಮತೋಲಿತ NPK ಬಳಸಿ, ದ್ರಾಕ್ಷಿ ಹಣ್ಣುಗಳು ಬೆಳೆಯುವಾಗ ಹೆಚ್ಚಿನ ಪೊಟ್ಯಾಸಿಯಮ್ ನೀಡಿ. ಬಳ್ಳಿಯು ಹಳದಿಯಾಗುವುದನ್ನು ತಡೆಯಲು ಮೆಗ್ನೀಸಿಯಮ್ ಸಲ್ಫೇಟ್ ಸೇರಿಸಿ."
        },
        'irrigation': {
            'en': "Highly responsive to drip irrigation. Reduce water supply during the ripening stage to increase sugar content and improve fruit color/flavor.",
            'kn': "ಹನಿ ನೀರಾವರಿಗೆ ಇದು ಉತ್ತಮವಾಗಿ ಸ್ಪಂದಿಸುತ್ತದೆ. ದ್ರಾಕ್ಷಿಯಲ್ಲಿ ಸಕ್ಕರೆ ಅಂಶ ಮತ್ತು ಹಣ್ಣಿನ ಬಣ್ಣ ಹೆಚ್ಚಿಸಲು ಹಣ್ಣು ಮಾಗುವ ಹಂತದಲ್ಲಿ ನೀರನ್ನು ಕಡಿಮೆ ಮಾಡಿ."
        },
        'soil': {
            'en': "Requires gravelly, well-draining, loose soils. Incorporate decomposed organic compost and sand to enhance permeability and root aeration.",
            'kn': "ಮೆರಳು ಮಿಶ್ರಿತ, ಸಡಿಲವಾದ ಮತ್ತು ನೀರು ಸರಾಗವಾಗಿ ಹರಿಯುವ ಮಣ್ಣು ಸೂಕ್ತ. ಬೇರಿನ ಉಸಿರಾಟಕ್ಕೆ ಸಾವಯವ ಗೊಬ್ಬರ ಮತ್ತು ಮರಳನ್ನು ಸೇರಿಸಿ."
        },
        'ideal_weather': {
            'en': "Mediterranean warm climate with dry summers and cool nights. Temp: 15°C - 33°C, low humidity (40-70%), low rain (20-60 mm).",
            'kn': "ಶುಷ್ಕ ಬೇಸಿಗೆ ಮತ್ತು ತಂಪಾದ ರಾತ್ರಿಗಳಿರುವ ಹಿತಕರವಾದ ವಾತಾವರಣ. ತಾಪಮಾನ: 15°C - 33°C, ಕಡಿಮೆ ಆರ್ದ್ರತೆ (40-70%), ಕಡಿಮೆ ಮಳೆ (20-60 ಮಿಮೀ)."
        },
        'estimated_income': {
            'en': "₹1,80,000 - ₹3,00,000 per acre. Excellent profit margins for high-grade table grapes and winery processing supplies.",
            'kn': "ಎಕರೆಗೆ ₹1,80,000 - ₹3,00,000. ಉತ್ತಮ ಗುಣಮಟ್ಟದ ತಿನ್ನುವ ದ್ರಾಕ್ಷಿಗಳು ಮತ್ತು ವೈನರಿ ಸರಬರಾಜುಗಳಿಗೆ ಅತ್ಯುತ್ತಮ ಲಾಭದ ಪ್ರಮಾಣ."
        }
    },
    'Watermelon': {
        'fertilizer': {
            'en': "Apply high nitrogen in early stages for vine growth. Shift to phosphorus and potassium-rich fertilizers as soon as flowering begins to get sweet fruit.",
            'kn': "ಬಳ್ಳಿಯ ಬೆಳವಣಿಗೆಗಾಗಿ ಆರಂಭಿಕ ಹಂತದಲ್ಲಿ ಹೆಚ್ಚಿನ ಸಾರಜನಕ ನೀಡಿ. ಸಿಹಿಯಾದ ಹಣ್ಣುಗಳನ್ನು ಪಡೆಯಲು ಹೂಬಿಡುವಿಕೆ ಪ್ರಾರಂಭವಾದ ತಕ್ಷಣ ರಂಜಕ ಮತ್ತು ಪೊಟ್ಯಾಶ್ ನೀಡಿ."
        },
        'irrigation': {
            'en': "Provide consistent watering in early stages. Reduce water near harvesting to prevent fruit cracking and to maximize the sugar concentration.",
            'kn': "ಆರಂಭಿಕ ಹಂತಗಳಲ್ಲಿ ಸ್ಥಿರವಾಗಿ ನೀರುಣಿಸಿ. ಹಣ್ಣು ಒಡೆಯುವುದನ್ನು ತಡೆಯಲು ಮತ್ತು ಹಣ್ಣಿನ ಸಿಹಿ ಹೆಚ್ಚಿಸಲು ಕೊಯ್ಲಿಗೆ ಹತ್ತಿರವಿರುವಾಗ ನೀರನ್ನು ಕಡಿಮೆ ಮಾಡಿ."
        },
        'soil': {
            'en': "Thrives in warm, sandy loam soils that heat up quickly. Incorporate well-rotted cow manure to boost soil organic content and heat retention.",
            'kn': "ಬೇಗನೆ ಬಿಸಿಯಾಗುವ ಮರಳು ಮಿಶ್ರಿತ ಮಣ್ಣಿನಲ್ಲಿ ಉತ್ತಮವಾಗಿ ಬೆಳೆಯುತ್ತದೆ. ಮಣ್ಣಿನ ತೇವಾಂಶ ಮತ್ತು ಉಷ್ಣತೆ ಕಾಪಾಡಲು ಚೆನ್ನಾಗಿ ಕೊಳೆತ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಸೇರಿಸಿ."
        },
        'ideal_weather': {
            'en': "Dry, hot and highly sunny summer climate. Temp: 22°C - 38°C, humidity (45-80%), low rainfall (40-95 mm). Requires ample direct sunlight.",
            'kn': "ಶುಷ್ಕ, ಬಿಸಿ ಮತ್ತು ಅತ್ಯಂತ ಬಿಸಿಲಿನ ಬೇಸಿಗೆ ವಾತಾವರಣ. ತಾಪಮಾನ: 22°C - 38°C, ಆರ್ದ್ರತೆ (45-80%), ಕಡಿಮೆ ಮಳೆ (40-95 ಮಿಮೀ). ಹೆಚ್ಚಿನ ಬಿಸಿಲು ಬೇಕು."
        },
        'estimated_income': {
            'en': "₹50,000 - ₹75,000 per acre. Short 3-month harvest turnaround makes it a wonderful dry-season cash flow generator.",
            'kn': "ಎಕರೆಗೆ ₹50,000 - ₹75,000. ಕೇವಲ 3 ತಿಂಗಳ ತ್ವರಿತ ಕೊಯ್ಲು ಚಕ್ರದಿಂದಾಗಿ ಒಣ ಹಂಗಾಮಿನಲ್ಲಿ ಅತ್ಯುತ್ತಮ ಆದಾಯ ನೀಡುತ್ತದೆ."
        }
    },
    'Orange': {
        'fertilizer': {
            'en': "Apply nitrogen-rich fertilizer along with micronutrients like Zinc, Iron, and Manganese. Spraying liquid zinc prevents leaf mottling.",
            'kn': "ಸಾರಜನಕಯುಕ್ತ ಗೊಬ್ಬರದೊಂದಿಗೆ ಸತು, ಕಬ್ಬಿಣ ಮತ್ತು ಮ್ಯಾಂಗನೀಸ್‌ ಸೂಕ್ಷ್ಮ ಪೋಷಕಾಂಶಗಳನ್ನು ನೀಡಿ. ಸತುವಿನ ದ್ರಾವಣವನ್ನು ಸಿಂಪಡಿಸುವುದರಿಂದ ಎಲೆಗಳು ಮಚ್ಚೆಯಾಗುವುದನ್ನು ತಡೆಯಬಹುದು."
        },
        'irrigation': {
            'en': "Citrus trees need regular irrigation to prevent fruit drop. Avoid micro-irrigation directly contacting the trunk to prevent collar rot disease.",
            'kn': "ಕಿತ್ತಳೆ ಹಣ್ಣುಗಳು ಉದುರುವುದನ್ನು ತಡೆಯಲು ನಿಯಮಿತವಾಗಿ ನೀರು ಹಾಯಿಸಿ. ಗಿಡದ ಬುಡ ಕೊಳೆಯುವ ರೋಗ ತಡೆಯಲು ನೀರು ನೇರವಾಗಿ ಕಾಂಡಕ್ಕೆ ತಾಕದಂತೆ ನೋಡಿಕೊಳ್ಳಿ."
        },
        'soil': {
            'en': "Prefers deep, rich, sandy loams with neutral pH (6.0-7.0). Ensure excellent drainage. Mix compost and vermicompost to enrich the planting pit.",
            'kn': "ತಟಸ್ಥ ಪಿಎಚ್ (6.0-7.0) ಹೊಂದಿರುವ ಆಳವಾದ ಮರಳು ಮಿಶ್ರಿತ ಮಣ್ಣು ಉತ್ತಮ. ಅತ್ಯುತ್ತಮ ಬಸನ ಇರಲಿ. ಹೊಂಡಕ್ಕೆ ಕಾಂಪೋಸ್ಟ್ ಮತ್ತು ಎರೆಗೊಬ್ಬರವನ್ನು ಹಾಕಿ."
        },
        'ideal_weather': {
            'en': "Subtropical warm/humid climate. Temp: 16°C - 35°C, humidity (60-85%), rainfall 60-130 mm. Dry periods trigger uniform flowering buds.",
            'kn': "ಉಪೋಷ್ಣವಲಯದ ಬೆಚ್ಚಗಿನ ಮತ್ತು ತೇವ ಹವಾಮಾನ. ತಾಪಮಾನ: 16°C - 35°C, ಆರ್ದ್ರತೆ (60-85%), ಮಳೆ 60-130 ಮಿಮೀ. ಒಣ ಹವೆ ಹೂಮೊಗ್ಗು ಬಿಡಲು ಸಹಕಾರಿ."
        },
        'estimated_income': {
            'en': "₹1,10,000 - ₹1,60,000 per acre. Heavy recurring demands from commercial beverage plants and retail fruit markets.",
            'kn': "ಎಕರೆಗೆ ₹1,10,000 - ₹1,60,000. ಪಾನೀಯ ತಯಾರಿಕಾ ಕಂಪನಿಗಳು ಮತ್ತು ತಾಜಾ ಹಣ್ಣಿನ ಮಾರುಕಟ್ಟೆಗಳಲ್ಲಿ ಭಾರಿ ನಿರಂತರ ಬೇಡಿಕೆ."
        }
    },
    'Papaya': {
        'fertilizer': {
            'en': "Papaya is a fast-growing, heavy-yielding tree. Apply balanced NPK every two months, and add Boron to prevent bumpy, misshapen fruits.",
            'kn': "ಪಪ್ಪಾಯಿಯು ವೇಗವಾಗಿ ಬೆಳೆಯುವ ಮತ್ತು ಹೆಚ್ಚು ಇಳುವರಿ ನೀಡುವ ಗಿಡವಾಗಿದೆ. ಪ್ರತಿ ಎರಡು ತಿಂಗಳಿಗೊಮ್ಮೆ ಸಮತೋಲಿತ NPK ನೀಡಿ, ಕಾಯಿ ಡೊಂಕಾಗುವುದನ್ನು ತಡೆಯಲು ಬೋರಾನ್ ನೀಡಿ."
        },
        'irrigation': {
            'en': "Requires adequate water, but cannot tolerate waterlogging even for a day. Always plant on a raised bed with slope drainage to run off rain.",
            'kn': "ಸಾಕಷ್ಟು ನೀರು ಬೇಕು, ಆದರೆ ಒಂದು ದಿನವೂ ನೀರು ನಿಲ್ಲಬಾರದು. ಮಳೆ ನೀರು ಹರಿದುಹೋಗಲು ಯಾವಾಗಲೂ ಮಣ್ಣಿನ ಏರು ಮಡಿಗಳ ಮೇಲೆ ಗಿಡವನ್ನು ನೆಡಬೇಕು."
        },
        'soil': {
            'en': "Thrives in rich alluvial or sandy loam soils. Add leaf mold, compost, and composted wood chips to the base to improve organic content.",
            'kn': "ಸಮೃದ್ಧವಾದ ಮೆಕ್ಕಲು ಅಥವಾ ಮರಳು ಮಿಶ್ರಿತ ಮಣ್ಣಿನಲ್ಲಿ ಬೆಳೆಯುತ್ತದೆ. ಸಾವಯವ ಅಂಶ ಹೆಚ್ಚಿಸಲು ಬುಡಕ್ಕೆ ಒಣ ಎಲೆಗಳು ಮತ್ತು ಕಂಪೋಸ್ಟ್ ಅನ್ನು ಹಾಕಿ."
        },
        'ideal_weather': {
            'en': "Warm tropical year-round conditions. Temp: 20°C - 36°C, humidity (60-85%), rainfall 60-160 mm. Avoid frost-prone and heavy wind zones.",
            'kn': "ವರ್ಷವಿಡೀ ಬೆಚ್ಚಗಿರುವ ಉಷ್ಣವಲಯದ ಹವಾಮಾನ. ತಾಪಮಾನ: 20°C - 36°C, ಆರ್ದ್ರತೆ (60-85%), ಮಳೆ 60-160 ಮಿಮೀ. ಮಂಜು ಮತ್ತು ಅತಿ ಗಾಳಿಯಿಂದ ರಕ್ಷಿಸಿ."
        },
        'estimated_income': {
            'en': "₹80,000 - ₹1,30,000 per acre. Continuous weekly yields beginning within 9-10 months of sapling plantation.",
            'kn': "ಎಕರೆಗೆ ₹80,000 - ₹1,30,000. ಸಸಿಗಳನ್ನು ನೆಟ್ಟ 9-10 ತಿಂಗಳುಗಳಲ್ಲಿ ನಿರಂತರ ವಾರಕ್ಕೊಮ್ಮೆ ಇಳುವರಿ ಮತ್ತು ಉತ್ತಮ ಆದಾಯ ನೀಡುತ್ತದೆ."
        }
    }
}

if not mongo_available:
    predictions_col = MockCollection(seed_demo_history=True)
    users_col = MockCollection()


def _seed_default_users():
    if users_col is None:
        return
    if users_col.count_documents({}) == 0:
        users_col.insert_one({
            'username': 'admin',
            'email': 'admin@agrosmart.ai',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'created_at': datetime.datetime.now().isoformat()
        })
        users_col.insert_one({
            'username': 'farmer',
            'email': 'farmer@agrosmart.ai',
            'password_hash': generate_password_hash('farmer123'),
            'role': 'farmer',
            'created_at': datetime.datetime.now().isoformat()
        })


_seed_default_users()

# Standard agronomic rules in case ML model is not loaded
def fallback_recommendation(n, p, k, temp, humidity, ph, rainfall):
    # scientifically reasonable selection based on basic filters
    if rainfall > 180 and humidity > 75:
        return 'Rice'
    elif k > 110:
        if humidity > 75:
            return 'Coconut'
        else:
            return 'Banana'
    elif temp < 22 and humidity < 40:
        return 'Chickpea'
    elif rainfall > 120 and temp < 28:
        return 'Coffee'
    elif ph < 6.0 and rainfall > 70:
        return 'Grapes'
    elif temp > 28 and rainfall < 90:
        return 'Mango'
    elif rainfall < 95 and temp > 22 and humidity > 45:
        return 'Watermelon'
    elif p > 45 and k > 60:
        return 'Papaya'
    elif n > 70:
        return 'Cotton'
    elif ph >= 6.0 and ph <= 7.5:
        return 'Orange'
    else:
        return 'Maize'

# --- Weather Database / Simulator ---
# Returns realistic parameters based on city search. Highly robust fallback generator.
weather_cities = {
    'bangalore': {
        'names': {'en': 'Bengaluru', 'kn': 'ಬೆಂಗಳೂರು'},
        'temp_base': 26.5, 'humidity_base': 65, 'desc': {'en': 'Scattered Clouds', 'kn': 'ಚದುರಿದ ಮೋಡಗಳು'}, 'wind': 12, 'rain': 10
    },
    'mysore': {
        'names': {'en': 'Mysuru', 'kn': 'ಮೈಸೂರು'},
        'temp_base': 28.0, 'humidity_base': 60, 'desc': {'en': 'Sunny & Clear', 'kn': 'ಬಿಸಿಲಿನ ವಾತಾವರಣ'}, 'wind': 10, 'rain': 5
    },
    'hubli': {
        'names': {'en': 'Hubballi-Dharwad', 'kn': 'ಹುಬ್ಬಳ್ಳಿ-ಧಾರವಾಡ'},
        'temp_base': 31.0, 'humidity_base': 50, 'desc': {'en': 'Warm and Dry', 'kn': 'ಬಿಸಿ ಮತ್ತು ಒಣ ಹವೆ'}, 'wind': 14, 'rain': 2
    },
    'mangalore': {
        'names': {'en': 'Mangaluru', 'kn': 'ಮಂಗಳೂರು'},
        'temp_base': 30.5, 'humidity_base': 85, 'desc': {'en': 'Humid with Light Showers', 'kn': 'ಸಣ್ಣ ಮಳೆಯೊಂದಿಗೆ ಆರ್ದ್ರತೆ'}, 'wind': 18, 'rain': 75
    },
    'belgaum': {
        'names': {'en': 'Belagavi', 'kn': 'ಬೆಳಗಾವಿ'},
        'temp_base': 25.0, 'humidity_base': 70, 'desc': {'en': 'Pleasant Breeze', 'kn': 'ಹ್ಲಾದಕರ ತಂಗಾಳಿ'}, 'wind': 15, 'rain': 12
    },
    'delhi': {
        'names': {'en': 'New Delhi', 'kn': 'ನವದೆಹಲಿ'},
        'temp_base': 35.0, 'humidity_base': 40, 'desc': {'en': 'Hazy Sunshine', 'kn': 'ಮಬ್ಬು ಸೂರ್ಯನ ಬೆಳಕು'}, 'wind': 8, 'rain': 0
    },
    'mumbai': {
        'names': {'en': 'Mumbai', 'kn': 'ಮುಂಬೈ'},
        'temp_base': 31.0, 'humidity_base': 80, 'desc': {'en': 'Overcast Skies', 'kn': 'ಮೋಡ ಕವಿದ ವಾತಾವರಣ'}, 'wind': 16, 'rain': 45
    }
}

# --- Helpers ---

def get_current_user():
    user_session = session.get('user')
    if not user_session:
        return None
    username = user_session.get('username')
    if not username:
        return None
    return users_col.find_one({'username': username})

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}


def get_record_by_id(record_id):
    if mongo_available:
        try:
            oid = ObjectId(record_id)
            return predictions_col.find_one({'_id': oid})
        except Exception:
            return predictions_col.find_one({'_id': record_id})
    return predictions_col.find_one({'_id': record_id})


def reload_model():
    global model, model_loaded, crops_list
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        with open(LABELS_PATH, 'rb') as f:
            crops_list = pickle.load(f)
        model_loaded = True
        return 'Model reloaded successfully.'
    except Exception as e:
        model_loaded = False
        return f'Model reload failed: {e}'


def handle_admin_upload(req):
    uploaded_model = req.files.get('crop_model')
    uploaded_labels = req.files.get('label_classes')
    uploaded_dataset = req.files.get('dataset_file')
    saved_files = []

    if uploaded_model and uploaded_model.filename:
        filename = secure_filename(uploaded_model.filename)
        uploaded_model.save(os.path.join(BASE_DIR, filename))
        saved_files.append(filename)
    if uploaded_labels and uploaded_labels.filename:
        filename = secure_filename(uploaded_labels.filename)
        uploaded_labels.save(os.path.join(BASE_DIR, filename))
        saved_files.append(filename)
    if uploaded_dataset and uploaded_dataset.filename:
        filename = secure_filename(uploaded_dataset.filename)
        uploaded_dataset.save(os.path.join(BASE_DIR, filename))
        saved_files.append(filename)

    if not saved_files:
        return 'No files were uploaded. Please choose model, label, or dataset files.'
    if 'crop_recommender.pkl' in saved_files or 'label_classes.pkl' in saved_files:
        reload_message = reload_model()
        return f'Uploaded: {", ".join(saved_files)}. {reload_message}'

    return f'Uploaded: {", ".join(saved_files)}.'

# --- Routes ---

@app.route('/api/health')
def health():
    return jsonify({
        'ok': True,
        'mongo': mongo_available,
        'model_loaded': model_loaded,
    })


@app.route('/')
def index():
    if not get_current_user():
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('index'))

    message = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = users_col.find_one({'username': username})
        if user and check_password_hash(user['password_hash'], password):
            session['user'] = {'username': user['username'], 'role': user.get('role', 'farmer')}
            return redirect(url_for('index'))
        message = 'Invalid username or password.'
    return render_template('login.html', message=message)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    current_user = get_current_user()
    if current_user:
        return redirect(url_for('index'))

    message = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not email or not password:
            message = 'Please fill in all fields.'
        elif users_col.find_one({'username': username}):
            message = 'Username already exists.'
        elif users_col.find_one({'email': email}):
            message = 'Email is already registered.'
        else:
            users_col.insert_one({
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'role': 'farmer',
                'created_at': datetime.datetime.now().isoformat()
            })
            session['user'] = {'username': username, 'role': 'farmer'}
            return redirect(url_for('index'))
    return render_template('signup.html', message=message)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    query = {}
    if current_user.get('role') != 'admin':
        query['username'] = current_user['username']

    history_cursor = predictions_col.find(filter=query, limit=100)
    history = []
    for item in history_cursor:
        if '_id' in item:
            item['_id'] = str(item['_id'])
        history.append(item)
    return render_template('profile.html', user=current_user, history=history)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    current_user = get_current_user()
    if not current_user or current_user.get('role') != 'admin':
        return redirect(url_for('login'))

    message = None
    if request.method == 'POST':
        if request.form.get('action') == 'reload_model':
            message = reload_model()
        elif request.form.get('action') == 'upload_files':
            message = handle_admin_upload(request)
    return render_template('admin.html', user=current_user, model_loaded=model_loaded, message=message)

@app.route('/report/<record_id>')
def report(record_id):
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    record = get_record_by_id(record_id)
    if not record:
        return "Record not found.", 404
    if current_user.get('role') != 'admin' and record.get('username') != current_user['username']:
        return "Unauthorized", 403
    if '_id' in record:
        record['_id'] = str(record['_id'])

    # Ensure dynamic advisory advice and localized soil types exist for the report template
    if 'advice' not in record or not record.get('advice'):
        crop = record.get('recommended_crop', 'Maize')
        advice = crop_advisory.get(crop, crop_advisory.get('Maize'))
        record['advice'] = {
            'fertilizer': advice['fertilizer'],
            'irrigation': advice['irrigation'],
            'soil_improvement': advice['soil'],
            'ideal_weather': advice.get('ideal_weather', {'en': 'Moderate weather', 'kn': 'ಮಧ್ಯಮ ಹವಾಮಾನ'}),
            'estimated_income': advice.get('estimated_income', {'en': 'High yield potential', 'kn': 'ಹೆಚ್ಚಿನ ಇಳುವರಿ ಸಾಮರ್ಥ್ಯ'})
        }
    else:
        # backfill if fields are missing in stored mongo records
        if 'ideal_weather' not in record['advice']:
            crop = record.get('recommended_crop', 'Maize')
            advice = crop_advisory.get(crop, crop_advisory.get('Maize'))
            record['advice']['ideal_weather'] = advice.get('ideal_weather', {'en': 'Moderate weather', 'kn': 'ಮಧ್ಯಮ ಹವಾಮಾನ'})
        if 'estimated_income' not in record['advice']:
            crop = record.get('recommended_crop', 'Maize')
            advice = crop_advisory.get(crop, crop_advisory.get('Maize'))
            record['advice']['estimated_income'] = advice.get('estimated_income', {'en': 'High yield potential', 'kn': 'ಹೆಚ್ಚಿನ ಇಳುವರಿ ಸಾಮರ್ಥ್ಯ'})
    if 'soil_type_localized' not in record or not record.get('soil_type_localized'):
        ph = record.get('ph', 7.0)
        if ph < 6.0:
            soil_type_en = 'Acidic Soil'
            soil_type_kn = 'ಆಮ್ಲೀಯ ಮಣ್ಣು'
        elif ph > 7.5:
            soil_type_en = 'Alkaline Soil'
            soil_type_kn = 'ಕ್ಷಾರೀಯ ಮಣ್ಣು'
        else:
            soil_type_en = 'Neutral Soil (Ideal)'
            soil_type_kn = 'ತಟಸ್ಥ ಮಣ್ಣು (ಆದರ್ಶ)'
        record['soil_type_localized'] = {'en': soil_type_en, 'kn': soil_type_kn}

    return render_template('report.html', record=record, user=current_user)

@app.route('/export/history/<fmt>')
@app.route('/export/history.<fmt>')
def export_history(fmt):
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    query = {}
    if current_user.get('role') != 'admin':
        query['username'] = current_user['username']

    history_cursor = predictions_col.find(filter=query, limit=1000)
    history = list(history_cursor) if history_cursor is not None else []
    if not history:
        return "No history available to export.", 404

    try:
        import pandas as pd
    except ImportError:
        return "Export functionality requires pandas. Please install it with pip install pandas.", 500
    df = pd.DataFrame(list(history))
    if '_id' in df.columns:
        df['_id'] = df['_id'].astype(str)

    filename_base = f"agrosmart_history_{current_user['username']}"
    if fmt == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            download_name=f"{filename_base}.csv",
            as_attachment=True
        )
    elif fmt in ('xlsx', 'xls'):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='History')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name=f"{filename_base}.xlsx",
            as_attachment=True
        )
    else:
        return "Unsupported export format.", 400

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
            
        user_message = data.get('message', '').strip().lower()
        
        # Simple intelligent localized chatbot database
        responses = {
            'greeting': {
                'keywords': ['hello', 'hi', 'hey', 'namaste', 'namaskara', 'hello there', 'ಯಾರು', 'ಹಲೋ', 'ನಮಸ್ಕಾರ'],
                'en': "Hello! I am your AgroSmart AI Assistant. How can I help you with your crops, soil pH, or fertilizers today?",
                'kn': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಅಗ್ರೋಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಸಲಹೆಗಾರ. ಇವತ್ತು ನಿಮಗೆ ಬೆಳೆಗಳು, ಮಣ್ಣಿನ ಪಿಎಚ್ ಅಥವಾ ರಸಗೊಬ್ಬರಗಳ ಬಗ್ಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?"
            },
            'ph': {
                'keywords': ['ph', 'acidic', 'alkaline', 'soil test', 'acid', 'ಪಿಎಚ್', 'ಆಮ್ಲ', 'ಕ್ಷಾರ', 'ಮಣ್ಣಿನ ಪರೀಕ್ಷೆ'],
                'en': "Soil pH determines nutrient availability. Ideal pH for most crops is 6.0 to 7.0 (neutral). For acidic soil, apply agricultural lime (calcium carbonate). For alkaline soil, apply gypsum or elemental sulfur to lower pH.",
                'kn': "ಮಣ್ಣಿನ ಪಿಎಚ್ ಪೋಷಕಾಂಶಗಳ ಲಭ್ಯತೆಯನ್ನು ನಿರ್ಧರಿಸುತ್ತದೆ. ಹೆಚ್ಚಿನ ಬೆಳೆಗಳಿಗೆ ಸೂಕ್ತವಾದ ಪಿಎಚ್ 6.0 ರಿಂದ 7.0 (ತಟಸ್ಥ). ಆಮ್ಲೀಯ ಮಣ್ಣಿಗೆ ಕೃಷಿ ಸುಣ್ಣವನ್ನು ಹಾಕಿ. ಕ್ಷಾರೀಯ ಮಣ್ಣಿಗೆ ಜಿಪ್ಸಮ್ ಅಥವಾ ಗಂಧಕವನ್ನು ಬಳಸಿ ಪಿಎಚ್ ಅನ್ನು ಕಡಿಮೆ ಮಾಡಿ."
            },
            'fertilizer': {
                'keywords': ['fertilizer', 'npk', 'nitrogen', 'phosphorus', 'potassium', 'urea', 'dap', 'manure', 'ಗೊಬ್ಬರ', 'ಯೂರಿಯಾ', 'ಡಿಎಪಿ', 'ಸಾರಜನಕ'],
                'en': "NPK stands for Nitrogen (for leafy growth), Phosphorus (for root and flower development), and Potassium (for disease resistance and fruit quality). Apply organic farmyard manure or vermicompost to build overall soil health along with chemical NPK in split doses.",
                'kn': "NPK ಎಂದರೆ ಸಾರಜನಕ (ಎಲೆಗಳ ಬೆಳವಣಿಗೆಗೆ), ರಂಜಕ (ಬೇರು ಮತ್ತು ಹೂಬಿಡುವಿಕೆಗೆ), ಮತ್ತು ಪೊಟ್ಯಾಷಿಯಂ (ರೋಗ ನಿರೋಧಕ ಶಕ್ತಿ ಮತ್ತು ಹಣ್ಣಿನ ಗುಣಮಟ್ಟಕ್ಕಾಗಿ). ಮಣ್ಣಿನ ಒಟ್ಟಾರೆ ಆರೋಗ್ಯಕ್ಕಾಗಿ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಅಥವಾ ಎರೆಗೊಬ್ಬರವನ್ನು ಸಮತೋಲಿತ NPK ಜೊತೆಗೆ ಬಳಸಿ."
            },
            'pest': {
                'keywords': ['pest', 'insects', 'disease', 'fungus', 'bugs', 'leaf rot', 'worm', 'ಕ್ರಿಮಿಕೀಟ', 'ರೋಗ', 'ಕೀಟನಾಶಕ', 'ಹುಳು'],
                'en': "For sustainable pest management, use Neem oil spray (1-2%) for early-stage sucking pests. Ensure proper crop rotation, remove infected plant debris, and use pheromone traps. For severe fungal attacks, consult a local expert for appropriate copper-based fungicides.",
                'kn': "ಸುಸ್ಥಿರ ಕೀಟ ನಿಯಂತ್ರಣಕ್ಕಾಗಿ, ಆರಂಭಿಕ ಕೀಟಗಳಿಗೆ ಬೇವಿನ ಎಣ್ಣೆ ಸಿಂಪಡಣೆಯನ್ನು (1-2%) ಬಳಸಿ. ಸರಿಯಾದ ಬೆಳೆ ಸರದಿಯನ್ನು ಅನುಸರಿಸಿ ಮತ್ತು ಸೋಂಕಿತ ಸಸ್ಯದ ಭಾಗಗಳನ್ನು ತೆಗೆದುಹಾಕಿ. ತೀವ್ರ ಶಿಲೀಂಧ್ರ ರೋಗಗಳಿಗೆ ತಾಮ್ರದ ಆಧಾರಿತ ಶಿಲೀಂಧ್ರನಾಶಕಗಳನ್ನು ಬಳಸಿ."
            },
            'water': {
                'keywords': ['water', 'irrigation', 'rain', 'drip', 'watering', 'ಬರ', 'ನೀರಾವರಿ', 'ನೀರು', 'ಹನಿ ನೀರಾವರಿ'],
                'en': "Drip irrigation is the most efficient way to water crops as it saves up to 50% water and delivers moisture directly to root zones, reducing weeds. Avoid watering during mid-day heat to prevent evaporation; early morning or late evening is best.",
                'kn': "ಹನಿ ನೀರಾವರಿಯು ಅತ್ಯಂತ ಪರಿಣಾಮಕಾರಿ ವಿಧಾನವಾಗಿದ್ದು, ಶೇ. 50 ರಷ್ಟು ನೀರನ್ನು ಉಳಿಸುತ್ತದೆ ಮತ್ತು ನೇರವಾಗಿ ಬೇರುಗಳಿಗೆ ತೇವ ನೀಡುತ್ತದೆ. ಮಧ್ಯಾಹ್ನದ ಬಿಸಿಲಿನಲ್ಲಿ ನೀರು ಹಾಯಿಸಬೇಡಿ; ಮುಂಜಾನೆ ಅಥವಾ ಸಂಜೆ ನೀರುಣಿಸುವುದು ಅತ್ಯುತ್ತಮ."
            },
            'crop_rotation': {
                'keywords': ['rotation', 'rotate', 'succession', 'legumes', 'ಬೆಳೆ ಸರದಿ', 'ದ್ವಿದಳ ಧಾನ್ಯ'],
                'en': "Crop rotation breaks pest cycles and naturally restores soil nutrients. Always rotate heavy nutrient consumers (like maize or rice) with leguminous crops (like chickpeas, cowpeas, or mung beans) which naturally capture and fix atmospheric nitrogen in the soil.",
                'kn': "ಬೆಳೆ ಸರದಿ ವಿಧಾನವು ಕೀಟಗಳ ಚಕ್ರವನ್ನು ತಡೆಯುತ್ತದೆ ಮತ್ತು ಮಣ್ಣಿನ ಫಲವತ್ತತೆಯನ್ನು ನೈಸರ್ಗಿಕವಾಗಿ ಮರುಸ್ಥಾಪಿಸುತ್ತದೆ. ಜೋಳ ಅಥವಾ ಭತ್ತದಂತಹ ಹೆಚ್ಚಿನ ಪೋಷಕಾಂಶ ಹೀರುವ ಬೆಳೆಗಳ ನಂತರ ದ್ವಿದಳ ಧಾನ್ಯಗಳ ಬೆಳೆಗಳನ್ನು (ಕಡಲೆ, ಹೆಸರು) ಬೆಳೆಯಿರಿ."
            }
        }
        
        # Match keywords
        matched_reply = None
        for category, item in responses.items():
            if any(kw in user_message for kw in item['keywords']):
                matched_reply = item
                break
                
        if matched_reply:
            reply_en = matched_reply['en']
            reply_kn = matched_reply['kn']
        else:
            # Default helper message
            reply_en = "I'm sorry, I couldn't understand that farming query fully. Try asking about 'soil pH', 'organic fertilizer', 'pest control', 'crop rotation', or 'drip irrigation'."
            reply_kn = "ಕ್ಷಮಿಸಿ, ಕೃಷಿಗೆ ಸಂಬಂಧಿಸಿದ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನನಗೆ ಸಂಪೂರ್ಣವಾಗಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು 'ಮಣ್ಣಿನ ಪಿಎಚ್', 'ಸಾವಯವ ಗೊಬ್ಬರ', 'ಕೀಟ ನಿಯಂತ್ರಣ', ಅಥವಾ 'ಹನಿ ನೀರಾವರಿ' ಬಗ್ಗೆ ಕೇಳಿ."
            
        return jsonify({
            'success': True,
            'reply': {
                'en': reply_en,
                'kn': reply_kn
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f"Chat error: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        query = {}
        if current_user.get('role') != 'admin':
            query['username'] = current_user['username']

        history_cursor = predictions_col.find(filter=query, limit=50)
        history = []
        
        # Convert _id fields to string for JSON serialization
        for item in history_cursor:
            if "_id" in item:
                item["_id"] = str(item["_id"])
            history.append(item)
                
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to retrieve history: {str(e)}"}), 500

@app.route('/api/predict', methods=['POST'])
def api_predict():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'success': False, 'error': 'Invalid payload'}), 400

        n = float(data.get('N', 0))
        p = float(data.get('P', 0))
        k = float(data.get('K', 0))
        temp = float(data.get('temperature', 0))
        humidity = float(data.get('humidity', 0))
        ph = float(data.get('ph', 0))
        rainfall = float(data.get('rainfall', 0))

        if model_loaded and model is not None:
            try:
                prediction = model.predict([[n, p, k, temp, humidity, ph, rainfall]])
                if hasattr(prediction, '__iter__'):
                    recommended_crop = prediction[0]
                else:
                    recommended_crop = prediction
            except Exception as model_e:
                recommended_crop = fallback_recommendation(n, p, k, temp, humidity, ph, rainfall)
        else:
            recommended_crop = fallback_recommendation(n, p, k, temp, humidity, ph, rainfall)

        recommended_crop = str(recommended_crop)
        if recommended_crop not in crop_advisory:
            recommended_crop = fallback_recommendation(n, p, k, temp, humidity, ph, rainfall)

        # Determine soil classification
        if ph < 6.0:
            soil_type_en = 'Acidic Soil'
            soil_type_kn = 'ಆಮ್ಲೀಯ ಮಣ್ಣು'
        elif ph > 7.5:
            soil_type_en = 'Alkaline Soil'
            soil_type_kn = 'ಕ್ಷಾರೀಯ ಮಣ್ಣು'
        else:
            soil_type_en = 'Neutral Soil (Ideal)'
            soil_type_kn = 'ತಟಸ್ಥ ಮಣ್ಣು (ಆದರ್ಶ)'

        advice = crop_advisory.get(recommended_crop, crop_advisory['Maize'])
        prediction_record = {
            'username': current_user['username'],
            'N': n,
            'P': p,
            'K': k,
            'ph': ph,
            'recommended_crop': recommended_crop,
            'soil_type': soil_type_en,
            'soil_type_localized': {'en': soil_type_en, 'kn': soil_type_kn},
            'timestamp': datetime.datetime.now().isoformat(),
            'advice': {
                'fertilizer': advice['fertilizer'],
                'irrigation': advice['irrigation'],
                'soil_improvement': advice['soil'],
                'ideal_weather': advice.get('ideal_weather', {'en': 'Moderate weather', 'kn': 'ಮಧ್ಯಮ ಹವಾಮಾನ'}),
                'estimated_income': advice.get('estimated_income', {'en': 'High yield potential', 'kn': 'ಹೆಚ್ಚಿನ ಇಳುವರಿ ಸಾಮರ್ಥ್ಯ'})
            }
        }

        insert_result = predictions_col.insert_one(prediction_record)
        prediction_id = str(insert_result.inserted_id)

        return jsonify({
            'success': True,
            'crop': recommended_crop,
            'soil_classification': {'en': soil_type_en, 'kn': soil_type_kn},
            'advice': {
                'fertilizer': {'en': advice['fertilizer']['en'], 'kn': advice['fertilizer']['kn']},
                'irrigation': {'en': advice['irrigation']['en'], 'kn': advice['irrigation']['kn']},
                'soil_improvement': {'en': advice['soil']['en'], 'kn': advice['soil']['kn']},
                'ideal_weather': {'en': advice.get('ideal_weather', {}).get('en', 'Moderate weather'), 'kn': advice.get('ideal_weather', {}).get('kn', 'ಮಧ್ಯಮ ಹವಾಮಾನ')},
                'estimated_income': {'en': advice.get('estimated_income', {}).get('en', 'High yield potential'), 'kn': advice.get('estimated_income', {}).get('kn', 'ಹೆಚ್ಚಿನ ಇಳುವರಿ ಸಾಮರ್ಥ್ಯ')}
            },
            'prediction_id': prediction_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        city = request.args.get('city', 'bangalore').strip().lower()
        
        # Use database mock or generate a random variation for any new searched city
        if city in weather_cities:
            data = weather_cities[city]
        else:
            # Generate highly realistic dynamic weather for unknown searched city
            hash_val = sum(ord(c) for c in city)
            temp = 24.0 + (hash_val % 12) + random.uniform(-1, 1)
            humidity = 50 + (hash_val % 40)
            desc_en = "Light Breeze & Sunny"
            desc_kn = "ಸೌಮ್ಯ ತಂಗಾಳಿ ಮತ್ತು ಬಿಸಿಲು"
            
            data = {
                'names': {'en': city.capitalize(), 'kn': city.capitalize()},
                'temp_base': temp,
                'humidity_base': humidity,
                'desc': {'en': desc_en, 'kn': desc_kn},
                'wind': 8 + (hash_val % 10),
                'rain': hash_val % 20
            }
            
        # Add a small random variation to simulate real-time sensor reporting
        variation_temp = random.uniform(-0.5, 0.5)
        variation_hum = random.randint(-2, 2)
        
        temp = round(data['temp_base'] + variation_temp, 1)
        humidity = min(100, max(15, int(data['humidity_base'] + variation_hum)))
        
        return jsonify({
            'success': True,
            'city_name': data['names'],
            'temp': temp,
            'humidity': humidity,
            'description': data['desc'],
            'wind_speed': data['wind'],
            'rainfall_prob': data['rain'],
            'timestamp': datetime.datetime.now().strftime("%I:%M %p")
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f"Weather retrieval failed: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)

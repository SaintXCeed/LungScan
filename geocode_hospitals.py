"""
Geocode all unique hospitals in doctors.json using Nominatim (OpenStreetMap).
"""
import json
import time
import urllib.request
import urllib.parse
import random

JSON_PATH = 'C:/Users/trija/Documents/LungDetection/backend/static/doctors.json'

with open(JSON_PATH, encoding='utf-8') as f:
    doctors = json.load(f)

cache = {}

def geocode(hospital, city):
    queries = [
        f"{hospital}, {city}, Indonesia",
        f"{hospital}, Indonesia",
        f"{city}, Indonesia",
    ]
    headers = {'User-Agent': 'LungScanAI/1.0 (student project)'}
    for q in queries:
        params = urllib.parse.urlencode({'q': q, 'format': 'json', 'limit': 1})
        url = f"https://nominatim.openstreetmap.org/search?{params}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data:
                lat = float(data[0]['lat'])
                lng = float(data[0]['lon'])
                print(f"  OK '{q}' -> ({lat:.4f}, {lng:.4f})")
                return lat, lng
        except Exception as e:
            print(f"  ERR '{q}': {e}")
        time.sleep(1.2)
    return None

failed = []
for i, doc in enumerate(doctors):
    hospital = doc['facility']
    city = doc['city']
    key = f"{hospital}|{city}"

    if key not in cache:
        print(f"[{i+1}/54] Geocoding: {hospital}, {city}")
        result = geocode(hospital, city)
        if result:
            cache[key] = result
        else:
            print(f"  FAILED - keeping old coords for: {hospital}")
            failed.append(key)
            cache[key] = (doc['lat'], doc['lng'])
    else:
        print(f"[{i+1}/54] Cache: {hospital}")

    lat, lng = cache[key]
    random.seed(doc['id'])
    doc['lat'] = lat + random.uniform(-0.0003, 0.0003)
    doc['lng'] = lng + random.uniform(-0.0003, 0.0003)

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(doctors, f, indent=4, ensure_ascii=False)

print(f"\nDone! Updated {len(doctors)} doctors.")
if failed:
    print(f"Failed: {failed}")
else:
    print("All hospitals geocoded successfully!")

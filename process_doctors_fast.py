import pandas as pd
import json
import random

EXCEL_PATH = 'C:/Users/trija/Documents/LungDetection/Daftar_50_Dokter_Kanker_Paru_Indonesia.xlsx'
OUTPUT_JSON = 'C:/Users/trija/Documents/LungDetection/backend/static/doctors.json'

# Base coordinates for major Indonesian cities
CITY_COORDS = {
    'Jakarta': (-6.2088, 106.8456),
    'Surabaya': (-7.2504, 112.7688),
    'Bandung': (-6.9175, 107.6191),
    'Medan': (3.5952, 98.6722),
    'Semarang': (-6.9666, 110.4167),
    'Makassar': (-5.1476, 119.4327),
    'Palembang': (-2.9909, 104.7565),
    'Denpasar': (-8.6705, 115.2126),
    'Yogyakarta': (-7.7956, 110.3695),
    'Malang': (-7.9839, 112.6214),
    # Add aliases or defaults
    'DKI Jakarta': (-6.2088, 106.8456),
}

def get_city_coord(city, prov):
    # Try finding the city name or parts of it
    city = str(city).title()
    for key in CITY_COORDS:
        if key in city or key in str(prov):
            return CITY_COORDS[key]
    # Default to Jakarta if not found
    return CITY_COORDS['Jakarta']

def infer_type(hospital_name):
    hospital_name = str(hospital_name).lower()
    if any(x in hospital_name for x in ['rsup', 'rsud', 'umum', 'pusat', 'rsk']):
        return 'BPJS'
    else:
        return 'Swasta'

def main():
    print(f"Reading {EXCEL_PATH}...")
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        print(f"Error reading excel: {e}")
        return

    df = df.fillna('')
    doctors_list = []
    
    hospital_cache = {}

    for idx, row in df.iterrows():
        name_raw = str(row.get('Nama Dokter', '')).strip()
        gelar = str(row.get('Gelar', '')).strip()
        hospital = str(row.get('Rumah Sakit Utama', '')).strip()
        city = str(row.get('Kota', '')).strip()
        prov = str(row.get('Provinsi', '')).strip()
        
        # Format name
        if not name_raw.lower().startswith('dr'):
            full_name = f"dr. {name_raw}"
        else:
            full_name = name_raw
            
        if gelar:
            full_name = f"{full_name}, {gelar}"
            
        hospital_key = f"{hospital}, {city}"
        
        if hospital_key not in hospital_cache:
            base_lat, base_lng = get_city_coord(city, prov)
            # Add random jitter so hospitals in the same city are spread out by ~1-5km
            lat_jitter = random.uniform(-0.04, 0.04)
            lng_jitter = random.uniform(-0.04, 0.04)
            hospital_cache[hospital_key] = {
                'lat': base_lat + lat_jitter,
                'lng': base_lng + lng_jitter,
            }
            
        h_info = hospital_cache[hospital_key]
        
        doctor_obj = {
            "id": idx + 1,
            "name": full_name,
            "specialty": "Dokter Spesialis Paru (Pulmonologi)",
            "facility": hospital,
            "address": f"{hospital}, {city}, {prov}",
            "phone": "+62 800-0000-0000",
            "type": infer_type(hospital),
            "lat": h_info['lat'] + random.uniform(-0.0002, 0.0002), # jitter for doctors in same hospital
            "lng": h_info['lng'] + random.uniform(-0.0002, 0.0002),
            "city": city,
            "province": prov
        }
        
        doctors_list.append(doctor_obj)

    print(f"Saving {len(doctors_list)} records to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(doctors_list, f, indent=4, ensure_ascii=False)
        
    print("Done!")

if __name__ == '__main__':
    main()

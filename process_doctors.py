import pandas as pd
import json
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Define file paths
EXCEL_PATH = 'C:/Users/trija/Documents/LungDetection/Daftar_50_Dokter_Kanker_Paru_Indonesia.xlsx'
OUTPUT_JSON = 'C:/Users/trija/Documents/LungDetection/backend/static/doctors.json'

def infer_type(hospital_name):
    hospital_name = str(hospital_name).lower()
    if any(x in hospital_name for x in ['rsup', 'rsud', 'umum', 'pusat', 'rsk']):
        return 'BPJS'
    else:
        return 'Swasta'

def geocode_with_retry(geolocator, query, retries=3):
    for i in range(retries):
        try:
            time.sleep(1.5) # Be kind to Nominatim
            location = geolocator.geocode(query, timeout=10)
            if location:
                return location
        except (GeocoderTimedOut, GeocoderServiceError):
            time.sleep(2)
            continue
    return None

def main():
    print(f"Reading {EXCEL_PATH}...")
    try:
        df = pd.read_excel(EXCEL_PATH)
    except Exception as e:
        print(f"Error reading excel: {e}")
        return

    # Basic cleaning
    df = df.fillna('')
    
    geolocator = Nominatim(user_agent="lungscan_ai_mvp_v1")
    
    # Dictionary to cache hospital locations
    hospital_cache = {}
    
    doctors_list = []
    
    print(f"Processing {len(df)} doctors...")
    for idx, row in df.iterrows():
        name_raw = str(row.get('Nama Dokter', ''))
        gelar = str(row.get('Gelar', ''))
        hospital = str(row.get('Rumah Sakit Utama', ''))
        city = str(row.get('Kota', ''))
        prov = str(row.get('Provinsi', ''))
        
        # Format name
        if not name_raw.lower().startswith('dr'):
            full_name = f"dr. {name_raw}"
        else:
            full_name = name_raw
            
        if gelar:
            full_name = f"{full_name}, {gelar}"
            
        hospital_key = f"{hospital}, {city}"
        
        if hospital_key not in hospital_cache:
            print(f"Geocoding: {hospital_key}")
            # Try full query
            loc = geocode_with_retry(geolocator, f"{hospital}, {city}, Indonesia")
            if not loc:
                # Fallback to city
                loc = geocode_with_retry(geolocator, f"{city}, Indonesia")
            
            if loc:
                hospital_cache[hospital_key] = {
                    'lat': loc.latitude,
                    'lng': loc.longitude,
                    'address': loc.address
                }
            else:
                # Default to Jakarta if completely failed
                hospital_cache[hospital_key] = {
                    'lat': -6.200000,
                    'lng': 106.816666,
                    'address': f"{hospital}, {city}, {prov}, Indonesia"
                }
        
        h_info = hospital_cache[hospital_key]
        
        doctor_obj = {
            "id": idx + 1,
            "name": full_name,
            "specialty": "Kanker Paru / Onkologi",
            "facility": hospital,
            "address": h_info['address'].split(',')[0] + f", {city}" if len(h_info['address']) > 20 else h_info['address'],
            "phone": "+62 800-0000-0000",  # Placeholder as it's not in the excel
            "type": infer_type(hospital),
            "lat": h_info['lat'] + (idx * 0.0001), # Add slight jitter so markers don't perfectly overlap if they are in the same hospital
            "lng": h_info['lng'] + (idx * 0.0001),
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

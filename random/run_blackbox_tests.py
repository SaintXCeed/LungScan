import subprocess
import time
import requests
import os
import json

BACKEND_DIR = r"c:\Users\trija\Documents\LungDetection\backend"
TEST_DIR = r"c:\Users\trija\Documents\LungDetection\gambar test"

print("Memulai backend...")
proc = subprocess.Popen(
    ["python", "-m", "uvicorn", "main:app", "--port", "8000"],
    cwd=BACKEND_DIR
)

def wait_for_server():
    max_retries = 120
    for i in range(max_retries):
        try:
            res = requests.get("http://127.0.0.1:8000/api/health")
            if res.status_code == 200:
                print("Backend siap!")
                return True
        except:
            pass
        time.sleep(1)
    return False

if not wait_for_server():
    print("Gagal memulai backend.")
    proc.terminate()
    exit(1)

results = []

print("\n--- Mulai Pengujian Blackbox ---\n")

# Test 1: File normal (Adenocarcinoma)
f_path = os.path.join(TEST_DIR, "Adenocarsinoma.jpg")
print(f"Test 1: Upload {f_path}")
try:
    with open(f_path, "rb") as f:
        res = requests.post("http://127.0.0.1:8000/api/predict", files={"file": ("Adenocarsinoma.jpg", f, "image/jpeg")})
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:200]}...")
    results.append({"id": "TC-01", "status_code": res.status_code, "response": res.json()})
except Exception as e:
    print(f"Error: {e}")

# Test 2: Invalid type (Model.txt.txt)
f_path = os.path.join(TEST_DIR, "Model.txt.txt")
print(f"\nTest 2: Upload {f_path}")
try:
    with open(f_path, "rb") as f:
        res = requests.post("http://127.0.0.1:8000/api/predict", files={"file": ("Model.txt.txt", f, "text/plain")})
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
    results.append({"id": "TC-02", "status_code": res.status_code, "response": res.json()})
except Exception as e:
    print(f"Error: {e}")

# Test 3: File > 10MB
f_path = os.path.join(TEST_DIR, "Adenocarsinoma-diatas10MB.jpeg")
print(f"\nTest 3: Upload {f_path}")
try:
    with open(f_path, "rb") as f:
        res = requests.post("http://127.0.0.1:8000/api/predict", files={"file": ("Adenocarsinoma-diatas10MB.jpeg", f, "image/jpeg")})
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
    results.append({"id": "TC-03", "status_code": res.status_code, "response": res.json()})
except Exception as e:
    print(f"Error: {e}")

# Test 4: File Normal (Normal bypass severity)
f_path = os.path.join(TEST_DIR, "normal-ct-chest.jpg")
print(f"\nTest 4: Upload {f_path}")
try:
    with open(f_path, "rb") as f:
        res = requests.post("http://127.0.0.1:8000/api/predict", files={"file": ("normal-ct-chest.jpg", f, "image/jpeg")})
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:200]}...")
    results.append({"id": "TC-04", "status_code": res.status_code, "response": res.json()})
except Exception as e:
    print(f"Error: {e}")

# Test 5: /api/guidance
print(f"\nTest 5: GET /api/guidance")
try:
    res = requests.get("http://127.0.0.1:8000/api/guidance")
    print(f"Status: {res.status_code}")
    results.append({"id": "TC-05", "status_code": res.status_code, "response": res.json()})
except Exception as e:
    print(f"Error: {e}")

# Test 6: /api/doctors
print(f"\nTest 6: GET /api/doctors")
try:
    res = requests.get("http://127.0.0.1:8000/api/doctors")
    print(f"Status: {res.status_code}")
    results.append({"id": "TC-06", "status_code": res.status_code, "response": res.json()})
except Exception as e:
    print(f"Error: {e}")

proc.terminate()
print("\nBackend dihentikan.")

with open("test_results.json", "w") as f:
    json.dump(results, f, indent=4)

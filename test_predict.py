import requests, sys, time, json
sys.stdout.reconfigure(encoding='utf-8')

img_path = r"model-final\chest-ctscan-images\test\adenocarcinoma\000108 (3).png"

print("Running 3 prediction tests to measure timing...")
print()
for i in range(3):
    t0 = time.time()
    with open(img_path, "rb") as f:
        files = {"file": ("000108.png", f, "image/png")}
        resp = requests.post("http://localhost:8000/api/predict", files=files)
    elapsed = time.time() - t0

    if resp.status_code == 200:
        data = resp.json()
        print(f"Test {i+1}: {elapsed:.2f}s")
        print(f"  prediction: {data['prediction']} ({data['confidence']}%)")
        print(f"  severity  : {data['severity']} ({data['severity_confidence']}%)")
        print(f"  heatmap   : {len(data['heatmap_base64'])} chars")
    else:
        print(f"Test {i+1}: ERROR {resp.status_code} - {resp.text}")
    print()

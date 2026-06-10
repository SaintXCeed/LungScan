"""
Comprehensive validation: test predictions across all 4 classes
and inspect model architecture to verify correctness.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\trija\Documents\LungDetection")

import numpy as np
from PIL import Image
import io, glob, json
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.resnet50 import preprocess_input

print("=" * 60)
print("LOADING MODELS")
print("=" * 60)

type_model = keras.models.load_model(
    r"model-final\Lung_Cancer_ResNet50_88Acc.keras", compile=False
)
severity_model = keras.models.load_model(
    r"model-final\Lung_Cancer_Severity_Model.h5", compile=False
)

# ── 1. Inspect type model architecture ────────────────────────────────────────
print("\n[1] Last 8 layers of Type Model:")
for layer in type_model.layers[-8:]:
    try:
        out_shape = layer.output.shape
    except:
        out_shape = "?"
    print(f"  {layer.name:40s} {type(layer).__name__:30s} {str(out_shape)}")

# ── 2. Check if BatchNorm exists between GAP and Dense ────────────────────────
print("\n[2] Layers between GAP and Dense:")
found_gap = False
intermed = []
for layer in type_model.layers:
    if "global_average" in layer.name:
        found_gap = True
    if found_gap:
        intermed.append(layer.name)
        if "dense" in layer.name:
            break
print(f"  Chain: {' -> '.join(intermed)}")

# ── 3. BatchNorm parameters ────────────────────────────────────────────────────
bn_layers = [l for l in type_model.layers if "batch_normalization" in l.name.lower()]
print(f"\n[3] BatchNorm layers found: {[l.name for l in bn_layers]}")

# The BN closest to Dense (last BN before Dense)
if bn_layers:
    bn = bn_layers[-1]
    gamma, beta, mean, var = bn.get_weights()  # [gamma, beta, run_mean, run_var]
    std = np.sqrt(var + 1e-5)
    effective_scale = gamma / std
    print(f"    gamma range  : [{gamma.min():.4f}, {gamma.max():.4f}]")
    print(f"    mean range   : [{mean.min():.4f}, {mean.max():.4f}]")
    print(f"    eff_scale rng: [{effective_scale.min():.4f}, {effective_scale.max():.4f}]")

# ── 4. Dense layer weights ────────────────────────────────────────────────────
dense = type_model.get_layer("dense")
W, b = dense.get_weights()  # W: (2048, 4), b: (4,)
print(f"\n[4] Dense layer: W={W.shape}, b={b.shape}")
print(f"    W range: [{W.min():.4f}, {W.max():.4f}]")

# ── 5. BN-corrected effective weights for CAM ─────────────────────────────────
if bn_layers:
    w_eff = W * effective_scale[:, np.newaxis]  # (2048, 4)
    print(f"\n[5] BN-corrected CAM weights:")
    print(f"    w_eff range: [{w_eff.min():.4f}, {w_eff.max():.4f}]")
    print(f"    Difference from raw W (mean abs): {np.abs(w_eff - W).mean():.4f}")

# ── 6. Severity model architecture ────────────────────────────────────────────
print("\n[6] Severity model last 5 layers:")
for layer in severity_model.layers[-5:]:
    try:
        out_shape = layer.output.shape
    except:
        out_shape = "?"
    print(f"  {layer.name:40s} {type(layer).__name__:25s} {str(out_shape)}")

# ── 7. Multi-class prediction test ────────────────────────────────────────────
TYPE_CLASSES = ["adenocarcinoma", "large.cell.carcinoma", "normal", "squamous.cell.carcinoma"]
SEVERITY_CLASSES = ["Normal", "Benign", "Malignant"]
TEST_DIR = r"model-final\chest-ctscan-images\test"

print("\n" + "=" * 60)
print("PREDICTION ACCURACY TEST (3 images per class)")
print("=" * 60)

results = {"correct": 0, "total": 0}

for cls in TYPE_CLASSES:
    cls_dir = os.path.join(TEST_DIR, cls)
    if not os.path.exists(cls_dir):
        print(f"  [SKIP] {cls}: directory not found")
        continue
    
    imgs = glob.glob(os.path.join(cls_dir, "*.png"))[:3]
    if not imgs:
        imgs = glob.glob(os.path.join(cls_dir, "*.jpg"))[:3]
    
    print(f"\n  Class: {cls} ({len(imgs)} images)")
    
    for img_path in imgs:
        img = Image.open(img_path).convert("RGB").resize((460, 460), Image.LANCZOS)
        arr = preprocess_input(np.array(img, dtype=np.float32))
        x = tf.constant(np.expand_dims(arr, 0), dtype=tf.float32)
        
        pred = type_model(x, training=False).numpy()[0]
        pred_cls = TYPE_CLASSES[np.argmax(pred)]
        conf = np.max(pred) * 100
        
        correct = pred_cls == cls
        results["total"] += 1
        if correct:
            results["correct"] += 1
        
        marker = "OK" if correct else "WRONG"
        print(f"    [{marker}] {os.path.basename(img_path)[:30]:30s} -> {pred_cls:25s} ({conf:.1f}%)")

acc = results["correct"] / results["total"] * 100 if results["total"] > 0 else 0
print(f"\nLocal test accuracy: {results['correct']}/{results['total']} = {acc:.1f}%")

# ── 8. Severity model: check output with known cancer images ──────────────────
print("\n" + "=" * 60)
print("SEVERITY MODEL TEST")
print("=" * 60)
cls_dir = os.path.join(TEST_DIR, "adenocarcinoma")
imgs = glob.glob(os.path.join(cls_dir, "*.png"))[:3]
for img_path in imgs:
    img = Image.open(img_path).convert("RGB").resize((224, 224), Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    x = tf.constant(np.expand_dims(arr, 0), dtype=tf.float32)
    pred = severity_model(x, training=False).numpy()[0]
    print(f"  {os.path.basename(img_path)[:30]:30s}: {dict(zip(SEVERITY_CLASSES, [f'{p*100:.1f}%' for p in pred]))}")
    print(f"    -> {SEVERITY_CLASSES[np.argmax(pred)]} ({np.max(pred)*100:.1f}%)")

print("\nDone.")

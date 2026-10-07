"""
Severity Model Evaluation — Cancer Images Only.

The severity model is called ONLY for cancer predictions (normal → bypassed by clinical rule).
Ground truth labels derived from TNM staging in folder names:
  Stage I  (Ib) → Benign
  Stage III (IIIa) → Malignant

Valid set cancer folders:
  adenocarcinoma_..._T2_N0_M0_Ib    → Benign   (Stage I)
  large.cell.carcinoma_..._IIIa     → Malignant (Stage III)
  squamous.cell.carcinoma_..._IIIa  → Malignant (Stage III)
"""
import sys, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\trija\Documents\LungDetection")

import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow import keras

MODEL_PATH = r"model-final\Lung_Cancer_Severity_Model.h5"
VALID_DIR  = r"model-final\chest-ctscan-images\valid"
OUT_PATH   = r"backend\static\severity_metrics.json"

# The severity model outputs 3 classes but only Benign/Malignant are tested here
# (Normal is handled by clinical rule in backend, never reaches the model)
SEVERITY_CLASSES = ["Normal", "Benign", "Malignant"]
INPUT_SIZE = (224, 224)

# Map folder → severity ground truth (skip normal folder)
FOLDER_MAP = {
    "adenocarcinoma_left.lower.lobe_T2_N0_M0_Ib":         1,  # Benign   (Stage I)
    "large.cell.carcinoma_left.hilum_T2_N2_M0_IIIa":      2,  # Malignant (Stage III)
    "squamous.cell.carcinoma_left.hilum_T1_N2_M0_IIIa":   2,  # Malignant (Stage III)
    # "normal" is intentionally excluded — handled by clinical rule
}

# ── Load model ─────────────────────────────────────────────────────────────────
print("Loading severity model...", flush=True)
model = keras.models.load_model(MODEL_PATH, compile=False)
print(f"  input={model.input_shape}", flush=True)

# ── Collect cancer images only ──────────────────────────────────────────────────
print("\nCollecting cancer images (excluding normal — handled by clinical rule)...", flush=True)
X, y_true = [], []

for folder_name, sev_idx in FOLDER_MAP.items():
    folder_path = os.path.join(VALID_DIR, folder_name)
    if not os.path.isdir(folder_path):
        print(f"  [MISSING] {folder_name}"); continue
    imgs = glob.glob(os.path.join(folder_path, "*.png")) + glob.glob(os.path.join(folder_path, "*.jpg"))
    print(f"  {SEVERITY_CLASSES[sev_idx]:12s} | {folder_name[:55]:55s} ({len(imgs)} imgs)")
    for p in imgs:
        img = Image.open(p).convert("RGB").resize(INPUT_SIZE, Image.LANCZOS)
        arr = np.array(img, dtype=np.float32) / 255.0
        X.append(arr)
        y_true.append(sev_idx)

X      = np.array(X, dtype=np.float32)
y_true = np.array(y_true, dtype=np.int32)
print(f"\nTotal cancer samples: {len(X)}")
dist = {SEVERITY_CLASSES[i]: int((y_true==i).sum()) for i in range(len(SEVERITY_CLASSES))}
print(f"Distribution: {dist}")

# ── Inference ──────────────────────────────────────────────────────────────────
BATCH = 8
print("\nRunning inference...", flush=True)
preds_all = []
for i in range(0, len(X), BATCH):
    out = model(tf.constant(X[i:i+BATCH]), training=False).numpy()
    preds_all.append(out)

preds_all = np.concatenate(preds_all, axis=0)   # (N, 3)
y_pred    = np.argmax(preds_all, axis=1)          # (N,)

# ── Metrics (full 3-class, though Normal has 0 support in ground truth) ─────────
def safe_div(a, b): return a / b if b > 0 else 0.0

n_classes = len(SEVERITY_CLASSES)
n_total   = len(y_true)

cm = np.zeros((n_classes, n_classes), dtype=int)
for t, p in zip(y_true, y_pred):
    cm[t, p] += 1

print("\nConfusion Matrix (rows=actual, cols=predicted):")
print("          " + "  ".join(f"{c[:9]:>9}" for c in SEVERITY_CLASSES))
for i, cls in enumerate(SEVERITY_CLASSES):
    print(f"  {cls[:9]:9}  " + "  ".join(f"{v:9d}" for v in cm[i]))

per_class = {}
support_total_active = 0  # only classes with support

for i, cls in enumerate(SEVERITY_CLASSES):
    tp = cm[i, i]
    fp = cm[:, i].sum() - tp
    fn = cm[i, :].sum() - tp
    support = cm[i, :].sum()

    prec = safe_div(tp, tp + fp)
    rec  = safe_div(tp, tp + fn)
    f1   = safe_div(2 * prec * rec, prec + rec)

    per_class[cls] = {
        "precision": round(prec * 100, 2),
        "recall":    round(rec  * 100, 2),
        "f1_score":  round(f1   * 100, 2),
        "support":   int(support),
    }
    if support > 0:
        support_total_active += support
    print(f"  {cls}: P={prec*100:.1f}%  R={rec*100:.1f}%  F1={f1*100:.1f}%  n={support}")

# Accuracy over cancer images only
accuracy = int(np.sum(y_pred == y_true)) / n_total * 100

# Weighted averages over classes WITH support (Benign + Malignant)
w_prec = w_rec = w_f1 = 0.0
m_prec = m_rec = m_f1 = 0.0
active_classes = [c for c in SEVERITY_CLASSES if per_class[c]["support"] > 0]

for cls in active_classes:
    w = per_class[cls]["support"] / support_total_active
    w_prec += per_class[cls]["precision"] * w
    w_rec  += per_class[cls]["recall"]    * w
    w_f1   += per_class[cls]["f1_score"]  * w

for cls in active_classes:
    m_prec += per_class[cls]["precision"]
    m_rec  += per_class[cls]["recall"]
    m_f1   += per_class[cls]["f1_score"]
n_active = len(active_classes)
m_prec /= n_active; m_rec /= n_active; m_f1 /= n_active

print(f"\n{'─'*50}")
print(f"  Accuracy (cancer set): {accuracy:.2f}%")
print(f"  Weighted Precision:    {w_prec:.2f}%")
print(f"  Weighted Recall:       {w_rec:.2f}%")
print(f"  Weighted F1-Score:     {w_f1:.2f}%")
print(f"  Macro Precision:       {m_prec:.2f}%")
print(f"  Macro Recall:          {m_rec:.2f}%")
print(f"  Macro F1-Score:        {m_f1:.2f}%")
print(f"  Total eval samples:    {n_total}")

metrics = {
    "overall": {
        "accuracy":            round(accuracy, 2),
        "weighted_precision":  round(w_prec,   2),
        "weighted_recall":     round(w_rec,    2),
        "weighted_f1":         round(w_f1,     2),
        "macro_precision":     round(m_prec,   2),
        "macro_recall":        round(m_rec,    2),
        "macro_f1":            round(m_f1,     2),
        "total_test_samples":  int(n_total),
        "eval_set":            "validation (cancer images only)",
        "note":                "Normal severity handled by clinical rule (not model); evaluated on Benign (Stage I) and Malignant (Stage III) cancer images"
    },
    "per_class": per_class,
    "class_labels": SEVERITY_CLASSES,
    "confusion_matrix": cm.tolist(),
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print(f"\nSaved → {OUT_PATH}")

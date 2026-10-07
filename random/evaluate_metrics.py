"""
Full test-set evaluation: Accuracy, Precision, Recall, F1-Score (per class + weighted avg)
Output is saved to model_metrics.json for the backend to serve.
"""
import sys, os, glob, json
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"C:\Users\trija\Documents\LungDetection")

import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.resnet50 import preprocess_input

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH = r"model-final\Lung_Cancer_ResNet50_88Acc.keras"
TEST_DIR   = r"model-final\chest-ctscan-images\test"
OUT_PATH   = r"backend\static\model_metrics.json"

CLASSES = [
    "adenocarcinoma",
    "large.cell.carcinoma",
    "normal",
    "squamous.cell.carcinoma",
]
INPUT_SIZE = (460, 460)

# ── Load model ────────────────────────────────────────────────────────────────
print("Loading model...", flush=True)
model = keras.models.load_model(MODEL_PATH, compile=False)
print(f"  input={model.input_shape}", flush=True)

# ── Collect all test images ───────────────────────────────────────────────────
print("\nCollecting test images...", flush=True)
X, y_true = [], []
for cls_idx, cls in enumerate(CLASSES):
    cls_dir = os.path.join(TEST_DIR, cls)
    imgs = glob.glob(os.path.join(cls_dir, "*.png")) + glob.glob(os.path.join(cls_dir, "*.jpg"))
    print(f"  {cls}: {len(imgs)} images")
    for p in imgs:
        img = Image.open(p).convert("RGB").resize(INPUT_SIZE, Image.LANCZOS)
        arr = preprocess_input(np.array(img, dtype=np.float32))
        X.append(arr)
        y_true.append(cls_idx)

X      = np.array(X, dtype=np.float32)    # (N, 460, 460, 3)
y_true = np.array(y_true, dtype=np.int32) # (N,)
print(f"\nTotal samples: {len(X)}", flush=True)

# ── Run inference in batches ──────────────────────────────────────────────────
BATCH = 8
print("Running inference...", flush=True)
preds_all = []
for i in range(0, len(X), BATCH):
    batch = tf.constant(X[i:i+BATCH])
    out   = model(batch, training=False).numpy()
    preds_all.append(out)
    if (i // BATCH) % 5 == 0:
        print(f"  batch {i//BATCH+1}/{(len(X)-1)//BATCH+1}", flush=True)

preds_all = np.concatenate(preds_all, axis=0)  # (N, 4)
y_pred    = np.argmax(preds_all, axis=1)        # (N,)

# ── Compute metrics ───────────────────────────────────────────────────────────
def safe_div(a, b): return a / b if b > 0 else 0.0

n_classes = len(CLASSES)
n_total   = len(y_true)

# Confusion matrix
cm = np.zeros((n_classes, n_classes), dtype=int)
for t, p in zip(y_true, y_pred):
    cm[t, p] += 1

print("\nConfusion Matrix:")
print("         " + "  ".join(f"{c[:6]:>6}" for c in ["Adeno", "Large", "Normal", "Squam"]))
for i, row in enumerate(cm):
    print(f"  {CLASSES[i][:6]:6}  " + "  ".join(f"{v:6d}" for v in row))

# Per-class metrics
per_class = {}
tp_total = fp_total = fn_total = support_total = 0

for i, cls in enumerate(CLASSES):
    tp = cm[i, i]
    fp = cm[:, i].sum() - tp
    fn = cm[i, :].sum() - tp
    support = cm[i, :].sum()

    prec   = safe_div(tp, tp + fp)
    rec    = safe_div(tp, tp + fn)
    f1     = safe_div(2 * prec * rec, prec + rec)

    per_class[cls] = {
        "precision": round(prec * 100, 2),
        "recall":    round(rec  * 100, 2),
        "f1_score":  round(f1   * 100, 2),
        "support":   int(support),
    }

    tp_total      += tp
    fp_total      += fp
    fn_total      += fn
    support_total += support

    print(f"  {cls}: P={prec*100:.1f}%  R={rec*100:.1f}%  F1={f1*100:.1f}%  n={support}")

# Overall accuracy
accuracy = int(np.sum(y_pred == y_true)) / n_total * 100

# Weighted averages
w_prec = w_rec = w_f1 = 0.0
for i, cls in enumerate(CLASSES):
    w = per_class[cls]["support"] / support_total
    w_prec += per_class[cls]["precision"] * w
    w_rec  += per_class[cls]["recall"]    * w
    w_f1   += per_class[cls]["f1_score"]  * w

# Macro averages
m_prec = np.mean([per_class[c]["precision"] for c in CLASSES])
m_rec  = np.mean([per_class[c]["recall"]    for c in CLASSES])
m_f1   = np.mean([per_class[c]["f1_score"]  for c in CLASSES])

print(f"\n{'─'*50}")
print(f"  Accuracy (overall): {accuracy:.2f}%")
print(f"  Weighted Precision: {w_prec:.2f}%")
print(f"  Weighted Recall:    {w_rec:.2f}%")
print(f"  Weighted F1-Score:  {w_f1:.2f}%")
print(f"  Macro Precision:    {m_prec:.2f}%")
print(f"  Macro Recall:       {m_rec:.2f}%")
print(f"  Macro F1-Score:     {m_f1:.2f}%")
print(f"  Total test samples: {n_total}")

# ── Save JSON ─────────────────────────────────────────────────────────────────
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
    },
    "per_class": per_class,
    "class_labels": CLASSES,
    "confusion_matrix": cm.tolist(),
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
print(f"\nSaved → {OUT_PATH}")

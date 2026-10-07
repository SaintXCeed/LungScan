"""
Script untuk menambahkan sel-sel visualisasi ke notebook482bfa0c7a-refactored.ipynb
"""
import json, copy, os

NB_PATH = r"C:\Users\trija\Documents\LungDetection\model-final\notebook482bfa0c7a-refactored.ipynb"

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# ── Idempotency check: jangan modifikasi jika sudah pernah dijalankan ─────────
for _c in nb["cells"]:
    if "Visualisasi 1" in "".join(_c.get("source", [])):
        print("[INFO] Notebook sudah dimodifikasi sebelumnya (ditemukan sel Visualisasi 1).")
        print("[INFO] Tidak ada perubahan yang dilakukan.")
        exit(0)

def make_md(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [text]
    }

def make_code(lines):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines if isinstance(lines, list) else [lines]
    }

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 1: Distribusi Dataset (setelah cell Data Preparation = index 3)
# ─────────────────────────────────────────────────────────────────────────────
vis1_md = make_md("## Visualisasi 1 — Distribusi Dataset per Kelas\nMenampilkan jumlah gambar pada setiap split (Train / Validasi / Test) untuk masing-masing kelas.")

vis1_code = make_code("""\
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

splits = {"Train": TRAIN_PATH, "Validasi": VAL_PATH, "Test": TEST_PATH}
split_counts = {}

for split_name, path in splits.items():
    counts = {}
    if os.path.isdir(path):
        for cls in CLASS_NAMES:
            cls_path = os.path.join(path, cls)
            if os.path.isdir(cls_path):
                counts[cls] = len([f for f in os.listdir(cls_path)
                                   if os.path.isfile(os.path.join(cls_path, f))])
            else:
                counts[cls] = 0
    split_counts[split_name] = counts

x = np.arange(len(CLASS_NAMES))
width = 0.25
colors = ["#3b82f6", "#10b981", "#f59e0b"]

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

for i, (split_name, color) in enumerate(zip(splits.keys(), colors)):
    vals = [split_counts[split_name].get(cls, 0) for cls in CLASS_NAMES]
    bars = ax.bar(x + i * width, vals, width, label=split_name, color=color, alpha=0.9)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                str(int(bar.get_height())), ha="center", va="bottom",
                fontsize=9, color="white")

short_names = [cls.replace("_", "\\n") for cls in CLASS_NAMES]
ax.set_xticks(x + width)
ax.set_xticklabels(short_names, color="white", fontsize=10)
ax.set_title("Distribusi Jumlah Gambar per Kelas dan Split Dataset", fontsize=14,
             fontweight="bold", color="white", pad=15)
ax.set_xlabel("Kelas", color="white"); ax.set_ylabel("Jumlah Gambar", color="white")
ax.tick_params(colors="white"); ax.spines[:].set_color("#475569")
ax.legend(facecolor="#0f172a", labelcolor="white", fontsize=10)
ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="white")
plt.tight_layout()
plt.savefig("viz_dataset_distribution.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print("Gambar disimpan: viz_dataset_distribution.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 2: Contoh Gambar per Kelas (setelah vis1)
# ─────────────────────────────────────────────────────────────────────────────
vis2_md = make_md("## Visualisasi 2 — Contoh Gambar CT-Scan per Kelas\nMenampilkan 3 sampel gambar dari masing-masing kelas dalam dataset train.")

vis2_code = make_code("""\
from PIL import Image
import matplotlib.pyplot as plt
import os, random

N_SAMPLES = 3
fig, axes = plt.subplots(len(CLASS_NAMES), N_SAMPLES,
                         figsize=(N_SAMPLES * 3.5, len(CLASS_NAMES) * 3.2))
fig.patch.set_facecolor("#0f172a")
fig.suptitle("Contoh Gambar CT-Scan per Kelas — Dataset Train",
             fontsize=14, fontweight="bold", color="white", y=1.01)

cls_colors = ["#ef4444", "#f97316", "#a855f7", "#22c55e"]

for row, (cls, color) in enumerate(zip(CLASS_NAMES, cls_colors)):
    cls_path = os.path.join(TRAIN_PATH, cls)
    files = [f for f in os.listdir(cls_path)
             if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    samples = random.sample(files, min(N_SAMPLES, len(files)))
    for col, fname in enumerate(samples):
        ax = axes[row][col]
        img = Image.open(os.path.join(cls_path, fname)).convert("RGB")
        ax.imshow(img)
        ax.axis("off")
        ax.set_facecolor("#0f172a")
        if col == 0:
            ax.set_ylabel(cls, fontsize=10, color=color, fontweight="bold",
                          rotation=90, labelpad=8)
        if row == 0:
            ax.set_title(f"Sampel {col+1}", fontsize=9, color="white")
        for spine in ax.spines.values():
            spine.set_edgecolor(color); spine.set_linewidth(2)
            spine.set_visible(True)

plt.tight_layout()
plt.savefig("viz_sample_images.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print("Gambar disimpan: viz_sample_images.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 3: Contoh Augmentasi (setelah cell Augmentation = index 5)
# ─────────────────────────────────────────────────────────────────────────────
vis3_md = make_md("## Visualisasi 3 — Contoh Efek Augmentasi Data\nMenampilkan pengaruh setiap transformasi augmentasi terhadap satu gambar sampel dari masing-masing kelas.")

vis3_code = make_code("""\
import torchvision.transforms as T
from PIL import Image
import matplotlib.pyplot as plt
import os, random, torch
import numpy as np

# Daftar augmentasi individual untuk divisualisasi
aug_list = [
    ("Original",             T.Compose([T.Resize(IMG_SIZE)])),
    ("Horizontal Flip",      T.Compose([T.Resize(IMG_SIZE), T.RandomHorizontalFlip(p=1.0)])),
    ("Vertical Flip",        T.Compose([T.Resize(IMG_SIZE), T.RandomVerticalFlip(p=1.0)])),
    ("Rotasi 25°",           T.Compose([T.Resize(IMG_SIZE), T.RandomRotation((25, 25))])),
    ("Color Jitter",         T.Compose([T.Resize(IMG_SIZE),
                                        T.ColorJitter(brightness=0.4, contrast=0.4)])),
]

n_aug  = len(aug_list)
n_cls  = min(2, len(CLASS_NAMES))   # tampilkan 2 kelas agar tidak terlalu panjang

fig, axes = plt.subplots(n_cls, n_aug, figsize=(n_aug * 3, n_cls * 3.2))
fig.patch.set_facecolor("#0f172a")
fig.suptitle("Efek Augmentasi Data per Kelas — Perbandingan Transformasi",
             fontsize=13, fontweight="bold", color="white", y=1.02)

for row, cls in enumerate(CLASS_NAMES[:n_cls]):
    cls_path = os.path.join(TRAIN_PATH, cls)
    files = [f for f in os.listdir(cls_path)
             if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    img_path = os.path.join(cls_path, random.choice(files))
    img_pil  = Image.open(img_path).convert("RGB")

    for col, (aug_name, aug_tf) in enumerate(aug_list):
        ax = axes[row][col] if n_cls > 1 else axes[col]
        aug_img = aug_tf(img_pil)
        ax.imshow(aug_img)
        ax.axis("off")
        ax.set_facecolor("#0f172a")
        if row == 0:
            ax.set_title(aug_name, fontsize=9, color="#94a3b8", pad=4)
        if col == 0:
            ax.set_ylabel(cls, fontsize=9, color="#10b981",
                          fontweight="bold", rotation=90, labelpad=6)

plt.tight_layout()
plt.savefig("viz_augmentation_examples.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print("Gambar disimpan: viz_augmentation_examples.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 4: Class Weights (setelah cell Class Weights = index 9)
# ─────────────────────────────────────────────────────────────────────────────
vis4_md = make_md("## Visualisasi 4 — Bobot Kelas (Class Weights)\nBobot dihitung untuk menangani ketidakseimbangan data. Kelas dengan sedikit sampel mendapat bobot lebih tinggi.")

vis4_code = make_code("""\
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 5))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

weights = list(class_weights_dict.values())
colors  = ["#ef4444", "#f97316", "#a855f7", "#22c55e"][:len(CLASS_NAMES)]

bars = ax.bar(CLASS_NAMES, weights, color=colors, alpha=0.9, width=0.5)
for bar, w in zip(bars, weights):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{w:.4f}", ha="center", va="bottom", fontsize=11,
            fontweight="bold", color="white")

ax.set_title("Bobot Kelas untuk Menangani Class Imbalance",
             fontsize=13, fontweight="bold", color="white", pad=12)
ax.set_xlabel("Kelas", color="white"); ax.set_ylabel("Bobot (Weight)", color="white")
ax.tick_params(colors="white"); ax.spines[:].set_color("#475569")
ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="white")
plt.tight_layout()
plt.savefig("viz_class_weights.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print("Gambar disimpan: viz_class_weights.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 5: Training History Diperkaya (ganti sel index 14)
# ─────────────────────────────────────────────────────────────────────────────
vis5_md = make_md("## Visualisasi 5 — Riwayat Pelatihan (Loss & Akurasi)\nGrafik menampilkan kurva Loss dan Akurasi pada data latih dan validasi, dengan pembatas antar fase pelatihan.")

vis5_code = make_code("""\
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

n_ep    = len(train_acc_hist)
epochs  = range(1, n_ep + 1)

# Hitung batas fase — Phase 1 = 10 epoch (atau sampai early stop)
# Fase 2 dimulai setelah fase 1 selesai
# Simpan panjang fase di variabel global jika tersedia, fallback ke 10
phase1_end = getattr(__builtins__, '__phase1_end__', min(10, n_ep))

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("#0f172a")
fig.suptitle("Riwayat Pelatihan ResNet50 — Two-Phase Transfer Learning",
             fontsize=14, fontweight="bold", color="white", y=1.02)

for ax in axes:
    ax.set_facecolor("#1e293b")
    ax.tick_params(colors="white")
    ax.spines[:].set_color("#475569")
    ax.xaxis.grid(True, linestyle="--", alpha=0.2, color="white")
    ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")
    if phase1_end < n_ep:
        ax.axvline(x=phase1_end + 0.5, color="#f59e0b", linestyle="--",
                   linewidth=1.5, alpha=0.8)
        ax.text(phase1_end * 0.5, ax.get_ylim()[0] if ax.get_ylim()[0] != 0 else 0.01,
                "Fase 1", ha="center", fontsize=8, color="#f59e0b", alpha=0.9)
        ax.text(phase1_end + (n_ep - phase1_end) * 0.5, 0.01,
                "Fase 2", ha="center", fontsize=8, color="#f59e0b", alpha=0.9)

# Akurasi
axes[0].plot(epochs, train_acc_hist, "#3b82f6", linewidth=2, label="Train")
axes[0].plot(epochs, val_acc_hist,   "#10b981", linewidth=2, label="Validasi",
             linestyle="--")
axes[0].set_title("Akurasi", color="white", fontsize=12)
axes[0].set_xlabel("Epoch", color="white"); axes[0].set_ylabel("Akurasi", color="white")
axes[0].legend(facecolor="#0f172a", labelcolor="white")

# Loss
axes[1].plot(epochs, train_loss_hist, "#f87171", linewidth=2, label="Train")
axes[1].plot(epochs, val_loss_hist,   "#fb923c", linewidth=2, label="Validasi",
             linestyle="--")
axes[1].set_title("Loss", color="white", fontsize=12)
axes[1].set_xlabel("Epoch", color="white"); axes[1].set_ylabel("Loss", color="white")
axes[1].legend(facecolor="#0f172a", labelcolor="white")

plt.tight_layout()
plt.savefig("viz_training_history.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print("Gambar disimpan: viz_training_history.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 6: Tabel Metrik + ROC Curve + Confidence (setelah evaluasi)
# ─────────────────────────────────────────────────────────────────────────────
vis6_md = make_md("## Visualisasi 6 — Metrik Evaluasi (Tabel & Grafik)")

vis6_code = make_code("""\
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
import torch, torch.nn.functional as F
import numpy as np

# ── Tabel Metrik ─────────────────────────────────────────────────────────────
df_metrics = pd.DataFrame([metrics])
print("=== Tabel Metrik Evaluasi ===")
display(df_metrics.style
        .format("{:.4f}")
        .background_gradient(cmap="RdYlGn", axis=1)
        .set_caption("Metrik Evaluasi ResNet50 pada Test Set"))

# ── ROC Curve ────────────────────────────────────────────────────────────────
n_cls   = len(CLASS_NAMES)
y_bin   = label_binarize(y_true, classes=list(range(n_cls)))

all_probs = []
resnet50.eval()
with torch.no_grad():
    for imgs, _ in test_loader:
        imgs  = imgs.to(device)
        probs = F.softmax(resnet50(imgs), dim=1)
        all_probs.extend(probs.cpu().numpy())
all_probs = np.array(all_probs)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("#0f172a")
colors_roc = ["#ef4444", "#f97316", "#a855f7", "#22c55e"]

ax = axes[0]
ax.set_facecolor("#1e293b"); ax.tick_params(colors="white")
ax.spines[:].set_color("#475569")
ax.plot([0, 1], [0, 1], "w--", linewidth=1, alpha=0.4, label="Acak (AUC=0.50)")

for i, (cls, color) in enumerate(zip(CLASS_NAMES, colors_roc)):
    fpr, tpr, _ = roc_curve(y_bin[:, i], all_probs[:, i])
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr, color=color, linewidth=2,
            label=f"{cls}  (AUC = {roc_auc:.3f})")

ax.set_title("Kurva ROC per Kelas — One-vs-Rest",
             color="white", fontsize=12, fontweight="bold")
ax.set_xlabel("False Positive Rate", color="white")
ax.set_ylabel("True Positive Rate", color="white")
ax.legend(facecolor="#0f172a", labelcolor="white", fontsize=8, loc="lower right")
ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")

# ── Distribusi Confidence ─────────────────────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor("#1e293b"); ax2.tick_params(colors="white")
ax2.spines[:].set_color("#475569")

conf_vals = np.max(all_probs, axis=1)
ax2.hist(conf_vals, bins=20, color="#3b82f6", edgecolor="#0f172a", alpha=0.9)
ax2.axvline(conf_vals.mean(), color="#10b981", linewidth=2,
            linestyle="--", label=f"Rata-rata: {conf_vals.mean():.2%}")
ax2.set_title("Distribusi Skor Keyakinan (Confidence) — Test Set",
              color="white", fontsize=12, fontweight="bold")
ax2.set_xlabel("Skor Confidence", color="white")
ax2.set_ylabel("Jumlah Gambar", color="white")
ax2.legend(facecolor="#0f172a", labelcolor="white")
ax2.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")

plt.tight_layout()
plt.savefig("viz_roc_confidence.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print(f"Confidence  rata-rata: {conf_vals.mean():.2%}  |  max: {conf_vals.max():.2%}  |  min: {conf_vals.min():.2%}")
print("Gambar disimpan: viz_roc_confidence.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALISASI 7: Per-Class Metrics Bar Chart (setelah confusion matrix)
# ─────────────────────────────────────────────────────────────────────────────
vis7_md = make_md("## Visualisasi 7 — Precision, Recall, F1 per Kelas\nGrafik batang perbandingan tiga metrik utama untuk setiap kelas.")

vis7_code = make_code("""\
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

# Hitung per-class metrics
prec_per  = precision_score(y_true, y_pred, average=None, zero_division=0) * 100
rec_per   = recall_score   (y_true, y_pred, average=None, zero_division=0) * 100
f1_per    = f1_score       (y_true, y_pred, average=None, zero_division=0) * 100

x      = np.arange(len(CLASS_NAMES))
width  = 0.25

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

b1 = ax.bar(x - width,     prec_per, width, label="Precision", color="#3b82f6", alpha=0.9)
b2 = ax.bar(x,             rec_per,  width, label="Recall",    color="#10b981", alpha=0.9)
b3 = ax.bar(x + width,     f1_per,   width, label="F1-Score",  color="#f59e0b", alpha=0.9)

for bars in [b1, b2, b3]:
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                f"{h:.1f}%", ha="center", va="bottom", fontsize=8, color="white")

ax.set_xticks(x); ax.set_xticklabels(CLASS_NAMES, color="white", fontsize=9)
ax.set_ylim(0, 115)
ax.set_title("Precision, Recall, dan F1-Score per Kelas — Test Set",
             fontsize=13, fontweight="bold", color="white", pad=12)
ax.set_xlabel("Kelas", color="white"); ax.set_ylabel("Nilai (%)", color="white")
ax.tick_params(colors="white"); ax.spines[:].set_color("#475569")
ax.legend(facecolor="#0f172a", labelcolor="white", fontsize=10)
ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="white")

plt.tight_layout()
plt.savefig("viz_per_class_metrics.png", dpi=150, bbox_inches="tight",
            facecolor="#0f172a")
plt.show()
print("Gambar disimpan: viz_per_class_metrics.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# INJECT CELLS KE DALAM NOTEBOOK
# ─────────────────────────────────────────────────────────────────────────────
# Temukan posisi berdasarkan heading markdown
def find_cell_index(nb, keyword):
    for i, cell in enumerate(nb["cells"]):
        src = "".join(cell.get("source", []))
        if keyword in src:
            return i
    return -1

new_cells = nb["cells"].copy()

# Cari setelah "# 2. Data Preparation"
idx = find_cell_index(nb, "# 2. Data Preparation")
# Sisipkan setelah kode Data Preparation (index+2 karena ada markdown+code)
insert_after = idx + 2
new_cells.insert(insert_after,     vis1_code)
new_cells.insert(insert_after,     vis1_md)
new_cells.insert(insert_after + 2, vis2_code)
new_cells.insert(insert_after + 2, vis2_md)

# Setelah "# 3. Data Augmentation" — sekarang offset bergeser +4
idx2 = next(i for i, c in enumerate(new_cells)
            if "# 3. Data Augmentation" in "".join(c.get("source", [])))
new_cells.insert(idx2 + 2, vis3_code)
new_cells.insert(idx2 + 2, vis3_md)

# Setelah "# 5. Class Weights"
idx3 = next(i for i, c in enumerate(new_cells)
            if "# 5. Class Weights" in "".join(c.get("source", [])))
new_cells.insert(idx3 + 2, vis4_code)
new_cells.insert(idx3 + 2, vis4_md)

# Ganti "# 8. Training History Visualization"
idx4 = next(i for i, c in enumerate(new_cells)
            if "# 8. Training History" in "".join(c.get("source", [])))
new_cells[idx4]     = vis5_md
new_cells[idx4 + 1] = vis5_code

# Setelah "# 9. Evaluasi pada Test Set"
idx5 = next(i for i, c in enumerate(new_cells)
            if "# 9. Evaluasi" in "".join(c.get("source", [])))
new_cells.insert(idx5 + 2, vis6_code)
new_cells.insert(idx5 + 2, vis6_md)

# Setelah "# 10. Classification Report"
idx6 = next(i for i, c in enumerate(new_cells)
            if "# 10. Classification" in "".join(c.get("source", [])))
new_cells.insert(idx6 + 2, vis7_code)
new_cells.insert(idx6 + 2, vis7_md)

nb["cells"] = new_cells

OUT_PATH = NB_PATH  # overwrite in-place
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print(f"Notebook diperbarui: {OUT_PATH}")
print(f"Total sel sekarang: {len(nb['cells'])}")

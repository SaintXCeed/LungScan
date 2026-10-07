"""
Script untuk menambahkan sel-sel visualisasi ke lung-cancer-severity-refactored.ipynb
"""
import json, os

NB_PATH = r"C:\Users\trija\Documents\LungDetection\model-final\lung-cancer-severity-refactored.ipynb"

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

def make_md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [text]}

def make_code(lines):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines if isinstance(lines, list) else [lines],
    }

def find_after(cells, keyword):
    """Return index of code cell AFTER the markdown containing keyword."""
    for i, c in enumerate(cells):
        if keyword in "".join(c.get("source", [])):
            # next cell is the code cell, return i+2 (insert after code)
            return i + 2
    return len(cells)

# ─────────────────────────────────────────────────────────────────────────────
# VIS 1 — Distribusi Dataset (setelah # 2. Data Preparation)
# ─────────────────────────────────────────────────────────────────────────────
vis1_md = make_md("## Visualisasi 1 — Distribusi Dataset per Kelas\nJumlah gambar per kelas sebelum augmentasi.")

vis1_code = make_code("""\
import matplotlib.pyplot as plt
import numpy as np
import os

counts = {}
for cls in CLASS_NAMES:
    p = os.path.join(base_dir, cls)
    counts[cls] = len([f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))])

fig, ax = plt.subplots(figsize=(9, 5))
fig.patch.set_facecolor("#0f172a")
ax.set_facecolor("#1e293b")

colors = ["#10b981", "#ef4444", "#3b82f6"]
bars   = ax.bar(CLASS_NAMES, counts.values(), color=colors, alpha=0.9, width=0.5)

for bar, v in zip(bars, counts.values()):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
            str(v), ha="center", va="bottom", fontsize=12,
            fontweight="bold", color="white")

ax.set_title("Distribusi Jumlah Gambar per Kelas — Dataset Asli",
             fontsize=13, fontweight="bold", color="white", pad=12)
ax.set_xlabel("Kelas", color="white"); ax.set_ylabel("Jumlah Gambar", color="white")
ax.tick_params(colors="white"); ax.spines[:].set_color("#475569")
ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="white")
plt.tight_layout()
plt.savefig("viz_sev_dataset_dist.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.show()
print("Disimpan: viz_sev_dataset_dist.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VIS 2 — Contoh Gambar per Kelas (setelah Vis 1)
# ─────────────────────────────────────────────────────────────────────────────
vis2_md = make_md("## Visualisasi 2 — Contoh Gambar CT-Scan per Kelas\n3 sampel dari masing-masing kelas dataset IQ-OTH/NCCD.")

vis2_code = make_code("""\
from PIL import Image
import matplotlib.pyplot as plt
import os, random

N = 3
cls_colors = ["#10b981", "#ef4444", "#3b82f6"]

fig, axes = plt.subplots(len(CLASS_NAMES), N,
                         figsize=(N * 3.5, len(CLASS_NAMES) * 3.2))
fig.patch.set_facecolor("#0f172a")
fig.suptitle("Contoh Gambar CT-Scan per Kelas — IQ-OTH/NCCD Dataset",
             fontsize=13, fontweight="bold", color="white", y=1.01)

for row, (cls, color) in enumerate(zip(CLASS_NAMES, cls_colors)):
    folder = os.path.join(base_dir, cls)
    files  = [f for f in os.listdir(folder)
              if os.path.isfile(os.path.join(folder, f))]
    samples = random.sample(files, min(N, len(files)))
    for col, fname in enumerate(samples):
        ax = axes[row][col]
        img = Image.open(os.path.join(folder, fname)).convert("RGB")
        ax.imshow(img, cmap="gray")
        ax.axis("off")
        ax.set_facecolor("#0f172a")
        if col == 0:
            ax.set_ylabel(cls, fontsize=10, color=color,
                          fontweight="bold", rotation=90, labelpad=8)
        if row == 0:
            ax.set_title(f"Sampel {col+1}", fontsize=9, color="white")
        for spine in ax.spines.values():
            spine.set_edgecolor(color); spine.set_linewidth(2); spine.set_visible(True)

plt.tight_layout()
plt.savefig("viz_sev_sample_images.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.show()
print("Disimpan: viz_sev_sample_images.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VIS 3 — Contoh Augmentasi (setelah # 4. Data Augmentation)
# ─────────────────────────────────────────────────────────────────────────────
vis3_md = make_md("## Visualisasi 3 — Contoh Augmentasi Data\nPerbandingan transformasi augmentasi yang diterapkan pada satu gambar sampel per kelas.")

vis3_code = make_code("""\
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
import os, random, copy

def apply_transforms(img):
    return [
        ("Original",       img.copy()),
        ("Flip Horizontal",img.transpose(Image.FLIP_LEFT_RIGHT)),
        ("Flip Vertikal",  img.transpose(Image.FLIP_TOP_BOTTOM)),
        ("Rotasi 25°",     img.rotate(25)),
        ("Kontras Tinggi", ImageEnhance.Contrast(img).enhance(1.6)),
        ("Sharpness",      ImageEnhance.Sharpness(img).enhance(2.0)),
    ]

n_cls = len(CLASS_NAMES)
n_aug = 6
cls_colors = ["#10b981", "#ef4444", "#3b82f6"]

fig, axes = plt.subplots(n_cls, n_aug, figsize=(n_aug * 2.8, n_cls * 3))
fig.patch.set_facecolor("#0f172a")
fig.suptitle("Efek Augmentasi Data per Kelas — Perbandingan Transformasi",
             fontsize=13, fontweight="bold", color="white", y=1.02)

for row, (cls, color) in enumerate(zip(CLASS_NAMES, cls_colors)):
    folder = os.path.join(base_dir, cls)
    files  = [f for f in os.listdir(folder)
              if os.path.isfile(os.path.join(folder, f))]
    img_path = os.path.join(folder, random.choice(files))
    img = Image.open(img_path).convert("RGB").resize((256, 256))
    transforms = apply_transforms(img)

    for col, (name, aug_img) in enumerate(transforms):
        ax = axes[row][col]
        ax.imshow(aug_img); ax.axis("off"); ax.set_facecolor("#0f172a")
        if row == 0:
            ax.set_title(name, fontsize=8, color="#94a3b8", pad=3)
        if col == 0:
            ax.set_ylabel(cls, fontsize=9, color=color,
                          fontweight="bold", rotation=90, labelpad=6)

plt.tight_layout()
plt.savefig("viz_sev_augmentation.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.show()
print("Disimpan: viz_sev_augmentation.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VIS 4 — Setelah Augmentasi: distribusi setelah TARGET_COUNT
# ─────────────────────────────────────────────────────────────────────────────
vis4_md = make_md("## Visualisasi 4 — Distribusi Dataset Setelah Augmentasi\nPerbandingan jumlah gambar sebelum dan sesudah proses penyeimbangan kelas.")

vis4_code = make_code("""\
import matplotlib.pyplot as plt
import numpy as np
import os

before = {}
after  = {}
for cls in CLASS_NAMES:
    src = os.path.join(base_dir, cls)
    before[cls] = len([f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))])
    dst = os.path.join(TRAIN_DIR, cls)
    after[cls]  = len([f for f in os.listdir(dst) if os.path.isfile(os.path.join(dst, f))])

x = np.arange(len(CLASS_NAMES)); width = 0.35
colors_b = ["#64748b", "#475569", "#334155"]
colors_a = ["#10b981", "#ef4444", "#3b82f6"]

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor("#0f172a"); ax.set_facecolor("#1e293b")

b1 = ax.bar(x - width/2, before.values(), width, label="Sebelum Augmentasi",
            color=colors_b, alpha=0.85)
b2 = ax.bar(x + width/2, after.values(),  width, label="Setelah Augmentasi",
            color=colors_a, alpha=0.9)

for bars in [b1, b2]:
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                str(int(bar.get_height())), ha="center", va="bottom",
                fontsize=10, color="white")

ax.set_xticks(x); ax.set_xticklabels(CLASS_NAMES, color="white")
ax.set_title("Distribusi Dataset: Sebelum vs Setelah Augmentasi",
             fontsize=13, fontweight="bold", color="white", pad=12)
ax.set_xlabel("Kelas", color="white"); ax.set_ylabel("Jumlah Gambar", color="white")
ax.tick_params(colors="white"); ax.spines[:].set_color("#475569")
ax.legend(facecolor="#0f172a", labelcolor="white")
ax.yaxis.grid(True, linestyle="--", alpha=0.3, color="white")
plt.tight_layout()
plt.savefig("viz_sev_aug_before_after.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.show()
print("Disimpan: viz_sev_aug_before_after.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VIS 5 — Training History Diperkaya (ganti sel # 9. Evaluasi)
# ─────────────────────────────────────────────────────────────────────────────
vis5_md = make_md("## Visualisasi 5 — Riwayat Pelatihan Model (Loss & Akurasi)")

vis5_code = make_code("""\
import matplotlib.pyplot as plt

n_ep   = len(train_acc_hist)
epochs = range(1, n_ep + 1)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor("#0f172a")
fig.suptitle("Riwayat Pelatihan ResNet50 — Severity Classification",
             fontsize=14, fontweight="bold", color="white", y=1.02)

for ax in axes:
    ax.set_facecolor("#1e293b"); ax.tick_params(colors="white")
    ax.spines[:].set_color("#475569")
    ax.xaxis.grid(True, linestyle="--", alpha=0.2, color="white")
    ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")

axes[0].plot(epochs, train_acc_hist, "#3b82f6", linewidth=2, label="Train")
axes[0].plot(epochs, val_acc_hist,   "#10b981", linewidth=2,
             label="Validasi", linestyle="--")
axes[0].set_title("Akurasi per Epoch", color="white", fontsize=12)
axes[0].set_xlabel("Epoch", color="white"); axes[0].set_ylabel("Akurasi", color="white")
axes[0].legend(facecolor="#0f172a", labelcolor="white")

axes[1].plot(epochs, train_loss_hist, "#f87171", linewidth=2, label="Train")
axes[1].plot(epochs, val_loss_hist,   "#fb923c", linewidth=2,
             label="Validasi", linestyle="--")
axes[1].set_title("Loss per Epoch", color="white", fontsize=12)
axes[1].set_xlabel("Epoch", color="white"); axes[1].set_ylabel("Loss", color="white")
axes[1].legend(facecolor="#0f172a", labelcolor="white")

plt.tight_layout()
plt.savefig("viz_sev_training_history.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.show()
print("Disimpan: viz_sev_training_history.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# VIS 6 — ROC + Confidence + Per-Class metrics (setelah evaluasi)
# ─────────────────────────────────────────────────────────────────────────────
vis6_md = make_md("## Visualisasi 6 — Kurva ROC, Distribusi Confidence & Metrik per Kelas")

vis6_code = make_code("""\
import matplotlib.pyplot as plt
import numpy as np
import torch, torch.nn.functional as F
from sklearn.metrics import roc_curve, auc, precision_score, recall_score, f1_score
from sklearn.preprocessing import label_binarize

n_cls  = len(CLASS_NAMES)
y_bin  = label_binarize(y_true, classes=list(range(n_cls)))

# Kumpulkan probabilitas
all_probs = []
resnet50.eval()
with torch.no_grad():
    for imgs, _ in val_loader:
        probs = F.softmax(resnet50(imgs.to(device)), dim=1)
        all_probs.extend(probs.cpu().numpy())
all_probs = np.array(all_probs)

colors_roc = ["#10b981", "#ef4444", "#3b82f6"]

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.patch.set_facecolor("#0f172a")

# ── ROC ──────────────────────────────────────────────────────────────────────
ax = axes[0]
ax.set_facecolor("#1e293b"); ax.tick_params(colors="white"); ax.spines[:].set_color("#475569")
ax.plot([0,1],[0,1],"w--", alpha=0.4, label="Acak (AUC=0.50)")
for i, (cls, c) in enumerate(zip(CLASS_NAMES, colors_roc)):
    fpr, tpr, _ = roc_curve(y_bin[:, i], all_probs[:, i])
    ax.plot(fpr, tpr, color=c, linewidth=2, label=f"{cls} (AUC={auc(fpr,tpr):.3f})")
ax.set_title("Kurva ROC per Kelas", color="white", fontsize=11, fontweight="bold")
ax.set_xlabel("FPR", color="white"); ax.set_ylabel("TPR", color="white")
ax.legend(facecolor="#0f172a", labelcolor="white", fontsize=8, loc="lower right")
ax.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")

# ── Confidence ───────────────────────────────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor("#1e293b"); ax2.tick_params(colors="white"); ax2.spines[:].set_color("#475569")
conf = np.max(all_probs, axis=1)
ax2.hist(conf, bins=20, color="#3b82f6", edgecolor="#0f172a", alpha=0.9)
ax2.axvline(conf.mean(), color="#10b981", linewidth=2, linestyle="--",
            label=f"Rata-rata: {conf.mean():.2%}")
ax2.set_title("Distribusi Confidence — Validasi", color="white", fontsize=11, fontweight="bold")
ax2.set_xlabel("Confidence Score", color="white"); ax2.set_ylabel("Jumlah", color="white")
ax2.legend(facecolor="#0f172a", labelcolor="white")
ax2.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")

# ── Per-class bar ─────────────────────────────────────────────────────────────
ax3 = axes[2]
ax3.set_facecolor("#1e293b"); ax3.tick_params(colors="white"); ax3.spines[:].set_color("#475569")
x = np.arange(n_cls); w = 0.25
prec = precision_score(y_true, y_pred, average=None, zero_division=0) * 100
rec  = recall_score   (y_true, y_pred, average=None, zero_division=0) * 100
f1   = f1_score       (y_true, y_pred, average=None, zero_division=0) * 100
for bars, vals, label, color in [
    (ax3.bar(x-w, prec, w, color="#3b82f6", alpha=0.9), prec, "Precision", "#3b82f6"),
    (ax3.bar(x,   rec,  w, color="#10b981", alpha=0.9), rec,  "Recall",    "#10b981"),
    (ax3.bar(x+w, f1,   w, color="#f59e0b", alpha=0.9), f1,   "F1",        "#f59e0b"),
]:
    pass
ax3.bar(x-w, prec, w, color="#3b82f6", alpha=0.9, label="Precision")
ax3.bar(x,   rec,  w, color="#10b981", alpha=0.9, label="Recall")
ax3.bar(x+w, f1,   w, color="#f59e0b", alpha=0.9, label="F1-Score")
ax3.set_xticks(x); ax3.set_xticklabels(CLASS_NAMES, color="white", fontsize=8)
ax3.set_ylim(0, 115)
ax3.set_title("Precision / Recall / F1 per Kelas", color="white", fontsize=11, fontweight="bold")
ax3.set_ylabel("Nilai (%)", color="white")
ax3.legend(facecolor="#0f172a", labelcolor="white", fontsize=8)
ax3.yaxis.grid(True, linestyle="--", alpha=0.2, color="white")

plt.tight_layout()
plt.savefig("viz_sev_roc_metrics.png", dpi=150, bbox_inches="tight", facecolor="#0f172a")
plt.show()
print("Disimpan: viz_sev_roc_metrics.png")
""")

# ─────────────────────────────────────────────────────────────────────────────
# INJECT CELLS
# ─────────────────────────────────────────────────────────────────────────────
cells = nb["cells"].copy()

def idx_after(cells, keyword):
    for i, c in enumerate(cells):
        if keyword in "".join(c.get("source", [])):
            return i + 2
    return len(cells)

insertions = [
    # (keyword untuk cari posisi, list sel yang diinsert SETELAH code cell-nya)
    ("# 2. Data Preparation",     [vis1_md, vis1_code, vis2_md, vis2_code]),
    ("# 3. Data Splitting",       [vis4_md, vis4_code]),   # after split = after aug section
    ("# 4. Data Augmentation",    [vis3_md, vis3_code]),
    ("# 8. Training Loop",        [vis5_md, vis5_code]),
    ("# 9. Evaluasi",             [vis6_md, vis6_code]),
]

offset = 0
for keyword, new_cells in insertions:
    pos = idx_after(nb["cells"], keyword) + offset
    for j, cell in enumerate(new_cells):
        cells.insert(pos + j, cell)
    offset += len(new_cells)

nb["cells"] = cells

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print(f"Notebook diperbarui: {NB_PATH}")
print(f"Total sel sekarang : {len(nb['cells'])}")

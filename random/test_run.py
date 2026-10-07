import os
import shutil
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from PIL import Image, ImageEnhance

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.onnx

import torchvision.transforms as transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
import torchvision.models as models
from torchvision.models import ResNet50_Weights

from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
# Daftar kandidat lokasi dataset (urutan prioritas)
CANDIDATES = [
    '/kaggle/input/iqothnccd-lung-cancer-dataset/The IQ-OTHNCCD lung cancer dataset/The IQ-OTHNCCD lung cancer dataset',
    './The IQ-OTHNCCD lung cancer dataset/The IQ-OTHNCCD lung cancer dataset',
    '../input/iqothnccd-lung-cancer-dataset/The IQ-OTHNCCD lung cancer dataset/The IQ-OTHNCCD lung cancer dataset',
]

base_dir = None
for _p in CANDIDATES:
    if os.path.isdir(_p):
        base_dir = _p
        break

if base_dir is None:
    raise FileNotFoundError(
        "Dataset tidak ditemukan! Cek path berikut:\n" + "\n".join(CANDIDATES)
    )

print("Dataset ditemukan di:", base_dir)

CLASS_NAMES = ['Bengin cases', 'Malignant cases', 'Normal cases']

for cls in CLASS_NAMES:
    cls_folder = os.path.join(base_dir, cls)
    if not os.path.isdir(cls_folder):
        raise FileNotFoundError(f"Folder kelas tidak ditemukan: {cls_folder}")
    n = len([f for f in os.listdir(cls_folder) if os.path.isfile(os.path.join(cls_folder, f))])
    print(f"  {cls}: {n} gambar")
assert 'base_dir' in dir() and base_dir is not None, \
    "ERROR: Jalankan Cell 2 (Data Preparation) terlebih dahulu!"

# Tentukan output dir (Kaggle pakai /kaggle/working, selain itu pakai local)
_working = '/kaggle/working' if os.path.isdir('/kaggle/working') else '.'
TRAIN_DIR = os.path.join(_working, 'dataset', 'train')
VAL_DIR   = os.path.join(_working, 'dataset', 'val')

# Reset direktori
for _d in [TRAIN_DIR, VAL_DIR]:
    if os.path.exists(_d):
        shutil.rmtree(_d)
    for cls in CLASS_NAMES:
        os.makedirs(os.path.join(_d, cls), exist_ok=True)

TRAIN_RATIO = 0.8

for cls in CLASS_NAMES:
    src_folder = os.path.join(base_dir, cls)
    files = sorted([f for f in os.listdir(src_folder) if os.path.isfile(os.path.join(src_folder, f))])
    random.shuffle(files)

    split_idx   = int(len(files) * TRAIN_RATIO)
    train_files = files[:split_idx]
    val_files   = files[split_idx:]

    for f in train_files:
        shutil.copy(os.path.join(src_folder, f), os.path.join(TRAIN_DIR, cls, f))
    for f in val_files:
        shutil.copy(os.path.join(src_folder, f), os.path.join(VAL_DIR, cls, f))

    print(f"  {cls}: {len(train_files)} train | {len(val_files)} val")

print(f"\nSplit selesai -> train: {TRAIN_DIR} | val: {VAL_DIR}")
assert 'TRAIN_DIR' in dir(), "ERROR: Jalankan Cell 3 (Data Splitting) terlebih dahulu!"

TARGET_COUNT = 600
IMG_SIZE     = (512, 512)

def get_random_transform():
    transforms_list = [
        lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),
        lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),
        lambda img: img.rotate(random.uniform(-25, 25)),
        lambda img: ImageEnhance.Contrast(img).enhance(random.uniform(1.2, 1.8)),
        lambda img: ImageEnhance.Color(img).enhance(random.uniform(1.2, 2.0)),
        lambda img: ImageEnhance.Sharpness(img).enhance(random.uniform(1.5, 2.5)),
    ]
    return random.choice(transforms_list)

def augment_class(cls, target):
    dst = os.path.join(TRAIN_DIR, cls)
    imgs = [f for f in os.listdir(dst) if os.path.isfile(os.path.join(dst, f))]
    needed = target - len(imgs)
    if needed <= 0:
        print(f"  {cls}: cukup ({len(imgs)} gambar), tidak perlu augmentasi")
        return
    print(f"  {cls}: menghasilkan {needed} gambar tambahan...")
    for i in range(needed):
        src_name = random.choice(imgs)
        try:
            with Image.open(os.path.join(dst, src_name)) as img:
                img = img.convert('RGB').resize(IMG_SIZE)
                aug = get_random_transform()(img)
                aug.save(os.path.join(dst, f"aug_{i:05d}_{src_name}"))
        except Exception as e:
            print(f"    Skipped {src_name}: {e}")

for cls in CLASS_NAMES:
    augment_class(cls, TARGET_COUNT)

print("\nAugmentasi selesai!")
assert 'TRAIN_DIR' in dir(), "ERROR: Jalankan Cell 3 (Data Splitting) terlebih dahulu!"
assert os.path.isdir(TRAIN_DIR), f"Folder train tidak ada: {TRAIN_DIR}"
assert os.path.isdir(VAL_DIR),   f"Folder val tidak ada: {VAL_DIR}"

IMG_SIZE = (512, 512)   # pastikan konsisten dengan augmentasi

data_transforms = transforms.Compose([
    transforms.Resize(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std =[0.229, 0.224, 0.225]),
])

train_dataset = ImageFolder(TRAIN_DIR, transform=data_transforms)
val_dataset   = ImageFolder(VAL_DIR,   transform=data_transforms)

# num_workers=0 aman di Windows; Kaggle/Colab bisa pakai 2
_nw = 0 if os.name == 'nt' else 2

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True,
                          num_workers=_nw, pin_memory=True)
val_loader   = DataLoader(val_dataset,   batch_size=32, shuffle=False,
                          num_workers=_nw, pin_memory=True)

print(f"Train: {len(train_dataset)} gambar | Val: {len(val_dataset)} gambar")
print(f"Class mapping: {train_dataset.class_to_idx}")
resnet50 = models.resnet50(weights=ResNet50_Weights.DEFAULT)

# Freeze semua layer kecuali fc (transfer learning)
for param in resnet50.parameters():
    param.requires_grad = False

# Ganti classifier head
num_ftrs = resnet50.fc.in_features
resnet50.fc = nn.Sequential(
    nn.Dropout(p=0.3),
    nn.Linear(num_ftrs, 3)
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("Using device:", device)
resnet50 = resnet50.to(device)
criterion = nn.CrossEntropyLoss()

# Hanya optimasi parameter fc yang tidak di-freeze
optimizer = optim.Adam(
    filter(lambda p: p.requires_grad, resnet50.parameters()),
    lr=1e-3
)

# ReduceLROnPlateau — turunkan LR jika val_loss tidak membaik
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.1, patience=3
)
EPOCHS   = 15
PATIENCE = 5

best_val_loss    = float('inf')
epochs_no_improve = 0

train_loss_hist, train_acc_hist = [], []
val_loss_hist,   val_acc_hist   = [], []

for epoch in range(EPOCHS):
    # ── Train ────────────────────────────────────────
    resnet50.train()
    run_loss, run_correct, run_total = 0.0, 0, 0

    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = resnet50(inputs)
        loss    = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        run_loss    += loss.item()
        _, preds     = torch.max(outputs, 1)
        run_correct += (preds == labels).sum().item()
        run_total   += labels.size(0)

    ep_loss = run_loss / len(train_loader)
    ep_acc  = run_correct / run_total
    train_loss_hist.append(ep_loss)
    train_acc_hist.append(ep_acc)

    # ── Validate ─────────────────────────────────────
    resnet50.eval()
    v_loss, v_correct, v_total = 0.0, 0, 0

    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = resnet50(inputs)
            loss    = criterion(outputs, labels)
            v_loss += loss.item()
            _, preds  = torch.max(outputs, 1)
            v_correct += (preds == labels).sum().item()
            v_total   += labels.size(0)

    avg_vl  = v_loss / len(val_loader)
    avg_va  = v_correct / v_total
    val_loss_hist.append(avg_vl)
    val_acc_hist.append(avg_va)

    scheduler.step(avg_vl)

    print(f"Epoch {epoch+1:02d}/{EPOCHS} | "
          f"Train Loss: {ep_loss:.4f}  Acc: {ep_acc:.4f} | "
          f"Val Loss: {avg_vl:.4f}  Acc: {avg_va:.4f}")

    # ── Checkpoint & Early Stop ───────────────────────
    if avg_vl < best_val_loss:
        best_val_loss = avg_vl
        epochs_no_improve = 0
        torch.save(resnet50.state_dict(), 'best_resnet50.pth')
        print(f"  >>> checkpoint disimpan (val_loss={best_val_loss:.4f})")
    else:
        epochs_no_improve += 1
        print(f"  --- Tidak ada peningkatan ({epochs_no_improve}/{PATIENCE})")
        if epochs_no_improve >= PATIENCE:
            print(f"\nEarly stopping pada epoch {epoch+1}!")
            break

# Load ulang bobot terbaik
print("\nMemuat ulang bobot terbaik...")
resnet50.load_state_dict(torch.load('best_resnet50.pth', map_location=device))
resnet50.eval()
print("Selesai.")
all_preds, all_labels = [], []
n_correct, n_total    = 0, 0

with torch.no_grad():
    for imgs, lbls in val_loader:
        imgs, lbls = imgs.to(device), lbls.to(device)
        outs = resnet50(imgs)
        _, preds = torch.max(outs, 1)
        n_correct += (preds == lbls).sum().item()
        n_total   += lbls.size(0)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(lbls.cpu().numpy())

y_true = np.array(all_labels)
y_pred = np.array(all_preds)

metrics = {
    'Accuracy' : round(n_correct / n_total, 4),
    'Precision': round(precision_score(y_true, y_pred, average='weighted', zero_division=0), 4),
    'Recall'   : round(recall_score   (y_true, y_pred, average='weighted', zero_division=0), 4),
    'F1 Score' : round(f1_score       (y_true, y_pred, average='weighted', zero_division=0), 4),
}

print("=== Metrik Evaluasi ResNet50 ===")
for k, v in metrics.items():
    print(f"  {k}: {v}")

display(pd.DataFrame([metrics]))

# ── Plot ─────────────────────────────────────────────
n_ep = len(train_acc_hist)
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(range(1, n_ep+1), train_acc_hist, label='Train')
axes[0].plot(range(1, n_ep+1), val_acc_hist,   label='Val')
axes[0].set_title('ResNet50 – Accuracy'); axes[0].set_xlabel('Epoch')
axes[0].legend(); axes[0].grid(True)

axes[1].plot(range(1, n_ep+1), train_loss_hist, label='Train')
axes[1].plot(range(1, n_ep+1), val_loss_hist,   label='Val')
axes[1].set_title('ResNet50 – Loss'); axes[1].set_xlabel('Epoch')
axes[1].legend(); axes[1].grid(True)

plt.tight_layout(); plt.show()
# Classification Report
print("=== Detailed Classification Report ===")
print(classification_report(y_true, y_pred, target_names=CLASS_NAMES, zero_division=0))

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
plt.title('Confusion Matrix')
plt.xlabel('Predicted'); plt.ylabel('True')
plt.tight_layout(); plt.show()

# Confidence distribution
all_conf = []
with torch.no_grad():
    for imgs, _ in val_loader:
        imgs  = imgs.to(device)
        probs = F.softmax(resnet50(imgs), dim=1)
        conf, _ = torch.max(probs, dim=1)
        all_conf.extend(conf.cpu().numpy())

all_conf = np.array(all_conf)
print(f"\nConfidence Statistics:")
print(f"  Rata-rata : {all_conf.mean():.2%}")
print(f"  Max       : {all_conf.max():.2%}")
print(f"  Min       : {all_conf.min():.2%}")

plt.figure(figsize=(8, 4))
plt.hist(all_conf, bins=20, color='steelblue', edgecolor='white')
plt.title('Distribution of Prediction Confidence')
plt.xlabel('Confidence Score'); plt.ylabel('Count')
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout(); plt.show()
# State-dict (bobot terbaik sudah di-load di Cell 8)
shutil.copy('best_resnet50.pth', 'lung-cancer-severity.pth')
print("Disimpan: lung-cancer-severity.pth")

# TorchScript
example = torch.rand(1, 3, 512, 512).to(device)
script  = torch.jit.trace(resnet50, example)
script.save('lung_cancer_model_production.pt')
print("Disimpan: lung_cancer_model_production.pt")

# ONNX
torch.onnx.export(
    resnet50, example, 'lung_cancer_model.onnx',
    export_params=True, opset_version=18,
    do_constant_folding=True,
    input_names=['input'], output_names=['output'],
    dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
)
print("Disimpan: lung_cancer_model.onnx")
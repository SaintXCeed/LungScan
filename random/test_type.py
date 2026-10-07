import os
import shutil
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from PIL import Image, ImageEnhance

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader

import torchvision.transforms as transforms
import torchvision.models as models
from torchvision.datasets import ImageFolder
from torchvision.models import ResNet50_Weights

from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_score, recall_score, f1_score
)
import kagglehub

# Download latest version
path = kagglehub.dataset_download("mohamedhanyyy/chest-ctscan-images")
print("Path to dataset files:", path)

dataset_path = path
data_dir     = Path(dataset_path)

# Dataset sudah memiliki struktur Data/train, Data/valid, Data/test
base_dir   = os.path.join(dataset_path, "Data")
TRAIN_PATH = os.path.join(base_dir, "train")
VAL_PATH   = os.path.join(base_dir, "valid")
TEST_PATH  = os.path.join(base_dir, "test")

BATCH_SIZE = 32
IMG_SIZE   = (460, 460)

print("Train :", TRAIN_PATH)
print("Valid :", VAL_PATH)
print("Test  :", TEST_PATH)

# Verifikasi jumlah gambar per kelas
for label, pth in [("TRAIN", TRAIN_PATH), ("VAL", VAL_PATH), ("TEST", TEST_PATH)]:
    print(f"\n[{label}]")
    for cls in sorted(os.listdir(pth)):
        cls_path = os.path.join(pth, cls)
        if os.path.isdir(cls_path):
            n = len([f for f in os.listdir(cls_path) if os.path.isfile(os.path.join(cls_path, f))])
            print(f"  {cls}: {n} gambar")

# Class names dari folder train (nama folder lengkap)
CLASS_NAMES = sorted([d for d in os.listdir(TRAIN_PATH) if os.path.isdir(os.path.join(TRAIN_PATH, d))])
print("\nKelas (train):", CLASS_NAMES)
resnet_mean = [0.485, 0.456, 0.406]
resnet_std  = [0.229, 0.224, 0.225]

# Train: augmentasi online
train_transforms = transforms.Compose([
    transforms.Resize(IMG_SIZE),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(25),
    transforms.ColorJitter(brightness=0.25, contrast=0.25),
    transforms.ToTensor(),
    transforms.Normalize(mean=resnet_mean, std=resnet_std),
])

# Valid & Test: hanya preprocessing standar
eval_transforms = transforms.Compose([
    transforms.Resize(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=resnet_mean, std=resnet_std),
])
train_dataset = ImageFolder(TRAIN_PATH, transform=train_transforms)
val_dataset   = ImageFolder(VAL_PATH,   transform=eval_transforms)
test_dataset  = ImageFolder(TEST_PATH,  transform=eval_transforms)

_nw = 0 if os.name == 'nt' else 2   # num_workers=0 di Windows, 2 di Kaggle/Colab

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                          num_workers=_nw, pin_memory=True)
val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False,
                          num_workers=_nw, pin_memory=True)
test_loader  = DataLoader(test_dataset,  batch_size=BATCH_SIZE, shuffle=False,
                          num_workers=_nw, pin_memory=True)

print(f"Train : {len(train_dataset)} gambar")
print(f"Val   : {len(val_dataset)} gambar")
print(f"Test  : {len(test_dataset)} gambar")
print(f"Class mapping: {train_dataset.class_to_idx}")
classes_arr = np.array(train_dataset.targets)
class_weights_arr = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(classes_arr),
    y=classes_arr
)
class_weights_dict = dict(enumerate(class_weights_arr))
class_weights_tensor = torch.tensor(class_weights_arr, dtype=torch.float32)

print("Class Weights:", class_weights_dict)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("Using device:", device)

# Load ResNet50 pretrained
resnet50 = models.resnet50(weights=ResNet50_Weights.DEFAULT)

# Ganti classifier head — num_classes diambil dari dataset agar selalu sinkron
num_ftrs    = resnet50.fc.in_features
num_classes = len(train_dataset.classes)
resnet50.fc = nn.Sequential(
    nn.Linear(num_ftrs, 256),
    nn.BatchNorm1d(256),
    nn.ReLU(inplace=True),
    nn.Dropout(p=0.4),
    nn.Linear(256, 128),
    nn.BatchNorm1d(128),
    nn.ReLU(inplace=True),
    nn.Dropout(p=0.3),
    nn.Linear(128, num_classes)
)

# ── FASE 1: Freeze backbone, hanya fc yang dilatih ──────────────────────
for param in resnet50.parameters():
    param.requires_grad = False
for param in resnet50.fc.parameters():
    param.requires_grad = True

resnet50 = resnet50.to(device)

total_params     = sum(p.numel() for p in resnet50.parameters())
trainable_params = sum(p.numel() for p in resnet50.parameters() if p.requires_grad)
print(f"Num classes     : {num_classes}")
print(f"Total params    : {total_params:,}")
print(f"Trainable params (Phase 1): {trainable_params:,}")
# Loss dengan class weights untuk mengatasi imbalance
criterion = nn.CrossEntropyLoss(
    weight=class_weights_tensor.to(device),
    label_smoothing=0.1
)

def run_epoch(loader, training=True):
    if training:
        resnet50.train()
    else:
        resnet50.eval()

    total_loss, correct, total = 0.0, 0, 0
    ctx = torch.enable_grad() if training else torch.no_grad()

    with ctx:
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            if training:
                optimizer.zero_grad()
            outputs = resnet50(inputs)
            loss    = criterion(outputs, labels)
            if training:
                loss.backward()
                optimizer.step()
            total_loss += loss.item()
            _, preds    = torch.max(outputs, 1)
            correct    += (preds == labels).sum().item()
            total      += labels.size(0)

    return total_loss / len(loader), correct / total

def train_phase(phase_name, epochs, lr, patience,
                unfreeze_layers=None, checkpoint_path='best_resnet50_type.pth'):
    global train_loss_hist, train_acc_hist, val_loss_hist, val_acc_hist

    # Unfreeze layer tertentu jika ada
    if unfreeze_layers:
        for name, param in resnet50.named_parameters():
            if any(layer in name for layer in unfreeze_layers):
                param.requires_grad = True
        trainable = sum(p.numel() for p in resnet50.parameters() if p.requires_grad)
        print(f"[{phase_name}] Trainable params: {trainable:,}")

    opt = optim.Adam(
        filter(lambda p: p.requires_grad, resnet50.parameters()),
        lr=lr
    )
    sch = optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode='min', factor=0.2, patience=3, min_lr=1e-7
    )
    global optimizer
    optimizer = opt

    best_loss, no_improve = float('inf'), 0
    print(f"\n{'='*60}")
    print(f"  {phase_name} | lr={lr} | max_epochs={epochs} | patience={patience}")
    print(f"{'='*60}")

    for epoch in range(epochs):
        tr_loss, tr_acc = run_epoch(train_loader, training=True)
        vl_loss, vl_acc = run_epoch(val_loader,   training=False)

        train_loss_hist.append(tr_loss)
        train_acc_hist.append(tr_acc)
        val_loss_hist.append(vl_loss)
        val_acc_hist.append(vl_acc)

        sch.step(vl_loss)
        curr_lr = opt.param_groups[0]['lr']
        print(f"  Epoch {epoch+1:02d}/{epochs} | "
              f"Train Loss: {tr_loss:.4f} Acc: {tr_acc:.4f} | "
              f"Val Loss: {vl_loss:.4f} Acc: {vl_acc:.4f} | LR: {curr_lr:.2e}")

        if vl_loss < best_loss:
            best_loss = vl_loss
            no_improve = 0
            torch.save(resnet50.state_dict(), checkpoint_path)
            print(f"    >>> Checkpoint disimpan (val_loss={best_loss:.4f})")
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"    --- Early stopping pada epoch {epoch+1}")
                break

    # Load bobot terbaik fase ini
    resnet50.load_state_dict(torch.load(checkpoint_path, map_location=device))
    print(f"\n[{phase_name}] Selesai. Best val_loss={best_loss:.4f}")

# ── Inisialisasi history ─────────────────────────────────────────────────
train_loss_hist, train_acc_hist = [], []
val_loss_hist,   val_acc_hist   = [], []
optimizer = None

# ─────────────────────────────────────────────────────────────────────────
# FASE 1: Warmup — hanya head (fc) yang dilatih, lr tinggi
# ─────────────────────────────────────────────────────────────────────────
train_phase(
    phase_name='Phase 1 — Head Warmup',
    epochs=10,
    lr=1e-3,
    patience=5,
)

# ─────────────────────────────────────────────────────────────────────────
# FASE 2: Fine-tuning — unfreeze layer3 + layer4, lr rendah
# ─────────────────────────────────────────────────────────────────────────
train_phase(
    phase_name='Phase 2 — Fine-tuning (layer3 + layer4 + fc)',
    epochs=25,
    lr=3e-5,
    patience=10,
    unfreeze_layers=['layer3', 'layer4'],
)

print("\nTraining selesai! Bobot terbaik sudah dimuat.")
n_ep = len(train_acc_hist)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].plot(range(1, n_ep+1), train_acc_hist, label='Train Accuracy')
axes[0].plot(range(1, n_ep+1), val_acc_hist,   label='Validation Accuracy')
axes[0].set_title('Model Accuracy During Training')
axes[0].set_xlabel('Epochs'); axes[0].set_ylabel('Accuracy')
axes[0].legend(); axes[0].grid(True)

axes[1].plot(range(1, n_ep+1), train_loss_hist, label='Train Loss')
axes[1].plot(range(1, n_ep+1), val_loss_hist,   label='Validation Loss')
axes[1].set_title('Model Loss During Training')
axes[1].set_xlabel('Epochs'); axes[1].set_ylabel('Loss')
axes[1].legend(); axes[1].grid(True)

plt.tight_layout()
plt.show()
resnet50.eval()
all_preds, all_labels = [], []
n_correct, n_total    = 0, 0

with torch.no_grad():
    for imgs, lbls in test_loader:
        imgs, lbls = imgs.to(device), lbls.to(device)
        outs  = resnet50(imgs)
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

print("=== Metrik Evaluasi ResNet50 (Test Set) ===")
for k, v in metrics.items():
    print(f"  {k}: {v}")

display(pd.DataFrame([metrics]))
print("Classification Report:\n")
print(classification_report(y_true, y_pred, target_names=CLASS_NAMES, zero_division=0))

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(7, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
plt.title('Confusion Matrix')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.tight_layout()
plt.show()
from torchvision.transforms.functional import to_pil_image

# ── Hook untuk Grad-CAM ──────────────────────────────────────────────────
_gradients  = {}
_activations = {}

def save_gradient(name):
    def hook(module, grad_in, grad_out):
        _gradients[name] = grad_out[0]
    return hook

def save_activation(name):
    def hook(module, input, output):
        _activations[name] = output
    return hook

# Pasang hook pada layer terakhir (layer4[-1])
target_layer = resnet50.layer4[-1]
target_layer.register_forward_hook(save_activation('layer4'))
target_layer.register_backward_hook(save_gradient('layer4'))

def generate_gradcam(img_tensor, class_idx=None):
    resnet50.eval()
    img_tensor = img_tensor.unsqueeze(0).to(device)
    img_tensor.requires_grad_(True)

    output = resnet50(img_tensor)
    if class_idx is None:
        class_idx = output.argmax(dim=1).item()

    resnet50.zero_grad()
    output[0, class_idx].backward()

    grads  = _gradients['layer4']
    acts   = _activations['layer4']

    weights = grads.mean(dim=(2, 3), keepdim=True)
    cam = (weights * acts).sum(dim=1, keepdim=True)
    cam = F.relu(cam)
    cam = cam.squeeze().detach().cpu().numpy()

    # Normalize
    cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    return cam, class_idx

# ── Visualisasi 6 gambar ─────────────────────────────────────────────────
sample_imgs, sample_lbls = next(iter(test_loader))
n_show = min(6, len(sample_imgs))

fig, axes = plt.subplots(n_show, 2, figsize=(10, n_show * 3))

for i in range(n_show):
    img_tensor = sample_imgs[i]
    true_cls   = sample_lbls[i].item()

    cam, pred_cls = generate_gradcam(img_tensor)

    # Denormalize image untuk visualisasi
    mean = torch.tensor(resnet_mean).view(3,1,1)
    std  = torch.tensor(resnet_std).view(3,1,1)
    img_vis = (img_tensor * std + mean).clamp(0, 1).permute(1, 2, 0).numpy()

    # Resize cam ke ukuran gambar
    import cv2
    cam_resized = cv2.resize(cam, (img_vis.shape[1], img_vis.shape[0]))
    heatmap     = plt.cm.jet(cam_resized)[:, :, :3]
    overlay     = 0.5 * img_vis + 0.5 * heatmap

    axes[i, 0].imshow(img_vis)
    axes[i, 0].set_title(f"Original | True: {CLASS_NAMES[true_cls]}")
    axes[i, 0].axis('off')

    axes[i, 1].imshow(overlay)
    axes[i, 1].set_title(f"Grad-CAM | Pred: {CLASS_NAMES[pred_cls]}")
    axes[i, 1].axis('off')

plt.tight_layout()
plt.show()
import shutil
# State-dict (bobot terbaik sudah di-load)
shutil.copy('best_resnet50_type.pth', 'final_lung_cancer_type_model.pth')
print("Saved: final_lung_cancer_type_model.pth")

# TorchScript
example = torch.rand(1, 3, 460, 460).to(device)
resnet50.eval()
script  = torch.jit.trace(resnet50, example)
script.save('lung_cancer_type_production.pt')
print("Saved: lung_cancer_type_production.pt")

# ONNX
torch.onnx.export(
    resnet50, example, 'lung_cancer_type_model.onnx',
    export_params=True, opset_version=18,
    do_constant_folding=True,
    input_names=['input'], output_names=['output'],
    dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
)
print("Saved: lung_cancer_type_model.onnx")

print("\nSemua model berhasil disimpan!")
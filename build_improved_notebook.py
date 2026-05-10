"""
Script untuk membuat LungScan_AI_Improved_Model_Notebook.ipynb
Jalankan: python build_improved_notebook.py
"""
import json

cells = []

# ─── CELL 0: Markdown Title ───────────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# LungScan AI — Improved Model Notebook\n",
        "\n",
        "Perbaikan dari baseline model:\n",
        "- **Augmentasi lebih kuat** (rotation ±25°, brightness, shear, shift)\n",
        "- **ImageDataGenerator** langsung dari folder lokal (tidak perlu download Kaggle)\n",
        "- **Full fine-tuning** — semua layer dibuka di tahap 2 (bukan hanya 30 terakhir)\n",
        "- **Learning rate scheduling** lebih agresif\n",
        "- **Class weights** dihitung otomatis dari distribusi dataset\n",
        "- **Lebih banyak epoch** — 15 (head) + 20 (fine-tune)\n",
        "\n",
        "Dataset: `chest-ctscan-images/` (lokal)\n",
        "Kelas: adenocarcinoma, large_cell_carcinoma, squamous_cell_carcinoma, normal"
    ]
})

# ─── CELL 1: Setup ────────────────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import os\n",
        "import json\n",
        "import numpy as np\n",
        "import matplotlib.pyplot as plt\n",
        "import tensorflow as tf\n",
        "from tensorflow import keras\n",
        "from tensorflow.keras import layers\n",
        "from tensorflow.keras.applications.efficientnet import preprocess_input\n",
        "from sklearn.utils.class_weight import compute_class_weight\n",
        "from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay\n",
        "\n",
        "print('TensorFlow:', tf.__version__)\n",
        "print('GPU:', tf.config.list_physical_devices('GPU'))\n",
        "\n",
        "# ── Paths ──────────────────────────────────────────────────────────────────\n",
        "# Ubah DATA_DIR ke path dataset Anda\n",
        "DATA_DIR   = r'C:\\Users\\trija\\Documents\\LungDetection\\chest-ctscan-images'\n",
        "EXPORT_DIR = r'C:\\Users\\trija\\Documents\\LungDetection'\n",
        "\n",
        "# ── Hyperparameters ────────────────────────────────────────────────────────\n",
        "IMG_SIZE    = (224, 224)\n",
        "BATCH_SIZE  = 16\n",
        "NUM_CLASSES = 4\n",
        "SEED        = 42\n",
        "\n",
        "CLASSES = ['adenocarcinoma', 'large_cell_carcinoma', 'normal', 'squamous_cell_carcinoma']\n",
        "# Catatan: ImageDataGenerator menggunakan urutan alfabetis folder\n",
        "# Kita akan override class_indices setelah fit\n",
        "\n",
        "tf.random.set_seed(SEED)\n",
        "np.random.seed(SEED)\n",
        "print('Setup selesai.')"
    ]
})

# ─── CELL 2: Markdown — Data ──────────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## 1. Data Generators dengan Augmentasi Kuat"]
})

# ─── CELL 3: Data Generators ──────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "from tensorflow.keras.preprocessing.image import ImageDataGenerator\n",
        "\n",
        "# ── Training generator: augmentasi kuat ────────────────────────────────────\n",
        "train_datagen = ImageDataGenerator(\n",
        "    preprocessing_function=preprocess_input,\n",
        "    rotation_range=25,          # putar ±25 derajat\n",
        "    width_shift_range=0.15,     # geser horizontal ±15%\n",
        "    height_shift_range=0.15,    # geser vertikal ±15%\n",
        "    horizontal_flip=True,\n",
        "    vertical_flip=True,         # CT scan valid diflip vertikal\n",
        "    zoom_range=0.20,            # zoom in/out ±20%\n",
        "    shear_range=0.10,           # geser sudut ±10%\n",
        "    brightness_range=[0.70, 1.30],  # kecerahan ±30%\n",
        "    fill_mode='nearest'\n",
        ")\n",
        "\n",
        "# ── Validation & Test generator: hanya preprocessing ───────────────────────\n",
        "eval_datagen = ImageDataGenerator(\n",
        "    preprocessing_function=preprocess_input\n",
        ")\n",
        "\n",
        "# ── Flow dari folder ───────────────────────────────────────────────────────\n",
        "train_gen = train_datagen.flow_from_directory(\n",
        "    os.path.join(DATA_DIR, 'train'),\n",
        "    target_size=IMG_SIZE,\n",
        "    batch_size=BATCH_SIZE,\n",
        "    class_mode='sparse',\n",
        "    seed=SEED,\n",
        "    shuffle=True\n",
        ")\n",
        "\n",
        "valid_gen = eval_datagen.flow_from_directory(\n",
        "    os.path.join(DATA_DIR, 'valid'),\n",
        "    target_size=IMG_SIZE,\n",
        "    batch_size=BATCH_SIZE,\n",
        "    class_mode='sparse',\n",
        "    shuffle=False\n",
        ")\n",
        "\n",
        "test_gen = eval_datagen.flow_from_directory(\n",
        "    os.path.join(DATA_DIR, 'test'),\n",
        "    target_size=IMG_SIZE,\n",
        "    batch_size=BATCH_SIZE,\n",
        "    class_mode='sparse',\n",
        "    shuffle=False\n",
        ")\n",
        "\n",
        "print('Train class indices:', train_gen.class_indices)\n",
        "print('Valid class indices:', valid_gen.class_indices)\n",
        "print('Test  class indices:', test_gen.class_indices)\n",
        "print(f'Train: {train_gen.n} | Valid: {valid_gen.n} | Test: {test_gen.n}')"
    ]
})

# ─── CELL 4: Markdown — Class Weights ─────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## 2. Class Weights (counter imbalance)"]
})

# ─── CELL 5: Class Weights ────────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Hitung class weights dari distribusi training\n",
        "y_train = train_gen.classes\n",
        "class_weights_arr = compute_class_weight(\n",
        "    class_weight='balanced',\n",
        "    classes=np.unique(y_train),\n",
        "    y=y_train\n",
        ")\n",
        "class_weight = {int(c): float(w) for c, w in enumerate(class_weights_arr)}\n",
        "print('Class weights:', class_weight)\n",
        "\n",
        "# Tampilkan distribusi kelas\n",
        "idx_to_label = {v: k for k, v in train_gen.class_indices.items()}\n",
        "unique, counts = np.unique(y_train, return_counts=True)\n",
        "for cls_idx, cnt in zip(unique, counts):\n",
        "    print(f'  [{cls_idx}] {idx_to_label[cls_idx]}: {cnt} gambar (weight={class_weight[cls_idx]:.3f})')"
    ]
})

# ─── CELL 6: Markdown — Model ─────────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 3. Arsitektur Model — EfficientNetB0\n",
        "\n",
        "Perbaikan dari baseline:\n",
        "- `GlobalAveragePooling2D` → `Dense(256, relu)` → `BatchNormalization` → `Dropout(0.4)` → output\n",
        "- Head lebih dalam untuk feature extraction yang lebih baik"
    ]
})

# ─── CELL 7: Build Model ──────────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "def build_model(num_classes=4, img_size=(224, 224), trainable_base=False):\n",
        "    base = keras.applications.EfficientNetB0(\n",
        "        include_top=False,\n",
        "        weights='imagenet',\n",
        "        input_shape=img_size + (3,)\n",
        "    )\n",
        "    base.trainable = trainable_base\n",
        "\n",
        "    inputs  = keras.Input(shape=img_size + (3,), name='ct_image')\n",
        "    x       = base(inputs, training=False)\n",
        "    x       = layers.GlobalAveragePooling2D(name='gap')(x)\n",
        "    x       = layers.Dense(256, activation='relu', name='fc1')(x)\n",
        "    x       = layers.BatchNormalization(name='bn1')(x)\n",
        "    x       = layers.Dropout(0.4, name='dropout')(x)\n",
        "    outputs = layers.Dense(num_classes, activation='softmax', name='class_probability')(x)\n",
        "\n",
        "    return keras.Model(inputs, outputs, name='lungscan_improved')\n",
        "\n",
        "model = build_model(trainable_base=False)\n",
        "model.summary()"
    ]
})

# ─── CELL 8: Markdown — Stage 1 ───────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 4. Training Tahap 1 — Head Only (base frozen)\n",
        "\n",
        "Latih hanya head baru selama 15 epoch, LR=1e-3"
    ]
})

# ─── CELL 9: Stage 1 Training ─────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "model.compile(\n",
        "    optimizer=keras.optimizers.Adam(1e-3),\n",
        "    loss='sparse_categorical_crossentropy',\n",
        "    metrics=['accuracy']\n",
        ")\n",
        "\n",
        "callbacks_stage1 = [\n",
        "    keras.callbacks.ModelCheckpoint(\n",
        "        'best_improved_lungscan.keras',\n",
        "        monitor='val_accuracy', save_best_only=True, mode='max', verbose=1\n",
        "    ),\n",
        "    keras.callbacks.EarlyStopping(\n",
        "        monitor='val_loss', patience=6, restore_best_weights=True, verbose=1\n",
        "    ),\n",
        "    keras.callbacks.ReduceLROnPlateau(\n",
        "        monitor='val_loss', factor=0.3, patience=3, min_lr=1e-7, verbose=1\n",
        "    ),\n",
        "]\n",
        "\n",
        "history_head = model.fit(\n",
        "    train_gen,\n",
        "    validation_data=valid_gen,\n",
        "    epochs=15,\n",
        "    class_weight=class_weight,\n",
        "    callbacks=callbacks_stage1\n",
        ")\n",
        "\n",
        "print('Stage 1 selesai.')"
    ]
})

# ─── CELL 10: Markdown — Stage 2 ──────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 5. Training Tahap 2 — Full Fine-Tuning\n",
        "\n",
        "Buka SEMUA layer EfficientNetB0 (berbeda dari baseline yang hanya buka 30 layer terakhir).\n",
        "LR sangat kecil (1e-5) untuk menghindari catastrophic forgetting."
    ]
})

# ─── CELL 11: Stage 2 Training ────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Buka SEMUA layer untuk fine-tuning\n",
        "for layer in model.layers:\n",
        "    layer.trainable = True\n",
        "\n",
        "# Kompilasi ulang dengan LR sangat kecil\n",
        "model.compile(\n",
        "    optimizer=keras.optimizers.Adam(1e-5),\n",
        "    loss='sparse_categorical_crossentropy',\n",
        "    metrics=['accuracy']\n",
        ")\n",
        "\n",
        "callbacks_stage2 = [\n",
        "    keras.callbacks.ModelCheckpoint(\n",
        "        'best_improved_lungscan.keras',\n",
        "        monitor='val_accuracy', save_best_only=True, mode='max', verbose=1\n",
        "    ),\n",
        "    keras.callbacks.EarlyStopping(\n",
        "        monitor='val_loss', patience=8, restore_best_weights=True, verbose=1\n",
        "    ),\n",
        "    keras.callbacks.ReduceLROnPlateau(\n",
        "        monitor='val_loss', factor=0.3, patience=3, min_lr=1e-8, verbose=1\n",
        "    ),\n",
        "]\n",
        "\n",
        "history_fine = model.fit(\n",
        "    train_gen,\n",
        "    validation_data=valid_gen,\n",
        "    epochs=20,\n",
        "    class_weight=class_weight,\n",
        "    callbacks=callbacks_stage2\n",
        ")\n",
        "\n",
        "print('Stage 2 selesai.')"
    ]
})

# ─── CELL 12: Markdown — Plot ─────────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## 6. Plot Training History"]
})

# ─── CELL 13: Plot ────────────────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "def plot_history(histories, labels=None):\n",
        "    acc, val_acc, loss, val_loss = [], [], [], []\n",
        "    for h in histories:\n",
        "        acc     += h.history.get('accuracy', [])\n",
        "        val_acc += h.history.get('val_accuracy', [])\n",
        "        loss    += h.history.get('loss', [])\n",
        "        val_loss+= h.history.get('val_loss', [])\n",
        "    epochs = range(1, len(acc)+1)\n",
        "\n",
        "    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))\n",
        "    ax1.plot(epochs, acc, label='Train Accuracy')\n",
        "    ax1.plot(epochs, val_acc, label='Valid Accuracy')\n",
        "    ax1.set_title('Accuracy'); ax1.set_xlabel('Epoch'); ax1.legend(); ax1.grid(True, alpha=0.3)\n",
        "\n",
        "    ax2.plot(epochs, loss, label='Train Loss')\n",
        "    ax2.plot(epochs, val_loss, label='Valid Loss')\n",
        "    ax2.set_title('Loss'); ax2.set_xlabel('Epoch'); ax2.legend(); ax2.grid(True, alpha=0.3)\n",
        "\n",
        "    plt.tight_layout()\n",
        "    plt.show()\n",
        "\n",
        "plot_history([history_head, history_fine])"
    ]
})

# ─── CELL 14: Markdown — Evaluation ──────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## 7. Evaluasi Test Set"]
})

# ─── CELL 15: Evaluation ──────────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Load model terbaik\n",
        "best_model = keras.models.load_model('best_improved_lungscan.keras')\n",
        "\n",
        "# Evaluasi pada test set\n",
        "test_loss, test_acc = best_model.evaluate(test_gen, verbose=1)\n",
        "print(f'Test Accuracy: {test_acc*100:.2f}%')\n",
        "print(f'Test Loss:     {test_loss:.4f}')\n",
        "\n",
        "# Prediksi untuk laporan per kelas\n",
        "test_gen.reset()\n",
        "y_true = test_gen.classes\n",
        "y_pred = np.argmax(best_model.predict(test_gen, verbose=1), axis=1)\n",
        "\n",
        "# Label names sesuai class_indices test generator\n",
        "label_names = [k for k, v in sorted(test_gen.class_indices.items(), key=lambda x: x[1])]\n",
        "print('\\nClassification Report:')\n",
        "print(classification_report(y_true, y_pred, target_names=label_names, digits=4))\n",
        "\n",
        "# Confusion matrix\n",
        "cm = confusion_matrix(y_true, y_pred)\n",
        "fig, ax = plt.subplots(figsize=(8, 7))\n",
        "ConfusionMatrixDisplay(cm, display_labels=label_names).plot(ax=ax, xticks_rotation=45, values_format='d')\n",
        "plt.title('Confusion Matrix — Test Set')\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
})

# ─── CELL 16: Markdown — Save ─────────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## 8. Simpan Model & Label Mapping"]
})

# ─── CELL 17: Save ────────────────────────────────────────────────────────────
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import shutil\n",
        "\n",
        "# Simpan model ke folder LungDetection\n",
        "model_path  = os.path.join(EXPORT_DIR, 'lungscan_ai_improved.keras')\n",
        "weights_path= os.path.join(EXPORT_DIR, 'lungscan_ai_improved.weights.h5')\n",
        "\n",
        "best_model.save(model_path)\n",
        "best_model.save_weights(weights_path)\n",
        "\n",
        "# Simpan label mapping\n",
        "label_map = {\n",
        "    'label_to_idx': train_gen.class_indices,\n",
        "    'idx_to_label': {str(v): k for k, v in train_gen.class_indices.items()},\n",
        "    'img_size': list(IMG_SIZE),\n",
        "    'model_name': 'lungscan_ai_effnetb0_improved',\n",
        "    'test_accuracy': round(float(test_acc * 100), 2)\n",
        "}\n",
        "with open(os.path.join(EXPORT_DIR, 'label_mapping_improved.json'), 'w') as f:\n",
        "    json.dump(label_map, f, indent=2)\n",
        "\n",
        "print('Model disimpan ke:', model_path)\n",
        "print('Weights disimpan ke:', weights_path)\n",
        "print('Label mapping:', label_map)"
    ]
})

# ─── CELL 18: Markdown — Notes ────────────────────────────────────────────────
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 9. Langkah Selanjutnya\n",
        "\n",
        "Setelah training selesai:\n",
        "1. Cek confusion matrix — apakah semua kelas sudah seimbang?\n",
        "2. Jika `large_cell_carcinoma` masih rendah → pertimbangkan data augmentation lebih agresif atau cari data tambahan\n",
        "3. Jika hasil memuaskan → integrasikan `lungscan_ai_improved.keras` ke backend FastAPI\n",
        "4. Update `model_accuracy` di backend response dengan nilai test accuracy yang nyata\n",
        "5. **Disclaimer medis wajib** — model ini untuk screening awal, bukan diagnosis klinis definitif"
    ]
})

# ─── Build notebook JSON ──────────────────────────────────────────────────────
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.x"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 5
}

output_path = r'C:\Users\trija\Documents\LungDetection\LungScan_AI_Improved_Model_Notebook.ipynb'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print('Notebook berhasil dibuat:', output_path)
print('Total cells:', len(cells))

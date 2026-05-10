import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.efficientnet import preprocess_input
from PIL import Image

ROOT = r'C:\Users\trija\Documents\LungDetection'
WEIGHTS_PATH = os.path.join(ROOT, 'lungscan_ai_baseline.weights.h5')
DATA_PATH = os.path.join(ROOT, 'chest-ctscan-images')
IMG_SIZE = (224, 224)
NUM_CLASSES = 4
IDX_TO_LABEL = {
    0: 'adenocarcinoma',
    1: 'large_cell_carcinoma',
    2: 'squamous_cell_carcinoma',
    3: 'normal'
}

# Rebuild architecture (same as training notebook)
from tensorflow.keras import layers

base_model = keras.applications.EfficientNetB0(
    include_top=False, weights=None, input_shape=IMG_SIZE + (3,)
)
base_model.trainable = True

augmentation = keras.Sequential([
    layers.RandomFlip('horizontal'),
    layers.RandomRotation(0.04),
    layers.RandomZoom(0.08),
    layers.RandomContrast(0.10),
], name='augmentation')

inputs = keras.Input(shape=IMG_SIZE + (3,), name='ct_image')
x = augmentation(inputs)
x = keras.applications.efficientnet.preprocess_input(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D(name='global_average_pooling')(x)
x = layers.Dropout(0.35, name='dropout')(x)
outputs = layers.Dense(NUM_CLASSES, activation='softmax', name='class_probability')(x)
model = keras.Model(inputs, outputs, name='lungscan_ai_effnetb0_baseline')
model.load_weights(WEIGHTS_PATH)
print('Model loaded OK')

FOLDER_LABEL_MAP = {
    'adenocarcinoma': 0,
    'adenocarcinoma_left.lower.lobe_T2_N0_M0_Ib': 0,
    'large.cell.carcinoma': 1,
    'large.cell.carcinoma_left.hilum_T2_N2_M0_IIIa': 1,
    'normal': 3,
    'squamous.cell.carcinoma': 2,
    'squamous.cell.carcinoma_left.hilum_T1_N2_M0_IIIa': 2,
}

def evaluate_split(split_name):
    split_path = os.path.join(DATA_PATH, split_name)
    correct, total = 0, 0
    per_class = {i: {'correct': 0, 'total': 0} for i in range(NUM_CLASSES)}

    for folder in os.listdir(split_path):
        folder_path = os.path.join(split_path, folder)
        if not os.path.isdir(folder_path):
            continue
        label_idx = FOLDER_LABEL_MAP.get(folder)
        if label_idx is None:
            print('  SKIP unknown folder: ' + folder)
            continue

        for fname in os.listdir(folder_path):
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                continue
            try:
                img = Image.open(os.path.join(folder_path, fname)).convert('RGB')
                img = img.resize(IMG_SIZE, Image.LANCZOS)
                arr = np.expand_dims(np.array(img, dtype=np.float32), 0)
                probs = model.predict(arr, verbose=0)[0]
                pred = int(np.argmax(probs))
                total += 1
                per_class[label_idx]['total'] += 1
                if pred == label_idx:
                    correct += 1
                    per_class[label_idx]['correct'] += 1
            except Exception as e:
                pass

    acc = correct / total * 100 if total > 0 else 0
    print('\n=== ' + split_name.upper() + ' SET ===')
    print('Overall Accuracy: ' + str(round(acc, 2)) + '% (' + str(correct) + '/' + str(total) + ')')
    for idx in range(NUM_CLASSES):
        data = per_class[idx]
        cls_acc = data['correct'] / data['total'] * 100 if data['total'] > 0 else 0
        print('  ' + IDX_TO_LABEL[idx] + ': ' + str(round(cls_acc, 1)) + '% (' + str(data['correct']) + '/' + str(data['total']) + ')')
    return acc

evaluate_split('test')
evaluate_split('valid')

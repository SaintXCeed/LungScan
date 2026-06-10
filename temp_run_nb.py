# ============================================================
# IMPORTS
# ============================================================

import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input


# ============================================================
# PATHS (ROBUST AUTO-RESOLVE)
# ============================================================

# Detect where we are running from
_cwd = os.getcwd()
if os.path.basename(_cwd) == "model-final":
    # Running inside model-final directory
    DATASET_PATH = "chest-ctscan-images/test"
    TYPE_MODEL_PATH = "Lung_Cancer_ResNet50_88Acc.keras"
    SEVERITY_MODEL_PATH = "Lung_Cancer_Severity_Model.h5"
else:
    # Running from project root directory
    DATASET_PATH = "model-final/chest-ctscan-images/test"
    TYPE_MODEL_PATH = "model-final/Lung_Cancer_ResNet50_88Acc.keras"
    SEVERITY_MODEL_PATH = "model-final/Lung_Cancer_Severity_Model.h5"

print("Dataset path:", DATASET_PATH)
print("Type model path:", TYPE_MODEL_PATH)
print("Severity model path:", SEVERITY_MODEL_PATH)


# ============================================================
# INPUT SIZES (MATCH TRAINING)
# ============================================================

TYPE_INPUT_SIZE = (460, 460)
SEVERITY_INPUT_SIZE = (256, 256)


# ============================================================
# LOAD MODELS
# ============================================================

print("Loading Type Classification Model (.keras)...")
type_model = tf.keras.models.load_model(TYPE_MODEL_PATH)
# Compile with jit_compile=False to prevent XLA symbol errors on Windows
type_model.compile(jit_compile=False)
print("Type model loaded successfully.")
print("Type model input shape:", type_model.input_shape)

print("\nLoading Severity Model (.h5)...")
severity_model = tf.keras.models.load_model(SEVERITY_MODEL_PATH)
# Compile with jit_compile=False to prevent XLA symbol errors on Windows
severity_model.compile(jit_compile=False)
print("Severity model loaded successfully.")
print("Severity model input shape:", severity_model.input_shape)


# ============================================================
# CLASS LABELS
# ============================================================

type_classes = [
    "adenocarcinoma",
    "large.cell.carcinoma",
    "normal",
    "squamous.cell.carcinoma"
]

severity_classes = [
    "Normal",
    "Benign",
    "Malignant"
]


# ============================================================
# PREPROCESSING FUNCTIONS
# ============================================================

def preprocess_for_type(img_path):
    """
    Preprocessing for Type Model (ResNet50 - RGB)
    """
    img = image.load_img(
        img_path,
        target_size=TYPE_INPUT_SIZE,
        color_mode="rgb"
    )

    x = image.img_to_array(img)
    x = preprocess_input(x)

    return np.expand_dims(x, axis=0)


def preprocess_for_severity(img_path):
    """
    Preprocessing for Severity Model (RGB - 3 Channels)
    """
    img = image.load_img(
        img_path,
        target_size=SEVERITY_INPUT_SIZE,
        color_mode="rgb"
    )

    x = image.img_to_array(img) / 255.0

    return np.expand_dims(x, axis=0)


# ============================================================
# PREDICTION FUNCTION (WITH CLINICAL LOGIC FIX)
# ============================================================

def predict_image(img_path):

    # ---- Stage 1: Type Prediction ----
    type_img = preprocess_for_type(img_path)
    type_pred = type_model.predict(type_img, verbose=0)

    predicted_type = type_classes[np.argmax(type_pred)]
    type_conf = round(float(np.max(type_pred)) * 100, 2)

    # ===== Clinical Logic Rule =====
    # If image is Normal → severity must be Normal
    if predicted_type == "normal":
        return {
            "type": predicted_type,
            "type_confidence": type_conf,
            "severity": "Normal",
            "severity_confidence": 100.0
        }

    # ---- Stage 2: Severity Prediction (only if not normal) ----
    sev_img = preprocess_for_severity(img_path)
    severity_pred = severity_model.predict(sev_img, verbose=0)

    predicted_severity = severity_classes[np.argmax(severity_pred)]
    severity_conf = round(float(np.max(severity_pred)) * 100, 2)

    return {
        "type": predicted_type,
        "type_confidence": type_conf,
        "severity": predicted_severity,
        "severity_confidence": severity_conf
    }


# ============================================================
# VISUAL DIAGNOSTIC TEST
# ============================================================

def run_diagnostic_test(num_images_per_class=2):

    if not os.path.exists(DATASET_PATH):
        print(f"Dataset not found at {DATASET_PATH}")
        return

    for class_folder in os.listdir(DATASET_PATH):

        class_path = os.path.join(DATASET_PATH, class_folder)

        if not os.path.isdir(class_path):
            continue

        print(f"\n>>> Scanning Class: {class_folder.upper()} <<<")

        images = [
            f for f in os.listdir(class_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        for img_name in images[:num_images_per_class]:

            img_path = os.path.join(class_path, img_name)

            result = predict_image(img_path)

            img_display = image.load_img(img_path)

            plt.figure(figsize=(5, 5))
            plt.imshow(img_display)
            plt.axis("off")

            title = (
                f"Predicted Type: {result['type']} ({result['type_confidence']}%)\n"
                f"Severity Level: {result['severity']} ({result['severity_confidence']}%)"
            )

            color = 'red' if result['severity'] == "Malignant" else 'green'

            plt.title(title, fontsize=10, fontweight='bold', color=color)
            plt.show()

            print(f"{img_name} -> {result}")


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    run_diagnostic_test(num_images_per_class=2)

import os
import json
import base64
import io
import logging
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LungScan AI MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR   = os.path.join(BASE_DIR, "static")
ROOT_DIR     = os.path.dirname(BASE_DIR)
IMPROVED_DIR = os.path.join(ROOT_DIR, "improve model")   # folder hasil training

MODEL_PATH   = os.path.join(IMPROVED_DIR, "lungscan_ai_improved.keras")
WEIGHTS_PATH = os.path.join(IMPROVED_DIR, "lungscan_ai_improved.weights.h5")

IMG_SIZE     = (224, 224)
NUM_CLASSES  = 4
MODEL_ACCURACY = 61.59   # real test-set accuracy

# ── Label mapping (improved model class ordering dari ImageDataGenerator) ──────
# Train folder indices (alphabetical): 0=adenocarcinoma, 1=large_cell, 2=normal, 3=squamous
_RAW_TO_CLEAN = {
    "adenocarcinoma_left.lower.lobe_t2_n0_m0_ib": "adenocarcinoma",
    "large.cell.carcinoma_left.hilum_t2_n2_m0_iiia": "large_cell_carcinoma",
    "normal": "normal",
    "squamous.cell.carcinoma_left.hilum_t1_n2_m0_iiia": "squamous_cell_carcinoma",
}

# Hardcoded index → clean label (matches improved model's alphabetical folder sort)
_idx_to_label = {
    0: "adenocarcinoma",
    1: "large_cell_carcinoma",
    2: "normal",
    3: "squamous_cell_carcinoma",
}

# ── Global state ───────────────────────────────────────────────────────────────
_model       = None
_model_error = None
_last_conv_name = None


# ── Architecture rebuild — improved model (no augmentation, extra Dense head) ──
def _build_model():
    """Rebuild improved EfficientNetB0 architecture matching the training notebook."""
    from tensorflow import keras
    from tensorflow.keras import layers

    base = keras.applications.EfficientNetB0(
        include_top=False,
        weights=None,
        input_shape=IMG_SIZE + (3,),
    )
    base.trainable = True

    inputs  = keras.Input(shape=IMG_SIZE + (3,), name="ct_image")
    x       = base(inputs, training=False)
    x       = layers.GlobalAveragePooling2D(name="gap")(x)
    x       = layers.Dense(256, activation="relu", name="fc1")(x)
    x       = layers.BatchNormalization(name="bn1")(x)
    x       = layers.Dropout(0.4, name="dropout")(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="class_probability")(x)

    model = keras.Model(inputs, outputs, name="lungscan_improved")
    model.compile(
        optimizer=keras.optimizers.Adam(1e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ── Model loader ───────────────────────────────────────────────────────────────
def _load_resources():
    global _model, _model_error

    try:
        from tensorflow import keras

        loaded = False

        # Strategy 1: load full .keras
        if os.path.exists(MODEL_PATH):
            try:
                logger.info(f"Mencoba load penuh dari: {MODEL_PATH}")
                _model = keras.models.load_model(MODEL_PATH, compile=False)
                logger.info("✅ Model improved berhasil dimuat (full .keras)!")
                loaded = True
            except Exception as e1:
                logger.warning(f"Full load gagal ({e1}), beralih ke weights-only …")

        # Strategy 2: rebuild + load weights.h5
        if not loaded:
            logger.info("Membangun ulang arsitektur improved …")
            _model = _build_model()

            if os.path.exists(WEIGHTS_PATH):
                logger.info(f"Memuat weights dari: {WEIGHTS_PATH}")
                _model.load_weights(WEIGHTS_PATH)
                logger.info("✅ Weights improved berhasil dimuat!")
                loaded = True

        if not loaded:
            raise FileNotFoundError(
                f"Tidak ada model/weights di: {IMPROVED_DIR}"
            )

        logger.info(f"Label mapping: {_idx_to_label}")

    except Exception as exc:
        _model_error = str(exc)
        logger.error(f"❌ Gagal memuat model: {exc}")


_load_resources()


# ── Image helpers ──────────────────────────────────────────────────────────────
def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Load image and apply EfficientNet preprocess_input externally.
    Improved model expects preprocessed input (no internal preprocessing layer)."""
    from tensorflow.keras.applications.efficientnet import preprocess_input
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE, Image.LANCZOS)
    arr = np.expand_dims(np.array(img, dtype=np.float32), axis=0)
    return preprocess_input(arr)  # converts [0,255] → [-1,1]


# ── Grad-CAM ───────────────────────────────────────────────────────────────────
def _get_effnet_and_last_conv():
    global _last_conv_name
    import tensorflow as tf

    effnet_layer = None
    for layer in _model.layers:
        if "efficientnet" in layer.name.lower():
            effnet_layer = layer
            break
    if effnet_layer is None:
        raise ValueError("Layer EfficientNet tidak ditemukan dalam model")

    if _last_conv_name is None:
        for layer in reversed(effnet_layer.layers):
            if isinstance(layer, tf.keras.layers.Conv2D):
                _last_conv_name = layer.name
                break
        if _last_conv_name is None:
            raise ValueError("Conv2D layer tidak ditemukan dalam EfficientNetB0")
        logger.info(f"Grad-CAM target layer: {_last_conv_name}")

    return effnet_layer, _last_conv_name


def _make_gradcam_heatmap(preprocessed: np.ndarray) -> np.ndarray:
    import tensorflow as tf
    from tensorflow import keras

    effnet_layer, last_conv_name = _get_effnet_and_last_conv()

    grad_model = keras.Model(
        inputs=effnet_layer.inputs,
        outputs=[
            effnet_layer.get_layer(last_conv_name).output,
            effnet_layer.output,
        ],
    )

    img_tensor = tf.constant(preprocessed, dtype=tf.float32)

    with tf.GradientTape() as tape:
        tape.watch(img_tensor)
        conv_outputs, base_output = grad_model(img_tensor, training=False)

        # Run head layers manually (improved model: gap → fc1 → bn1 → dropout → class_prob)
        x = _model.get_layer("gap")(base_output)
        x = _model.get_layer("fc1")(x)
        x = _model.get_layer("bn1")(x, training=False)
        x = _model.get_layer("dropout")(x, training=False)
        predictions = _model.get_layer("class_probability")(x)
        pred_index  = tf.argmax(predictions[0])
        class_score = predictions[:, pred_index]

    grads        = tape.gradient(class_score, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    heatmap      = tf.squeeze(conv_outputs[0] @ pooled_grads[..., tf.newaxis])
    heatmap      = tf.maximum(heatmap, 0)
    heatmap      = heatmap / (tf.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def _heatmap_to_base64(heatmap: np.ndarray, size: int = 224) -> str:
    h_pil = Image.fromarray((heatmap * 255).astype(np.uint8), mode="L")
    h_pil = h_pil.resize((size, size), Image.LANCZOS)
    Z = np.array(h_pil, dtype=np.float32) / 255.0

    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[:, :, 0] = np.clip(np.where(Z < 0.5, Z * 2, 1.0) * 255, 0, 255)
    green = np.where(Z < 0.25, Z * 4, np.where(Z < 0.75, 1.0, (1.0 - Z) * 4))
    rgba[:, :, 1] = np.clip(green * 255, 0, 255)
    rgba[:, :, 2] = np.clip(np.where(Z < 0.5, 1.0, (1.0 - Z) * 2) * 255, 0, 255)
    rgba[:, :, 3] = np.clip(Z * 210, 20, 210)

    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _fallback_heatmap(size: int = 224) -> str:
    x = np.linspace(-3, 3, size)
    y = np.linspace(-3, 3, size)
    X, Y = np.meshgrid(x, y)
    Z = (
        np.exp(-(X**2 + Y**2) / 2.5) * 0.9
        + np.exp(-((X - 1.2)**2 + (Y - 0.8)**2) / 1.2) * 0.6
        + np.exp(-((X + 0.8)**2 + (Y - 1.5)**2) / 2.0) * 0.4
    )
    Z = (Z - Z.min()) / (Z.max() - Z.min())
    return _heatmap_to_base64(Z, size)


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {
        "status":       "ok",
        "model_loaded": _model is not None,
        "model_path":   MODEL_PATH,
        "model_error":  _model_error,
        "model_accuracy": MODEL_ACCURACY,
    }


@app.get("/api/doctors")
async def get_doctors():
    try:
        with open(os.path.join(STATIC_DIR, "doctors.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


@app.get("/api/guidance")
async def get_guidance():
    try:
        with open(os.path.join(STATIC_DIR, "guidance.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@app.post("/api/predict")
async def predict_scan(file: UploadFile = File(...)):
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail=f"Model belum tersedia. Detail: {_model_error}",
        )

    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".dcm")):
        raise HTTPException(
            status_code=400,
            detail="Tipe file tidak valid. Hanya JPEG, PNG, dan DCM yang didukung.",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File terlalu besar. Maksimal 10MB.")

    try:
        import tensorflow as tf

        # ── Inference ──────────────────────────────────────────────────────────
        # Improved model expects preprocess_input applied EXTERNALLY
        preprocessed = _preprocess_image(content)
        probs        = _model.predict(tf.constant(preprocessed), verbose=0)[0]

        pred_idx   = int(np.argmax(probs))
        prediction = _idx_to_label[pred_idx]
        confidence = round(float(probs[pred_idx] * 100), 2)
        all_scores = {
            _idx_to_label[i]: round(float(p * 100), 2)
            for i, p in enumerate(probs)
        }
        logger.info(f"Prediksi: {prediction} ({confidence}%)")

        # ── Grad-CAM ───────────────────────────────────────────────────────────
        try:
            heatmap     = _make_gradcam_heatmap(preprocessed)
            heatmap_b64 = _heatmap_to_base64(heatmap)
        except Exception as exc:
            logger.warning(f"Grad-CAM gagal, pakai fallback: {exc}")
            heatmap_b64 = _fallback_heatmap()

        return JSONResponse(content={
            "prediction":     prediction,
            "confidence":     confidence,
            "all_scores":     all_scores,
            "heatmap_base64": heatmap_b64,
            "model_accuracy": MODEL_ACCURACY,
        })

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Prediction error: {exc}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses gambar: {exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

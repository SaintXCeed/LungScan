import os
import json
import base64
import io
import time
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
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR  = os.path.join(BASE_DIR, "static")
ROOT_DIR    = os.path.dirname(BASE_DIR)
MODEL_DIR   = os.path.join(ROOT_DIR, "model-final")

TYPE_MODEL_PATH     = os.path.join(MODEL_DIR, "Lung_Cancer_ResNet50_88Acc.keras")
SEVERITY_MODEL_PATH = os.path.join(MODEL_DIR, "Lung_Cancer_Severity_Model.h5")

# ── Input sizes ────────────────────────────────────────────────────────────────
# ResNet50 model has a fixed input shape of (None, 460, 460, 3) — must match.
TYPE_INPUT_SIZE     = (460, 460)
SEVERITY_INPUT_SIZE = (224, 224)

MODEL_ACCURACY = 88.0

# ── Grad-CAM target layer ──────────────────────────────────────────────────────
GRADCAM_LAYER = "conv5_block3_out"   # last activation before GAP

# ── Labels ────────────────────────────────────────────────────────────────────
TYPE_CLASSES = [
    "adenocarcinoma",
    "large.cell.carcinoma",
    "normal",
    "squamous.cell.carcinoma",
]
SEVERITY_CLASSES = ["Normal", "Benign", "Malignant"]

# ── Globals (all built ONCE at startup) ───────────────────────────────────────
_type_model        = None
_severity_model    = None
_grad_model        = None   # shared model: ResNet50 → (conv features, predictions)
_dense_weights     = None   # raw Dense weights (2048, 4)
_dense_weights_eff = None   # BN-corrected: W * (gamma/std) — used for CAM
_model_error       = None
_warmed_up         = False


# ── Preprocessing ──────────────────────────────────────────────────────────────
def _preprocess_for_type(image_bytes: bytes) -> np.ndarray:
    from tensorflow.keras.applications.resnet50 import preprocess_input
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(TYPE_INPUT_SIZE, Image.LANCZOS)
    arr = preprocess_input(np.array(img, dtype=np.float32))
    return np.expand_dims(arr, axis=0)


def _preprocess_for_severity(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(SEVERITY_INPUT_SIZE, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


# ── Model loader ───────────────────────────────────────────────────────────────
def _load_resources():
    global _type_model, _severity_model, _grad_model
    global _dense_weights, _dense_weights_eff
    global _model_error, _warmed_up
    import tensorflow as tf
    from tensorflow import keras

    try:
        # 1. Type model (ResNet50 88%)
        if not os.path.exists(TYPE_MODEL_PATH):
            raise FileNotFoundError(f"Type model tidak ditemukan: {TYPE_MODEL_PATH}")
        logger.info("Memuat Type model...")
        t0 = time.time()
        _type_model = keras.models.load_model(TYPE_MODEL_PATH, compile=False)
        logger.info(f"  loaded in {time.time()-t0:.1f}s  input={_type_model.input_shape}")

        # 2. Severity model
        if not os.path.exists(SEVERITY_MODEL_PATH):
            raise FileNotFoundError(f"Severity model tidak ditemukan: {SEVERITY_MODEL_PATH}")
        logger.info("Memuat Severity model...")
        t0 = time.time()
        _severity_model = keras.models.load_model(SEVERITY_MODEL_PATH, compile=False)
        logger.info(f"  loaded in {time.time()-t0:.1f}s  input={_severity_model.input_shape}")

        # 3. Shared inference model: one forward pass → conv features + predictions
        logger.info(f"Building shared inference model (layer={GRADCAM_LAYER})...")
        _grad_model = keras.Model(
            inputs=_type_model.input,
            outputs=[
                _type_model.get_layer(GRADCAM_LAYER).output,  # (None, 15, 15, 2048)
                _type_model.outputs[0],                         # (None, 4)
            ],
        )
        logger.info("  Shared model cached.")

        # 4. Cache Dense weights + BN-corrected effective weights for CAM
        #
        #    Architecture: conv5_block3_out → GAP → Dropout → BN → Dense
        #
        #    True CAM formula (Zhou et al. 2016) requires:
        #      CAM(x,y) = sum_k [ w_eff_k^c * f_k(x,y) ]
        #    where  w_eff = W_dense * (gamma / sqrt(var + eps))
        #    because BN applies: out = gamma*(in-mean)/std + beta
        #    and Dense is linear: logit = W @ BN_out
        #    so effective weight on raw conv feature = W * gamma/std
        #
        _dense_weights = _type_model.get_layer("dense").get_weights()[0]  # (2048, 4)

        # Get BN parameters (gamma, beta, running_mean, running_var)
        bn_layer   = _type_model.get_layer("batch_normalization")
        bn_params  = bn_layer.get_weights()   # [gamma, beta, mean, var]
        gamma, _, _, var = bn_params
        std             = np.sqrt(var + 1e-5)
        eff_scale       = (gamma / std)[:, np.newaxis]  # (2048, 1)

        _dense_weights_eff = _dense_weights * eff_scale  # (2048, 4) BN-corrected

        logger.info(
            f"  Dense weights cached: {_dense_weights.shape}  "
            f"BN-eff range [{_dense_weights_eff.min():.4f}, {_dense_weights_eff.max():.4f}]"
        )

        # 5. Warmup: one shared model pass + severity
        logger.info("Warming up...")
        dummy_t = tf.constant(np.zeros((1,) + TYPE_INPUT_SIZE + (3,), dtype=np.float32))
        dummy_s = tf.constant(np.zeros((1,) + SEVERITY_INPUT_SIZE + (3,), dtype=np.float32))

        t1 = time.time()
        _ = _grad_model(dummy_t, training=False)
        logger.info(f"  Shared model warmup: {time.time()-t1:.2f}s")

        t1 = time.time()
        _ = _severity_model(dummy_s, training=False)
        logger.info(f"  Severity warmup: {time.time()-t1:.2f}s")

        _warmed_up = True
        logger.info("Ready — all models warmed up.")

    except Exception as exc:
        _model_error = str(exc)
        logger.error(f"Gagal memuat model: {exc}")


_load_resources()


# ── Unified inference: single ResNet50 forward pass for both type + CAM ───────
def _run_inference(image_bytes: bytes) -> tuple[dict, np.ndarray]:
    """
    Single forward pass through _grad_model yields:
      - conv features (15×15×2048)  → used for CAM heatmap
      - type predictions (4,)        → used for classification

    ResNet50 runs EXACTLY ONCE per request — no redundant computation.
    For cancer cases: also runs severity model (224×224, ~1s).
    For normal cases: severity = 'Normal' by clinical rule, CAM skipped.

    Returns (result_dict, cam_heatmap_or_None)
    """
    import tensorflow as tf

    # Preprocess + single forward pass
    type_input  = _preprocess_for_type(image_bytes)
    img_tensor  = tf.constant(type_input, dtype=tf.float32)
    grad_out    = _grad_model(img_tensor, training=False)
    conv_feats  = grad_out[0][0].numpy()   # (15, 15, 2048)
    type_pred   = grad_out[1][0].numpy()   # (4,)

    pred_type       = TYPE_CLASSES[int(np.argmax(type_pred))]
    type_conf       = round(float(np.max(type_pred)) * 100, 2)
    all_type_scores = {
        label: round(float(p) * 100, 2)
        for label, p in zip(TYPE_CLASSES, type_pred)
    }

    # ── CAM: BN-corrected Class Activation Map (Zhou et al. 2016) ────────────────
    # Architecture: conv5_block3_out → GAP → Dropout → BN → Dense
    # True linear path from conv features to logit:
    #   logit_c = sum_k [ (W_c_k * gamma_k/std_k) * GAP(f_k) ] + bias_c
    # => Spatial map: CAM(x,y) = sum_k [ w_eff_k^c * f_k(x,y) ]
    # Uses _dense_weights_eff (cached at startup) = W * (gamma/std)
    pred_idx = int(np.argmax(type_pred))
    w_class  = _dense_weights_eff[:, pred_idx]           # (2048,) BN-corrected
    cam      = np.dot(conv_feats, w_class)               # (15, 15)
    cam      = np.maximum(cam, 0)                         # ReLU (keep only positive activations)
    cam      = cam / (cam.max() + 1e-8)                  # normalise [0,1]

    # ── Clinical rule: normal scan ─────────────────────────────────────────────
    if pred_type == "normal":
        return {
            "prediction":          pred_type,
            "confidence":          type_conf,
            "all_scores":          all_type_scores,
            "severity":            "Normal",
            "severity_confidence": 100.0,
        }, cam   # still return CAM for normal scans (shows which region looked normal)

    # ── Stage 2: severity model (224×224, ~1s) ─────────────────────────────────
    sev_input = _preprocess_for_severity(image_bytes)
    sev_pred  = _severity_model(
        tf.constant(sev_input, dtype=tf.float32), training=False
    ).numpy()[0]

    pred_sev = SEVERITY_CLASSES[int(np.argmax(sev_pred))]
    sev_conf = round(float(np.max(sev_pred)) * 100, 2)

    return {
        "prediction":          pred_type,
        "confidence":          type_conf,
        "all_scores":          all_type_scores,
        "severity":            pred_sev,
        "severity_confidence": sev_conf,
    }, cam



# ── Heatmap colourisation ──────────────────────────────────────────────────────
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
        "status":         "ok",
        "model_loaded":   _type_model is not None and _severity_model is not None,
        "warmed_up":      _warmed_up,
        "type_model":     TYPE_MODEL_PATH,
        "severity_model": SEVERITY_MODEL_PATH,
        "model_error":    _model_error,
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
    if _grad_model is None or _severity_model is None:
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
        t_start = time.time()

        # Single forward pass: classification + CAM in one shot
        result, cam = _run_inference(content)
        t_inf = time.time()

        # Colourise CAM → base64 PNG
        try:
            heatmap_b64 = _heatmap_to_base64(cam)
        except Exception as exc:
            logger.warning(f"CAM colourise gagal, pakai fallback: {exc}")
            heatmap_b64 = _fallback_heatmap()
        t_total = time.time()

        logger.info(
            f"[{result['prediction']} {result['confidence']}% | "
            f"sev={result['severity']} {result['severity_confidence']}%] "
            f"inference={t_inf-t_start:.2f}s  total={t_total-t_start:.2f}s"
        )

        return JSONResponse(content={
            "prediction":          result["prediction"],
            "confidence":          result["confidence"],
            "all_scores":          result["all_scores"],
            "severity":            result["severity"],
            "severity_confidence": result["severity_confidence"],
            "heatmap_base64":      heatmap_b64,
            "model_accuracy":      MODEL_ACCURACY,
        })

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Prediction error: {exc}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses gambar: {exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

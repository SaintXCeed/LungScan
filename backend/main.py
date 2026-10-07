import os
import json
import base64
import io
import time
import logging
import numpy as np
from PIL import Image
from scipy.stats import entropy as scipy_entropy
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

MODEL_ACCURACY = 82.0

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


# ── CT-Scan Validator ──────────────────────────────────────────────────────────
# Thresholds (tunable via env vars for easy adjustment)
_CT_MAX_SATURATION       = float(os.getenv("CT_MAX_SATURATION",       "0.18"))  # HSV S mean
_CT_MIN_DARK_RATIO       = float(os.getenv("CT_MIN_DARK_RATIO",       "0.25"))  # fraction of pixels with L < 60
_CT_MIN_ENTROPY          = float(os.getenv("CT_MIN_ENTROPY",          "3.5"))   # too low = solid/uniform
_CT_MAX_ENTROPY          = float(os.getenv("CT_MAX_ENTROPY",          "7.8"))   # too high = fully colourful photo
_CT_MIN_STDDEV           = float(os.getenv("CT_MIN_STDDEV",           "12.0"))  # not a blank/solid image
_CT_MIN_CENTER_DARK_RATIO= float(os.getenv("CT_MIN_CENTER_DARK_RATIO", "0.05")) # center-zone dark ratio; very conservative to avoid false-rejecting severe cases


def _validate_ct_scan(image_bytes: bytes) -> tuple[bool, str]:
    """
    Heuristic validator: checks whether an image looks like a lung CT-Scan
    based on pixel-level statistics.  Returns (is_valid, reason_string).

    A valid CT-Scan typically:
      1. Is nearly grayscale  → low HSV saturation
      2. Has a large dark background  → high dark-pixel ratio
      3. Has structured texture  → entropy in a plausible medical range
      4. Is not a solid blank image  → std-dev above a minimum
    """
    try:
        img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Work on a small thumbnail to keep it fast
        thumb = img_pil.copy()
        thumb.thumbnail((256, 256), Image.LANCZOS)
        arr = np.array(thumb, dtype=np.float32)  # (H, W, 3)  [0-255]

        # ── 1. Saturation check (HSV S-channel) ───────────────────────────────
        # Convert RGB [0-255] to HSV [0-1]
        arr_norm = arr / 255.0
        r, g, b = arr_norm[..., 0], arr_norm[..., 1], arr_norm[..., 2]
        cmax = np.maximum(np.maximum(r, g), b)
        cmin = np.minimum(np.minimum(r, g), b)
        delta = cmax - cmin
        # Saturation = delta / cmax  (0 where cmax==0)
        with np.errstate(invalid='ignore'):
            saturation = np.where(cmax > 0, delta / cmax, 0.0)
        mean_sat = float(saturation.mean())

        if mean_sat > _CT_MAX_SATURATION:
            return False, (
                f"Gambar terlalu berwarna (saturasi={mean_sat:.2f}, maks={_CT_MAX_SATURATION}). "
                "CT-Scan paru seharusnya hampir grayscale. "
                "Pastikan Anda mengunggah gambar CT-Scan dada yang valid."
            )

        # ── 2. Dark-pixel ratio (luminance proxy via grayscale) ───────────────
        gray = np.array(thumb.convert("L"), dtype=np.float32)  # (H, W)
        dark_ratio = float((gray < 60).mean())

        if dark_ratio < _CT_MIN_DARK_RATIO:
            return False, (
                f"Gambar memiliki terlalu sedikit area gelap (rasio gelap={dark_ratio:.2f}, "
                f"min={_CT_MIN_DARK_RATIO}). "
                "CT-Scan paru memiliki latar belakang hitam yang dominan. "
                "Pastikan Anda mengunggah gambar CT-Scan dada yang valid."
            )

        # ── 3. Entropy check (texture complexity) ─────────────────────────────
        hist, _ = np.histogram(gray.flatten(), bins=256, range=(0, 256))
        hist_prob = hist / (hist.sum() + 1e-10)
        img_entropy = float(scipy_entropy(hist_prob + 1e-10, base=2))

        if img_entropy < _CT_MIN_ENTROPY:
            return False, (
                f"Gambar terlalu seragam/polos (entropy={img_entropy:.2f}, "
                f"min={_CT_MIN_ENTROPY}). "
                "Pastikan Anda mengunggah gambar CT-Scan dada yang valid."
            )
        if img_entropy > _CT_MAX_ENTROPY:
            return False, (
                f"Gambar terlalu kompleks/berwarna-warni (entropy={img_entropy:.2f}, "
                f"maks={_CT_MAX_ENTROPY}). "
                "CT-Scan paru memiliki kompleksitas tekstur yang terbatas. "
                "Pastikan Anda mengunggah gambar CT-Scan dada yang valid."
            )

        # ── 4. Std-dev check (not blank) ──────────────────────────────────────
        std_dev = float(gray.std())
        if std_dev < _CT_MIN_STDDEV:
            return False, (
                f"Gambar tampak hampir kosong/solid (std={std_dev:.2f}, "
                f"min={_CT_MIN_STDDEV}). "
                "Pastikan Anda mengunggah gambar CT-Scan dada yang valid."
            )

        return True, "OK"

    except Exception as exc:
        logger.warning(f"CT-Scan validation error (skipping): {exc}")
        # If the validator itself crashes, allow the request through
        return True, "validation-skipped"


# ── Lung-region body-part check (WARNING only, never blocks) ──────────────────
def _check_lung_region(image_bytes: bytes) -> tuple[bool, str]:
    """
    Soft heuristic to detect whether the CT-Scan is likely of the CHEST/LUNG
    rather than another body part (brain, abdomen, etc.).

    Returns (looks_like_lung: bool, reason: str).
    This function NEVER causes a hard rejection — it only sets a warning flag.

    Key insight:
      - Lung CT (axial): center contains two dark lung fields (air ≈ pixel 0–60)
        → center dark ratio typically 20–60%
      - Brain CT (axial): center is filled with medium-gray brain tissue
        → center dark ratio typically 3–12%  (only small ventricles are dark)
      - Severe lung cancer with large mass: center still has SOME dark areas
        from residual lung/pleural space → typically ≥ 8%

    Threshold is intentionally very conservative (5%) to avoid false-warning
    on severe pathological cases (large tumors, pleural effusion, white-out).
    Env var CT_MIN_CENTER_DARK_RATIO can relax/tighten this.
    """
    try:
        img_pil = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale
        thumb = img_pil.copy()
        thumb.thumbnail((256, 256), Image.LANCZOS)
        gray = np.array(thumb, dtype=np.float32)  # (H, W)

        h, w = gray.shape

        # ── Center zone: middle 50% of both dimensions ────────────────────────
        cy1, cy2 = h // 4, 3 * h // 4
        cx1, cx2 = w // 4, 3 * w // 4
        center = gray[cy1:cy2, cx1:cx2]

        center_dark_ratio = float((center < 60).mean())

        logger.debug(f"Body-part check: center_dark_ratio={center_dark_ratio:.3f} threshold={_CT_MIN_CENTER_DARK_RATIO}")

        if center_dark_ratio < _CT_MIN_CENTER_DARK_RATIO:
            return False, (
                f"Bagian tengah gambar hampir tidak memiliki area gelap "
                f"(rasio={center_dark_ratio:.2f}, min={_CT_MIN_CENTER_DARK_RATIO}). "
                "Gambar ini kemungkinan bukan CT-Scan dada/paru. "
                "CT-Scan kepala, perut, atau bagian tubuh lain mungkin menghasilkan prediksi yang tidak akurat. "
                "Pastikan Anda mengunggah CT-Scan dada (thorax) yang benar."
            )

        return True, "OK"

    except Exception as exc:
        logger.warning(f"Lung-region check error (skipping): {exc}")
        return True, "check-skipped"


# ── Preprocessing ──────────────────────────────────────────────────────────────
def _preprocess_for_type(image_bytes: bytes) -> np.ndarray:
    from keras.applications.resnet50 import preprocess_input
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
    import keras
    logger.info(f"Using standalone Keras {keras.__version__}")

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

    # ── Stage 2: severity model  ─────────────────────────────────
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


@app.get("/api/metrics")
async def get_model_metrics():
    """
    Returns pre-computed evaluation metrics for the ResNet50 type classification model.
    Computed on the full test set (315 images, 4 classes).
    """
    try:
        with open(os.path.join(STATIC_DIR, "model_metrics.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"overall": {"accuracy": MODEL_ACCURACY}, "per_class": {}}


@app.get("/api/severity-metrics")
async def get_severity_metrics():
    """
    Returns pre-computed evaluation metrics for the Severity classification model.
    Evaluated on validation cancer images (59 samples: Benign Stage I + Malignant Stage III).
    Normal severity is determined by clinical rule (not the model), so it is excluded.
    """
    try:
        with open(os.path.join(STATIC_DIR, "severity_metrics.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"overall": {}, "per_class": {}}



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

    # ── CT-Scan validation (hard reject: clearly not a medical grayscale image)
    is_ct, reason = _validate_ct_scan(content)
    if not is_ct:
        logger.warning(f"Rejected non-CT image '{file.filename}': {reason}")
        raise HTTPException(
            status_code=422,
            detail={
                "code":    "INVALID_CT_SCAN",
                "message": reason,
            },
        )

    # ── Body-part check (soft warning: may not be chest CT — never blocks) ──────
    looks_like_lung, body_part_reason = _check_lung_region(content)
    if not looks_like_lung:
        logger.warning(f"Body-part warning for '{file.filename}': {body_part_reason}")

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

        # Warning flags (never block — only inform)
        low_confidence  = result["confidence"] < 45.0
        body_part_warn  = not looks_like_lung
        any_warning     = low_confidence or body_part_warn

        return JSONResponse(content={
            "prediction":          result["prediction"],
            "confidence":          result["confidence"],
            "all_scores":          result["all_scores"],
            "severity":            result["severity"],
            "severity_confidence": result["severity_confidence"],
            "heatmap_base64":      heatmap_b64,
            "model_accuracy":      MODEL_ACCURACY,
            "validation_warning":  any_warning,
            "body_part_warning":   body_part_warn,
            "body_part_reason":    body_part_reason if body_part_warn else None,
        })

    except HTTPException:
        raise

    except Exception as exc:
        logger.error(f"Prediction error: {exc}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses gambar: {exc}")


# ── Dataset Documentation API ──────────────────────────────────────────────────
DATASET_CHEST_CT = os.path.join(MODEL_DIR, "chest-ctscan-images", "test")
DATASET_IQOTHNCCD = os.path.join(
    MODEL_DIR,
    "The IQ-OTHNCCD lung cancer dataset",
    "The IQ-OTHNCCD lung cancer dataset",
)

# Mapping: class key → (dir in chest-ct, display label, color, description)
DATASET_META = {
    "adenocarcinoma": {
        "label": "Adenocarcinoma",
        "color": "#ef4444",
        "description": "Tipe kanker paru paling umum (~40% kasus). Berasal dari sel kelenjar di tepi paru.",
        "dataset": "Chest CT-Scan Images",
        "dir": os.path.join(DATASET_CHEST_CT, "adenocarcinoma"),
    },
    "large_cell_carcinoma": {
        "label": "Large Cell Carcinoma",
        "color": "#f97316",
        "description": "Tipe agresif yang dapat muncul di bagian mana pun dari paru. Tumbuh cepat dan menyebar lebih dini.",
        "dataset": "Chest CT-Scan Images",
        "dir": os.path.join(DATASET_CHEST_CT, "large.cell.carcinoma"),
    },
    "squamous_cell_carcinoma": {
        "label": "Squamous Cell Carcinoma",
        "color": "#a855f7",
        "description": "Berasal dari sel skuamosa di saluran udara. Sering ditemukan di pusat paru dekat bronkus.",
        "dataset": "Chest CT-Scan Images",
        "dir": os.path.join(DATASET_CHEST_CT, "squamous.cell.carcinoma"),
    },
    "normal": {
        "label": "Normal",
        "color": "#22c55e",
        "description": "Jaringan paru sehat tanpa indikasi keganasan.",
        "dataset": "Chest CT-Scan Images",
        "dir": os.path.join(DATASET_CHEST_CT, "normal"),
    },
    "benign": {
        "label": "Benign (IQ-OTH)",
        "color": "#06b6d4",
        "description": "Tumor jinak. Tidak bersifat ganas, namun tetap memerlukan pemantauan medis.",
        "dataset": "IQ-OTH/NCCD Dataset",
        "dir": os.path.join(DATASET_IQOTHNCCD, "Bengin cases"),
    },
    "malignant": {
        "label": "Malignant (IQ-OTH)",
        "color": "#ec4899",
        "description": "Tumor ganas. Sel kanker aktif yang memerlukan penanganan segera.",
        "dataset": "IQ-OTH/NCCD Dataset",
        "dir": os.path.join(DATASET_IQOTHNCCD, "Malignant cases"),
    },
    "normal_iq": {
        "label": "Normal (IQ-OTH)",
        "color": "#84cc16",
        "description": "Paru normal dari dataset IQ-OTH/NCCD. Digunakan sebagai baseline dalam penelitian.",
        "dataset": "IQ-OTH/NCCD Dataset",
        "dir": os.path.join(DATASET_IQOTHNCCD, "Normal cases"),
    },
}


def _img_to_b64_thumb(path: str, size: int = 200) -> str | None:
    """Convert image file to base64 thumbnail."""
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        ext = os.path.splitext(path)[1].lower()
        fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
        img.save(buf, format=fmt, quality=80)
        mime = "image/jpeg" if fmt == "JPEG" else "image/png"
        return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        logger.warning(f"Cannot load image {path}: {e}")
        return None


@app.get("/api/dataset/info")
async def get_dataset_info():
    """Return dataset class metadata and image counts."""
    result = {}
    for key, meta in DATASET_META.items():
        d = meta["dir"]
        if os.path.isdir(d):
            files = [
                f for f in os.listdir(d)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            count = len(files)
        else:
            count = 0
        result[key] = {
            "label":       meta["label"],
            "color":       meta["color"],
            "description": meta["description"],
            "dataset":     meta["dataset"],
            "total":       count,
        }
    return JSONResponse(content=result)


@app.get("/api/dataset/images/{class_key}")
async def get_dataset_images(class_key: str, n: int = 10):
    """Return up to n thumbnail images for a given class key as base64."""
    if class_key not in DATASET_META:
        raise HTTPException(status_code=404, detail=f"Class '{class_key}' tidak ditemukan.")

    meta = DATASET_META[class_key]
    d    = meta["dir"]

    if not os.path.isdir(d):
        raise HTTPException(status_code=404, detail=f"Direktori dataset tidak ditemukan: {d}")

    files = sorted([
        f for f in os.listdir(d)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])[:n]

    images = []
    for fname in files:
        b64 = _img_to_b64_thumb(os.path.join(d, fname), size=220)
        if b64:
            images.append({"filename": fname, "src": b64})

    return JSONResponse(content={
        "class_key":   class_key,
        "label":       meta["label"],
        "color":       meta["color"],
        "description": meta["description"],
        "dataset":     meta["dataset"],
        "images":      images,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

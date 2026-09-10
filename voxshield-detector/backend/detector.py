import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
AASIST_DIR = ROOT / "model" / "aasist"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TARGET_SR = 16000
MODEL_SAMPLES = 64600          # ~4.04 seconds
WINDOW_STEP = 16000            # 1 second overlap step
MAX_WINDOWS = 20               # safety limit

MODEL = None
MODEL_ERROR = None


# ---------------------------------------------------------
# LOAD AASIST
# ---------------------------------------------------------

def _load_aasist():
    global MODEL, MODEL_ERROR

    if MODEL is not None:
        return MODEL

    try:
        if not AASIST_DIR.exists():
            raise RuntimeError(
                "AASIST source not found. Run: "
                "git clone https://github.com/clovaai/aasist.git model\\aasist"
            )

        sys.path.insert(0, str(AASIST_DIR))

        from models.AASIST import Model

        config = {
            "architecture": "AASIST",
            "nb_samp": 64600,
            "first_conv": 128,
            "filts": [70, [1, 32], [32, 32], [32, 64], [64, 64]],
            "gat_dims": [64, 32],
            "pool_ratios": [0.5, 0.7, 0.5, 0.5],
            "temperatures": [2.0, 2.0, 100.0, 100.0],
        }

        model = Model(config).to(DEVICE)

        weights = AASIST_DIR / "models" / "weights" / "AASIST.pth"

        if not weights.exists():
            raise RuntimeError(f"Checkpoint not found: {weights}")

        state = torch.load(weights, map_location=DEVICE)

        model.load_state_dict(state, strict=True)
        model.eval()

        MODEL = model
        MODEL_ERROR = None

        return MODEL

    except Exception as exc:
        MODEL_ERROR = str(exc)
        raise


# ---------------------------------------------------------
# AUDIO PREPROCESSING
# ---------------------------------------------------------

def _to_mono_16k(audio: np.ndarray, sr: int) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float32)

    # Stereo -> mono
    if audio.ndim == 2:
        audio = audio.mean(axis=1)

    if audio.size == 0:
        return audio

    # Normalize unusually large values
    peak = float(np.max(np.abs(audio)))

    if peak > 1.5:
        audio = audio / peak

    # Resample
    if sr != TARGET_SR:
        audio = resample_poly(
            audio,
            TARGET_SR,
            sr
        ).astype(np.float32)

    return np.nan_to_num(audio).astype(np.float32)


# ---------------------------------------------------------
# SPEECH ESTIMATION
# ---------------------------------------------------------

def _speech_seconds(audio: np.ndarray, sr: int) -> float:
    frame = int(0.02 * sr)

    if len(audio) < frame:
        return 0.0

    usable = 0

    threshold = max(
        0.003,
        float(np.percentile(np.abs(audio), 60)) * 0.5
    )

    for i in range(0, len(audio) - frame + 1, frame):

        chunk = audio[i:i + frame]

        rms = float(
            np.sqrt(
                np.mean(chunk ** 2) + 1e-12
            )
        )

        if rms > threshold:
            usable += frame

    return usable / sr


# ---------------------------------------------------------
# CREATE 4-SECOND WINDOWS
# ---------------------------------------------------------

def _make_windows(audio: np.ndarray):
    """
    Creates overlapping ~4 second windows.

    Window length = 64600 samples (~4.04 sec)
    Step = 16000 samples (1 sec)

    Example:

    Audio:
    |-----------------------------|

    Windows:
    |--------4 sec--------|
         |--------4 sec--------|
              |--------4 sec--------|
                   |--------4 sec--------|
    """

    if len(audio) == 0:
        return []

    # Short audio
    if len(audio) < MODEL_SAMPLES:

        repeats = int(
            np.ceil(MODEL_SAMPLES / len(audio))
        )

        padded = np.tile(
            audio,
            repeats
        )[:MODEL_SAMPLES]

        return [
            padded.astype(np.float32)
        ]

    windows = []

    start = 0

    while start + MODEL_SAMPLES <= len(audio):

        window = audio[
            start:start + MODEL_SAMPLES
        ]

        windows.append(
            window.astype(np.float32)
        )

        if len(windows) >= MAX_WINDOWS:
            break

        start += WINDOW_STEP

    # Include final portion if it wasn't already covered
    final_start = len(audio) - MODEL_SAMPLES

    if (
        final_start > 0
        and len(windows) < MAX_WINDOWS
        and (
            not windows
            or final_start != (len(windows) - 1) * WINDOW_STEP
        )
    ):
        windows.append(
            audio[
                final_start:final_start + MODEL_SAMPLES
            ].astype(np.float32)
        )

    return windows


# ---------------------------------------------------------
# MODEL PREDICTION
# ---------------------------------------------------------

def _predict_windows(model, windows):

    if not windows:
        return []

    batch = np.stack(windows)

    x = torch.from_numpy(batch).to(DEVICE)

    with torch.inference_mode():

        _, logits = model(
            x,
            Freq_aug=False
        )

        probs = torch.softmax(
            logits.float(),
            dim=1
        )

    probs = probs.detach().cpu().numpy()

    results = []

    for probability in probs:

        # AASIST training labels:
        # class 0 = spoof
        # class 1 = bonafide

        ai_prob = float(probability[0])
        human_prob = float(probability[1])

        results.append({
            "ai_probability": round(ai_prob, 4),
            "human_probability": round(human_prob, 4)
        })

    return results


# ---------------------------------------------------------
# COMPLETE AUDIO ANALYSIS
# ---------------------------------------------------------

def analyze_audio(audio: np.ndarray, sr: int) -> dict:

    started = time.perf_counter()

    # Convert to mono 16 kHz
    audio = _to_mono_16k(
        audio,
        sr
    )

    duration = len(audio) / TARGET_SR

    speech = _speech_seconds(
        audio,
        TARGET_SR
    )

    # Not enough speech
    if speech < 1.0:

        return {
            "status": "ok",
            "verdict": "INSUFFICIENT SPEECH",

            "human_probability": None,
            "ai_probability": None,

            "usable_speech_seconds": round(
                speech,
                2
            ),

            "duration_seconds": round(
                duration,
                2
            ),

            "window_count": 0,

            "detector": "AASIST",
            "model_status": "ready",

            "latency_ms": round(
                (time.perf_counter() - started) * 1000,
                1
            ),

            "reason":
                "Not enough usable speech for a reliable detector window."
        }

    # Load model
    try:

        model = _load_aasist()

    except Exception as exc:

        return {
            "status": "error",
            "verdict": "DETECTOR UNAVAILABLE",

            "human_probability": None,
            "ai_probability": None,

            "usable_speech_seconds": round(
                speech,
                2
            ),

            "duration_seconds": round(
                duration,
                2
            ),

            "window_count": 0,

            "detector": "AASIST",
            "model_status": "unavailable",

            "error": str(exc)
        }

    # Create overlapping windows
    windows = _make_windows(audio)

    # Run AASIST
    scores = _predict_windows(
        model,
        windows
    )

    if not scores:

        return {
            "status": "error",
            "verdict": "NO WINDOWS",
            "error": "Could not create detector windows."
        }

    # -----------------------------------------------------
    # AGGREGATION
    # -----------------------------------------------------

    ai_scores = [
        x["ai_probability"]
        for x in scores
    ]

    human_scores = [
        x["human_probability"]
        for x in scores
    ]

    mean_ai = float(
        np.mean(ai_scores)
    )

    mean_human = float(
        np.mean(human_scores)
    )

    max_ai = float(
        np.max(ai_scores)
    )

    max_human = float(
        np.max(human_scores)
    )

    # -----------------------------------------------------
    # VERDICT
    # -----------------------------------------------------

    if mean_ai >= 0.70:

        verdict = "POSSIBLE AI-CLONED VOICE"

    elif mean_human >= 0.70:

        verdict = "HUMAN LIKELY"

    else:

        verdict = "UNCERTAIN"

    latency = (
        time.perf_counter() - started
    ) * 1000

    return {

        "status": "ok",

        "verdict": verdict,

        "human_probability": round(
            mean_human,
            4
        ),

        "ai_probability": round(
            mean_ai,
            4
        ),

        "max_ai_probability": round(
            max_ai,
            4
        ),

        "max_human_probability": round(
            max_human,
            4
        ),

        "usable_speech_seconds": round(
            speech,
            2
        ),

        "duration_seconds": round(
            duration,
            2
        ),

        "window_count": len(windows),

        "window_scores": scores,

        "detector": "AASIST",

        "model_status": "ready",

        "device": str(DEVICE),

        "latency_ms": round(
            latency,
            1
        ),

        "reason":
            "AASIST evaluated overlapping ~4-second windows with a 1-second step."
    }


# ---------------------------------------------------------
# FILE ANALYSIS
# ---------------------------------------------------------

def analyze_file(path: str) -> dict:

    audio, sr = sf.read(
        path,
        dtype="float32",
        always_2d=False
    )

    return analyze_audio(
        audio,
        sr
    )
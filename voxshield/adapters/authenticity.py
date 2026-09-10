from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

from voxshield.schemas import AnalysisStatus, AuthenticityResult
from voxshield.time import utc_now


class AASISTAuthenticityDetector:
    """AASIST adapter; training labels are class 0=spoof and class 1=bonafide."""

    def __init__(self, checkpoint: str | None = None, source_dir: str | None = None, model=None):
        self._model = model
        self._warning = None
        if model is None:
            self._load(checkpoint, source_dir)

    def _load(self, checkpoint: str | None, source_dir: str | None) -> None:
        checkpoint_path = Path(checkpoint) if checkpoint else None
        source_path = Path(source_dir) if source_dir else None
        if not checkpoint_path or not checkpoint_path.is_file():
            self._warning = "AASIST checkpoint is missing."
            return
        if not source_path or not (source_path / "models" / "AASIST.py").is_file():
            self._warning = "AASIST source is missing."
            return
        try:
            import torch

            sys.path.insert(0, str(source_path))
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
            loaded = Model(config)
            state = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
            loaded.load_state_dict(state, strict=True)
            loaded.eval()
            self._model = _TorchAASIST(loaded)
        except Exception as exc:
            self._warning = f"AASIST loading failed: {type(exc).__name__}"
        finally:
            if sys.path and sys.path[0] == str(source_path):
                sys.path.pop(0)

    @property
    def available(self) -> bool:
        return self._model is not None

    async def analyze(self, audio: bytes, sequence: int) -> AuthenticityResult:
        samples = struct.iter_unpack("<h", audio[: len(audio) // 2 * 2])
        square_sum = sum(value[0] ** 2 for value in samples)
        rms = math.sqrt(square_sum / (len(audio) // 2)) if len(audio) >= 2 else 0
        speech = len(audio) / 32000 if len(audio) >= 320 and rms >= 100 else 0
        common = dict(
            usable_speech_seconds=speech,
            detector_name="AASIST",
            timestamp=utc_now(),
            sequence=sequence,
        )
        if speech < 1:
            return AuthenticityResult(status=AnalysisStatus.INSUFFICIENT_SPEECH, **common)
        if not self._model:
            return AuthenticityResult(
                status=AnalysisStatus.UNAVAILABLE, warnings=[self._warning], **common
            )
        try:
            spoof, bonafide = map(float, self._model.predict_pcm16(audio))
            if not all(math.isfinite(x) and 0 <= x <= 1 for x in (spoof, bonafide)):
                raise ValueError("invalid probabilities")
            total = spoof + bonafide
            if total <= 0:
                raise ValueError("invalid probability sum")
            return AuthenticityResult(
                status=AnalysisStatus.READY,
                ai_probability=spoof / total,
                human_probability=bonafide / total,
                rolling_ai_probability=spoof / total,
                valid_windows=1,
                **common,
            )
        except Exception as exc:
            return AuthenticityResult(
                status=AnalysisStatus.ERROR,
                warnings=[f"Invalid detector output: {type(exc).__name__}"],
                **common,
            )


class _TorchAASIST:
    def __init__(self, model):
        self.model = model

    def predict_pcm16(self, audio: bytes):
        import torch

        signal = torch.frombuffer(bytearray(audio), dtype=torch.int16).float() / 32768
        if signal.numel() < 64600:
            signal = signal.repeat(math.ceil(64600 / signal.numel()))
        with torch.inference_mode():
            _, logits = self.model(signal[:64600].unsqueeze(0), Freq_aug=False)
            return torch.softmax(logits.float(), dim=1)[0].tolist()

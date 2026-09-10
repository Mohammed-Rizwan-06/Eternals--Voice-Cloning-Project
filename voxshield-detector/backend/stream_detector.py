import numpy as np
import torch

from . import detector


class StreamingDetector:

    def __init__(self):

        # Rolling audio buffer
        self.buffer = np.array(
            [],
            dtype=np.float32
        )

        # AASIST needs approximately 4.04 seconds
        self.window_samples = (
            detector.MODEL_SAMPLES
        )

        # Analyze once every 1 second
        self.step_samples = (
            detector.TARGET_SR
        )

        # Number of samples already analyzed
        self.last_processed_length = 0

    def add_audio(self, audio: np.ndarray):

        self.buffer = np.concatenate(
            [
                self.buffer,
                audio
            ]
        )

        # Keep approximately 8 seconds
        max_samples = (
            detector.TARGET_SR * 8
        )

        if len(self.buffer) > max_samples:

            self.buffer = self.buffer[
                -max_samples:
            ]

        # If old samples were removed, reset
        # the analysis position.
        if self.last_processed_length > len(
            self.buffer
        ):

            self.last_processed_length = 0

    def ready(self):

        return (
            len(self.buffer)
            >= self.window_samples
        )

    def should_analyze(self):

        if not self.ready():
            return False

        # Wait for approximately one second
        # of new audio before another prediction.
        return (
            len(self.buffer)
            - self.last_processed_length
            >= self.step_samples
        )

    def analyze(self):

        if not self.ready():
            return None

        if not self.should_analyze():
            return None

        model = detector._load_aasist()

        # Take the most recent ~4.04 seconds.
        window = self.buffer[
            -self.window_samples:
        ]

        x = torch.from_numpy(
            window.astype(np.float32)
        ).unsqueeze(0).to(
            detector.DEVICE
        )

        with torch.inference_mode():

            _, logits = model(
                x,
                Freq_aug=False
            )

            probs = torch.softmax(
                logits.float(),
                dim=1
            )[0]

        # Convert probabilities to NumPy
        probs = probs.cpu().numpy()

        # -------------------------------------------------
        # TEMPORARY DEBUG OUTPUT
        # -------------------------------------------------

        print("\n========== AASIST DEBUG ==========")

        print(
            "RAW LOGITS:",
            logits.cpu().numpy()
        )

        print(
            "RAW PROBS:",
            probs
        )

        print(
            "PROBABILITY 0:",
            float(probs[0])
        )

        print(
            "PROBABILITY 1:",
            float(probs[1])
        )

        print(
            "==================================\n"
        )

        # -------------------------------------------------
        # CURRENT INTERPRETATION
        # DO NOT CHANGE THIS YET
        # -------------------------------------------------

        ai_probability = float(
            probs[0]
        )

        human_probability = float(
            probs[1]
        )

        if ai_probability >= 0.70:

            verdict = (
                "POSSIBLE AI-CLONED VOICE"
            )

        elif human_probability >= 0.70:

            verdict = "HUMAN LIKELY"

        else:

            verdict = "UNCERTAIN"

        # Remember when this analysis happened.
        self.last_processed_length = len(
            self.buffer
        )

        return {

            "status": "ok",

            "verdict": verdict,

            "ai_probability": round(
                ai_probability,
                4
            ),

            "human_probability": round(
                human_probability,
                4
            ),

            "buffer_seconds": round(
                len(self.buffer)
                / detector.TARGET_SR,
                2
            ),

            "detector": "AASIST",

            "model_status": "ready"
        }
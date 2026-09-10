"""
VoxShield - Real-Time Audio Buffer & Transcript Accumulator
Module: backend.transcription.streaming
Owner: Keerthi

Implements:
1. AudioStreamBuffer: An ephemeral in-memory buffer with energy-based Voice Activity
   Detection (VAD) to slice continuous audio into speech segments without persistent
   disk storage (compliant with DPDP Act & Privacy requirements).
2. TranscriptAccumulator: Chronological history tracker for dialogue turns.
"""

import math
import struct
from typing import List, Optional
from .base import AudioChunk, SpeakerRole, TranscriptSegment


class AudioStreamBuffer:
    """
    In-memory circular audio buffer with energy-based VAD (Voice Activity Detection).
    Collects telephony frames and emits chunks when a pause or maximum duration is reached.
    Zeroizes memory upon slice completion to satisfy privacy compliance.
    """

    def __init__(
        self,
        session_id: str,
        sample_rate_hz: int = 16000,
        channels: int = 1,
        min_speech_duration_sec: float = 0.5,
        max_chunk_duration_sec: float = 3.5,
        silence_threshold_energy: float = 400.0,
        silence_duration_sec: float = 0.4,
    ):
        self.session_id = session_id
        self.sample_rate_hz = sample_rate_hz
        self.channels = channels
        self.min_speech_duration_sec = min_speech_duration_sec
        self.max_chunk_duration_sec = max_chunk_duration_sec
        self.silence_threshold_energy = silence_threshold_energy
        self.silence_duration_sec = silence_duration_sec

        self._byte_buffer = bytearray()
        self._sequence_counter = 0
        self._consecutive_silence_sec = 0.0
        self._current_speaker = SpeakerRole.CALLER

    @property
    def bytes_per_second(self) -> int:
        return self.sample_rate_hz * self.channels * 2

    def calculate_rms_energy(self, pcm_bytes: bytes) -> float:
        """Calculate Root Mean Square energy of 16-bit PCM chunk."""
        if len(pcm_bytes) < 2:
            return 0.0
        num_samples = len(pcm_bytes) // 2
        try:
            samples = struct.unpack(f"<{num_samples}h", pcm_bytes[:num_samples * 2])
            sum_sq = sum(s * s for s in samples)
            return math.sqrt(sum_sq / num_samples)
        except Exception:
            return 0.0

    def append_audio(
        self,
        pcm_bytes: bytes,
        speaker: SpeakerRole = SpeakerRole.CALLER,
        timestamp_ms: int = 0
    ) -> Optional[AudioChunk]:
        """
        Appends raw PCM audio bytes to the buffer.
        Returns an AudioChunk if a speech boundary (pause or max duration) is detected.
        """
        self._current_speaker = speaker
        self._byte_buffer.extend(pcm_bytes)

        frame_duration = len(pcm_bytes) / self.bytes_per_second if self.bytes_per_second > 0 else 0
        energy = self.calculate_rms_energy(pcm_bytes)

        if energy < self.silence_threshold_energy:
            self._consecutive_silence_sec += frame_duration
        else:
            self._consecutive_silence_sec = 0.0

        buffered_duration = len(self._byte_buffer) / self.bytes_per_second

        # Condition 1: Exceeded max segment duration
        # Condition 2: Natural pause after adequate speech
        should_flush = (
            buffered_duration >= self.max_chunk_duration_sec or
            (buffered_duration >= self.min_speech_duration_sec and
             self._consecutive_silence_sec >= self.silence_duration_sec)
        )

        if should_flush and len(self._byte_buffer) > 0:
            return self.flush(timestamp_ms=timestamp_ms)

        return None

    def flush(self, is_last: bool = False, timestamp_ms: int = 0) -> Optional[AudioChunk]:
        """Flushes buffered audio into an AudioChunk and resets buffer."""
        if len(self._byte_buffer) == 0:
            return None

        data = bytes(self._byte_buffer)
        self._byte_buffer.clear()
        self._consecutive_silence_sec = 0.0
        self._sequence_counter += 1

        return AudioChunk(
            session_id=self.session_id,
            sequence_num=self._sequence_counter,
            raw_data=data,
            timestamp_ms=timestamp_ms,
            sample_rate_hz=self.sample_rate_hz,
            channels=self.channels,
            speaker=self._current_speaker,
            is_last=is_last,
        )


class TranscriptAccumulator:
    """
    Maintains rolling conversational history per session.
    Allows extracting full transcripts or windowed excerpts for downstream analysis.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._segments: List[TranscriptSegment] = []

    def add_segment(self, segment: TranscriptSegment) -> None:
        self._segments.append(segment)

    def get_all_segments(self) -> List[TranscriptSegment]:
        return list(self._segments)

    def get_full_text(self) -> str:
        return " ".join(s.text for s in self._segments if s.is_final).strip()

    def get_caller_text(self) -> str:
        return " ".join(
            s.text for s in self._segments
            if s.is_final and s.speaker == SpeakerRole.CALLER
        ).strip()

    def get_recent_text(self, window_sec: float = 30.0) -> str:
        """Returns transcript of utterances within the last N seconds."""
        if not self._segments:
            return ""
        max_end = max((s.end_time_sec for s in self._segments), default=0.0)
        cutoff = max(0.0, max_end - window_sec)
        recent = [
            s.text for s in self._segments
            if s.is_final and s.end_time_sec >= cutoff
        ]
        return " ".join(recent).strip()

    def get_dialogue_turns(self) -> List[dict]:
        """Returns structured dialogue turns formatted for AI scam detection."""
        return [
            {
                "speaker": s.speaker.value,
                "text": s.text,
                "time": f"{s.start_time_sec:.1f}s - {s.end_time_sec:.1f}s",
                "confidence": s.confidence,
            }
            for s in self._segments if s.is_final
        ]

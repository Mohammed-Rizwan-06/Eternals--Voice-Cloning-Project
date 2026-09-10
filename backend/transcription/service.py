"""
VoxShield - Transcription Service
Module: backend.transcription.service
Owner: Keerthi

High-level session coordinator managing real-time telephony audio streams,
buffering, speech-to-text transcription, and event broadcasting to downstream
consumers (Yash's Risk Engine, Mohit's Frontend WebSocket).
"""

import asyncio
from typing import Callable, Coroutine, Dict, List, Optional
from .base import AudioChunk, BaseTranscriber, SpeakerRole, TranscriptSegment
from .streaming import AudioStreamBuffer, TranscriptAccumulator
from .whisper_engine import MockStreamingTranscriber, WhisperTranscriber


class TranscriptionService:
    """
    Main transcription orchestration service.
    Integrates directly with Rizwan's Telephony ingestion and streams
    results to Keerthi's Scam Intelligence and Yash's Risk Engine.
    """

    def __init__(
        self,
        transcriber: Optional[BaseTranscriber] = None,
        sample_rate_hz: int = 16000,
    ):
        self.sample_rate_hz = sample_rate_hz
        self.transcriber: BaseTranscriber = transcriber or WhisperTranscriber(
            model_size="base", fallback_to_mock=True
        )

        # Active session state
        self._buffers: Dict[str, AudioStreamBuffer] = {}
        self._accumulators: Dict[str, TranscriptAccumulator] = {}
        self._callbacks: List[Callable[[TranscriptSegment], Coroutine]] = []

    def register_callback(self, callback: Callable[[TranscriptSegment], Coroutine]) -> None:
        """Register async listener for real-time transcript updates."""
        self._callbacks.append(callback)

    def initialize_session(self, session_id: str) -> None:
        """Initialize session buffer and accumulator."""
        if session_id not in self._buffers:
            self._buffers[session_id] = AudioStreamBuffer(
                session_id=session_id,
                sample_rate_hz=self.sample_rate_hz,
            )
        if session_id not in self._accumulators:
            self._accumulators[session_id] = TranscriptAccumulator(session_id=session_id)

    async def ingest_audio_chunk(
        self,
        session_id: str,
        audio_bytes: bytes,
        speaker: SpeakerRole = SpeakerRole.CALLER,
        timestamp_ms: int = 0,
        is_last: bool = False
    ) -> List[TranscriptSegment]:
        """
        Ingest raw audio bytes from telephony (Rizwan).
        Buffers bytes, runs VAD, triggers STT on speech completion,
        and broadcasts segments to subscribers.
        """
        self.initialize_session(session_id)
        buf = self._buffers[session_id]

        ready_chunk = buf.append_audio(
            pcm_bytes=audio_bytes,
            speaker=speaker,
            timestamp_ms=timestamp_ms
        )

        if is_last and ready_chunk is None:
            ready_chunk = buf.flush(is_last=True, timestamp_ms=timestamp_ms)

        if ready_chunk is not None:
            return await self._process_chunk(ready_chunk)

        return []

    async def ingest_direct_text(
        self,
        session_id: str,
        speaker: SpeakerRole,
        text: str,
        start_sec: float = 0.0,
        end_sec: float = 1.0,
    ) -> TranscriptSegment:
        """
        Helper for testing or text-based mock telephony simulations.
        Directly injects recognized text into the session pipeline.
        """
        self.initialize_session(session_id)
        segment = TranscriptSegment(
            session_id=session_id,
            speaker=speaker,
            text=text,
            start_time_sec=start_sec,
            end_time_sec=end_sec,
            confidence=1.0,
            is_final=True,
        )
        self._accumulators[session_id].add_segment(segment)
        await self._broadcast_segment(segment)
        return segment

    async def _process_chunk(self, chunk: AudioChunk) -> List[TranscriptSegment]:
        segments = await self.transcriber.transcribe_chunk(chunk)
        acc = self._accumulators.get(chunk.session_id)

        for segment in segments:
            if acc:
                acc.add_segment(segment)
            await self._broadcast_segment(segment)

        return segments

    async def _broadcast_segment(self, segment: TranscriptSegment) -> None:
        """Notify all registered listeners."""
        for cb in self._callbacks:
            try:
                await cb(segment)
            except Exception as e:
                print(f"[TranscriptionService] Callback error: {e}")

    def get_full_transcript(self, session_id: str) -> str:
        acc = self._accumulators.get(session_id)
        return acc.get_full_text() if acc else ""

    def get_recent_transcript(self, session_id: str, window_sec: float = 30.0) -> str:
        acc = self._accumulators.get(session_id)
        return acc.get_recent_text(window_sec) if acc else ""

    def get_dialogue_turns(self, session_id: str) -> List[dict]:
        acc = self._accumulators.get(session_id)
        return acc.get_dialogue_turns() if acc else []

    def close_session(self, session_id: str) -> None:
        """Cleanup session resources."""
        self._buffers.pop(session_id, None)
        self._accumulators.pop(session_id, None)

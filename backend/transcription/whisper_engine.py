"""
VoxShield - Whisper Speech-to-Text Implementation
Module: backend.transcription.whisper_engine
Owner: Keerthi

Supports Whisper STT with multilingual & Indian accent optimization,
and includes a high-fidelity mock streaming transcriber for development/testing
without requiring heavy local GPU models or external APIs.
"""

import asyncio
import io
import math
import struct
import wave
from typing import List, Optional
from .base import AudioChunk, AudioEncoding, BaseTranscriber, SpeakerRole, TranscriptSegment


class MockStreamingTranscriber(BaseTranscriber):
    """
    Simulation STT engine for unit testing, CI/CD, and offline demos.
    Allows injecting pre-determined dialogue utterances per chunk or
    simulating realistic STT responses based on audio duration.
    """

    def __init__(self, script_dialogue: Optional[List[dict]] = None):
        self._script = script_dialogue or []
        self._script_index = 0
        self._current_time_sec = 0.0

    def set_script(self, script_dialogue: List[dict]) -> None:
        self._script = script_dialogue
        self._script_index = 0
        self._current_time_sec = 0.0

    async def transcribe_chunk(self, chunk: AudioChunk) -> List[TranscriptSegment]:
        duration = chunk.duration_sec
        start_t = self._current_time_sec
        end_t = start_t + duration
        self._current_time_sec = end_t

        # If a scripted scenario is loaded, pop the next dialogue turn
        if self._script and self._script_index < len(self._script):
            turn = self._script[self._script_index]
            self._script_index += 1
            speaker = SpeakerRole(turn.get("speaker", chunk.speaker.value))
            text = turn.get("text", "")
            return [
                TranscriptSegment(
                    session_id=chunk.session_id,
                    speaker=speaker,
                    text=text,
                    language=turn.get("language", "en"),
                    start_time_sec=start_t,
                    end_time_sec=end_t,
                    confidence=0.98,
                    is_final=True,
                )
            ]

        # Default fallback: generate synthetic speech indicator if audio has energy
        if len(chunk.raw_data) > 0:
            return [
                TranscriptSegment(
                    session_id=chunk.session_id,
                    speaker=chunk.speaker,
                    text=f"[Audio utterance seq={chunk.sequence_num} dur={duration:.1f}s]",
                    language="en",
                    start_time_sec=start_t,
                    end_time_sec=end_t,
                    confidence=0.92,
                    is_final=True,
                )
            ]
        return []

    async def transcribe_file(
        self,
        file_path: str,
        session_id: str,
        speaker: SpeakerRole = SpeakerRole.CALLER
    ) -> List[TranscriptSegment]:
        return [
            TranscriptSegment(
                session_id=session_id,
                speaker=speaker,
                text="Transcribed speech from audio file simulation.",
                start_time_sec=0.0,
                end_time_sec=5.0,
                confidence=0.95,
                is_final=True,
            )
        ]


class WhisperTranscriber(BaseTranscriber):
    """
    Production Whisper Transcriber.
    Attempts to use `faster-whisper` for low-latency streaming transcription.
    If unavailable or initialized in fallback mode, gracefully delegates
    to MockStreamingTranscriber.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "int8",
        language: Optional[str] = "en",
        fallback_to_mock: bool = True
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.fallback_to_mock = fallback_to_mock

        self._model = None
        self._is_ready = False
        self._mock_engine: Optional[MockStreamingTranscriber] = None

        self._init_engine()

    def _init_engine(self) -> None:
        try:
            from faster_whisper import WhisperModel
            # Attempt to initialize faster-whisper
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            self._is_ready = True
        except Exception as err:
            if self.fallback_to_mock:
                self._mock_engine = MockStreamingTranscriber()
                self._is_ready = True
            else:
                raise RuntimeError(
                    f"Failed to load faster-whisper and fallback_to_mock=False: {err}"
                ) from err

    @property
    def is_using_mock(self) -> bool:
        return self._mock_engine is not None

    def set_mock_script(self, script_dialogue: List[dict]) -> None:
        if self._mock_engine:
            self._mock_engine.set_script(script_dialogue)

    async def transcribe_chunk(self, chunk: AudioChunk) -> List[TranscriptSegment]:
        if self._mock_engine is not None:
            return await self._mock_engine.transcribe_chunk(chunk)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe_chunk_sync, chunk)

    def _transcribe_chunk_sync(self, chunk: AudioChunk) -> List[TranscriptSegment]:
        """Convert raw PCM bytes to WAV buffer and run faster-whisper."""
        if not self._model:
            return []

        # Convert raw PCM to in-memory WAV
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(chunk.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(chunk.sample_rate_hz)
            wf.writeframes(chunk.raw_data)
        wav_io.seek(0)

        segments, info = self._model.transcribe(
            wav_io,
            beam_size=3,
            language=self.language,
            initial_prompt="Indian banking, UPI PIN, OTP, transfer, account, urgent verification, KYC update",
            vad_filter=True,
        )

        results = []
        for s in segments:
            seg = TranscriptSegment(
                session_id=chunk.session_id,
                speaker=chunk.speaker,
                text=s.text.strip(),
                language=info.language or "en",
                start_time_sec=s.start,
                end_time_sec=s.end,
                confidence=math.exp(s.avg_logprob) if s.avg_logprob else 0.9,
                is_final=True,
            )
            results.append(seg)
        return results

    async def transcribe_file(
        self,
        file_path: str,
        session_id: str,
        speaker: SpeakerRole = SpeakerRole.CALLER
    ) -> List[TranscriptSegment]:
        if self._mock_engine is not None:
            return await self._mock_engine.transcribe_file(file_path, session_id, speaker)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._transcribe_file_sync, file_path, session_id, speaker
        )

    def _transcribe_file_sync(
        self, file_path: str, session_id: str, speaker: SpeakerRole
    ) -> List[TranscriptSegment]:
        if not self._model:
            return []
        segments, info = self._model.transcribe(file_path, beam_size=5, language=self.language)
        results = []
        for s in segments:
            results.append(
                TranscriptSegment(
                    session_id=session_id,
                    speaker=speaker,
                    text=s.text.strip(),
                    language=info.language or "en",
                    start_time_sec=s.start,
                    end_time_sec=s.end,
                    confidence=math.exp(s.avg_logprob) if s.avg_logprob else 0.9,
                    is_final=True,
                )
            )
        return results

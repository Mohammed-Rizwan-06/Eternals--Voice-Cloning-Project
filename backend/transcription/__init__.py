"""
VoxShield - Transcription Subsystem
Module Owner: Keerthi

Provides real-time streaming speech-to-text (STT) processing for incoming telephony
and VoIP calls. Ephemeral memory buffering complies with DPDP privacy mandates.
"""

from .base import (
    AudioChunk,
    AudioEncoding,
    BaseTranscriber,
    SpeakerRole,
    TranscriptSegment,
    TranscriptWord,
    TranscriptionSessionState,
)
from .streaming import AudioStreamBuffer, TranscriptAccumulator
from .whisper_engine import MockStreamingTranscriber, WhisperTranscriber
from .service import TranscriptionService

__all__ = [
    "AudioChunk",
    "AudioEncoding",
    "BaseTranscriber",
    "SpeakerRole",
    "TranscriptSegment",
    "TranscriptWord",
    "TranscriptionSessionState",
    "AudioStreamBuffer",
    "TranscriptAccumulator",
    "MockStreamingTranscriber",
    "WhisperTranscriber",
    "TranscriptionService",
]

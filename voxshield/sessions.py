from __future__ import annotations

import asyncio
import json
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from uuid import uuid4

from voxshield.adapters.unavailable import UnavailableAdapters
from voxshield.demo import SCENARIOS, fixture
from voxshield.risk import RiskEngine
from voxshield.schemas import (
    AuthenticityResult,
    CallerInformation,
    CallState,
    ConversationResult,
    ProtectionState,
    Reputation,
    ServiceState,
    ServiceStatus,
    SessionSnapshot,
    SSEEvent,
)
from voxshield.time import utc_now

SubscriberQueue = asyncio.Queue[SSEEvent | None]


@dataclass
class SessionRecord:
    snapshot: SessionSnapshot
    events: deque[SSEEvent]
    subscribers: set[SubscriberQueue] = field(default_factory=set)
    event_sequence: int = 0
    last_auth_sequence: int = -1
    last_conversation_sequence: int = -1


class SessionManager:
    def __init__(
        self,
        demo_mode: bool = False,
        queue_size: int = 64,
        history_size: int = 128,
        max_sessions: int = 256,
    ) -> None:
        self.demo_mode = demo_mode
        self.queue_size = queue_size
        self.history_size = history_size
        self.max_sessions = max_sessions
        self.records: OrderedDict[str, SessionRecord] = OrderedDict()
        self.risk = RiskEngine()
        self.adapters = UnavailableAdapters()

    async def create(self, scenario: str | None = None) -> SessionSnapshot:
        if scenario and not self.demo_mode:
            raise ValueError("Demo scenario requested while Demo Mode is disabled")

        self._make_session_capacity()
        session_id = str(uuid4())
        now = utc_now()
        if self.demo_mode:
            caller, authenticity, conversation = fixture(scenario or SCENARIOS[0], now)
            services = ServiceStatus(
                telephony=ServiceState.UNAVAILABLE,
                authenticity_detector=ServiceState.READY,
                transcription=ServiceState.READY,
                scam_intelligence=ServiceState.READY,
            )
        else:
            caller = CallerInformation(
                display_name="Unknown caller",
                masked_phone_number="***",
                reputation=Reputation.UNAVAILABLE,
            )
            authenticity = await self.adapters.authenticity.analyze(b"", 0)
            conversation = await self.adapters.transcription.transcribe(b"", 0)
            services = ServiceStatus()

        risk = self.risk.evaluate(caller, authenticity, conversation, 0)
        snapshot = SessionSnapshot(
            session_id=session_id,
            call_state=CallState.CREATED,
            protection_state=ProtectionState.DISABLED,
            caller=caller,
            authenticity=authenticity,
            conversation=conversation,
            risk=risk,
            service_status=services,
            created_at=now,
            updated_at=now,
            is_demo=self.demo_mode,
        )
        record = SessionRecord(
            snapshot=snapshot,
            events=deque(maxlen=self.history_size),
            last_auth_sequence=authenticity.sequence,
            last_conversation_sequence=conversation.sequence,
        )
        self.records[session_id] = record
        self._emit(record, "session_created", {"snapshot": snapshot.model_dump(mode="json")})
        if self.demo_mode:
            self._emit(record, "authenticity_updated", authenticity.model_dump(mode="json"))
            for signal in conversation.signals:
                self._emit(record, "scam_signal_detected", signal.model_dump(mode="json"))
            self._emit(record, "conversation_updated", conversation.model_dump(mode="json"))
            self._emit(record, "risk_updated", risk.model_dump(mode="json"))
        return snapshot

    def get(self, session_id: str) -> SessionSnapshot:
        try:
            return self.records[session_id].snapshot
        except KeyError:
            raise KeyError(session_id) from None

    def command(self, session_id: str, command: str) -> SessionSnapshot:
        try:
            record = self.records[session_id]
        except KeyError:
            raise KeyError(session_id) from None

        snapshot = record.snapshot
        now = utc_now()
        if command == "enable":
            snapshot = snapshot.model_copy(
                update={"protection_state": ProtectionState.ACTIVE, "updated_at": now}
            )
            event_type = "protection_enabled"
        elif command == "verify":
            event_type = "verification_requested"
        elif command == "stop-protection":
            snapshot = snapshot.model_copy(
                update={"protection_state": ProtectionState.STOPPED, "updated_at": now}
            )
            event_type = "protection_stopped"
        elif command == "report":
            event_type = "session_summary"
        elif command == "end":
            snapshot = snapshot.model_copy(
                update={"call_state": CallState.ENDING, "updated_at": now}
            )
            record.snapshot = snapshot
            self._emit(record, "call_ending", {})
            snapshot = snapshot.model_copy(
                update={
                    "call_state": CallState.ENDED,
                    "protection_state": ProtectionState.STOPPED,
                    "updated_at": utc_now(),
                }
            )
            event_type = "call_ended"
        else:
            raise ValueError("unknown command")

        record.snapshot = snapshot
        self._emit(record, event_type, {})
        if command == "end":
            self._close_subscribers(record)
        return snapshot

    def ingest_authenticity(self, session_id: str, result: AuthenticityResult) -> bool:
        record = self.records[session_id]
        self._validate_provenance(record, result.is_demo)
        if result.sequence <= record.last_auth_sequence:
            return False

        record.last_auth_sequence = result.sequence
        risk = self.risk.evaluate(
            record.snapshot.caller,
            result,
            record.snapshot.conversation,
            record.snapshot.risk.sequence + 1,
        )
        record.snapshot = record.snapshot.model_copy(
            update={"authenticity": result, "risk": risk, "updated_at": utc_now()}
        )
        self._emit(record, "authenticity_updated", result.model_dump(mode="json"))
        self._emit(record, "risk_updated", risk.model_dump(mode="json"))
        return True

    def ingest_conversation(self, session_id: str, result: ConversationResult) -> bool:
        record = self.records[session_id]
        self._validate_provenance(record, result.is_demo)
        if result.sequence <= record.last_conversation_sequence:
            return False

        record.last_conversation_sequence = result.sequence
        risk = self.risk.evaluate(
            record.snapshot.caller,
            record.snapshot.authenticity,
            result,
            record.snapshot.risk.sequence + 1,
        )
        record.snapshot = record.snapshot.model_copy(
            update={"conversation": result, "risk": risk, "updated_at": utc_now()}
        )
        self._emit(record, "conversation_updated", result.model_dump(mode="json"))
        self._emit(record, "risk_updated", risk.model_dump(mode="json"))
        return True

    def bind_call(self, session_id: str, call_id: str) -> None:
        record = self.records[session_id]
        record.snapshot = record.snapshot.model_copy(
            update={"call_id": call_id, "call_state": CallState.ACTIVE, "updated_at": utc_now()}
        )
        self._emit(record, "transport_started", {"call_id": call_id})

    def emit_transport(self, session_id: str, event_type: str, payload: dict) -> SSEEvent:
        return self._emit(self.records[session_id], event_type, payload)

    def subscribe(self, session_id: str) -> SubscriberQueue:
        record = self.records[session_id]
        queue: SubscriberQueue = asyncio.Queue(maxsize=self.queue_size)
        if record.snapshot.call_state == CallState.ENDED:
            queue.put_nowait(None)
        else:
            record.subscribers.add(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: SubscriberQueue) -> None:
        record = self.records.get(session_id)
        if record is not None:
            record.subscribers.discard(queue)

    def event_stream(self, session_id: str, queue: SubscriberQueue):
        async def generate():
            try:
                record = self.records.get(session_id)
                if record is not None:
                    for event in tuple(record.events):
                        yield self.format_sse(event)
                while True:
                    event = await queue.get()
                    if event is None:
                        break
                    yield self.format_sse(event)
            finally:
                self.unsubscribe(session_id, queue)

        return generate()

    def _emit(self, record: SessionRecord, event_type: str, payload: dict) -> SSEEvent:
        record.event_sequence += 1
        event = SSEEvent(
            session_id=record.snapshot.session_id,
            sequence=record.event_sequence,
            event_type=event_type,
            timestamp=utc_now(),
            payload=payload,
            is_demo=record.snapshot.is_demo,
        )
        record.events.append(event)
        for queue in tuple(record.subscribers):
            self._put_bounded(queue, event)
        return event

    def _close_subscribers(self, record: SessionRecord) -> None:
        for queue in tuple(record.subscribers):
            self._put_bounded(queue, None)
        record.subscribers.clear()

    @staticmethod
    def _put_bounded(queue: SubscriberQueue, item: SSEEvent | None) -> None:
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(item)

    @staticmethod
    def _validate_provenance(record: SessionRecord, is_demo: bool) -> None:
        if is_demo != record.snapshot.is_demo:
            raise ValueError("normal and demo data cannot be mixed")

    def _make_session_capacity(self) -> None:
        while len(self.records) >= self.max_sessions:
            ended_session = next(
                (
                    session_id
                    for session_id, record in self.records.items()
                    if record.snapshot.call_state == CallState.ENDED
                ),
                None,
            )
            session_id = ended_session or next(iter(self.records))
            record = self.records.pop(session_id)
            self._close_subscribers(record)

    @staticmethod
    def format_sse(event: SSEEvent) -> str:
        data = json.dumps(event.model_dump(mode="json"))
        return f"id: {event.sequence}\nevent: {event.event_type}\ndata: {data}\n\n"

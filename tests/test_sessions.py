import pytest

from voxshield.schemas import AnalysisStatus, AuthenticityResult, ConversationResult
from voxshield.sessions import SessionManager
from voxshield.time import utc_now


@pytest.mark.asyncio
async def test_stale_and_duplicate_sequence_ignored():
    manager = SessionManager()
    snap = await manager.create()

    def result(seq):
        return AuthenticityResult(
            status=AnalysisStatus.READY,
            human_probability=0.9,
            ai_probability=0.1,
            timestamp=utc_now(),
            sequence=seq,
        )

    assert manager.ingest_authenticity(snap.session_id, result(1)) is True
    assert manager.ingest_authenticity(snap.session_id, result(1)) is False
    assert manager.ingest_authenticity(snap.session_id, result(0)) is False


@pytest.mark.asyncio
async def test_stale_and_duplicate_conversation_sequence_ignored():
    manager = SessionManager()
    snap = await manager.create()

    def result(seq):
        return ConversationResult(status=AnalysisStatus.READY, timestamp=utc_now(), sequence=seq)

    assert manager.ingest_conversation(snap.session_id, result(1)) is True
    assert manager.ingest_conversation(snap.session_id, result(1)) is False
    assert manager.ingest_conversation(snap.session_id, result(0)) is False


@pytest.mark.asyncio
async def test_sse_event_ordering():
    manager = SessionManager(demo_mode=True)
    snap = await manager.create()
    manager.command(snap.session_id, "enable")
    manager.command(snap.session_id, "verify")
    events = list(manager.records[snap.session_id].events)
    assert [e.sequence for e in events] == list(range(1, len(events) + 1))


@pytest.mark.asyncio
async def test_bounded_subscriber_queue_drops_oldest():
    manager = SessionManager(demo_mode=True, queue_size=2)
    snap = await manager.create()
    q = manager.subscribe(snap.session_id)
    manager.command(snap.session_id, "enable")
    manager.command(snap.session_id, "verify")
    manager.command(snap.session_id, "report")
    assert q.qsize() == 2
    assert [q.get_nowait().event_type, q.get_nowait().event_type] == [
        "verification_requested",
        "session_summary",
    ]
    manager.unsubscribe(snap.session_id, q)
    assert not manager.records[snap.session_id].subscribers


@pytest.mark.asyncio
async def test_call_end_detaches_subscribers_after_terminal_event():
    manager = SessionManager(demo_mode=True, queue_size=3)
    snap = await manager.create()
    q = manager.subscribe(snap.session_id)
    manager.command(snap.session_id, "end")
    assert not manager.records[snap.session_id].subscribers
    assert q.get_nowait().event_type == "call_ending"
    assert q.get_nowait().event_type == "call_ended"
    assert q.get_nowait() is None


@pytest.mark.asyncio
async def test_event_history_is_bounded():
    manager = SessionManager(demo_mode=True, history_size=2)
    snap = await manager.create()
    manager.command(snap.session_id, "enable")
    manager.command(snap.session_id, "verify")
    assert len(manager.records[snap.session_id].events) == 2


@pytest.mark.asyncio
async def test_session_collection_is_bounded_and_prefers_ended_eviction():
    manager = SessionManager(max_sessions=2)
    first = await manager.create()
    second = await manager.create()
    manager.command(first.session_id, "end")
    third = await manager.create()
    assert len(manager.records) == 2
    assert first.session_id not in manager.records
    assert second.session_id in manager.records
    assert third.session_id in manager.records

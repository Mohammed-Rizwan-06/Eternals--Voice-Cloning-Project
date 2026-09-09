import pytest
from fastapi.testclient import TestClient

from voxshield.config import Settings
from voxshield.main import create_app


@pytest.fixture
def normal_client():
    with TestClient(create_app(Settings(demo_mode=False))) as client:
        yield client


@pytest.fixture
def demo_client():
    with TestClient(
        create_app(Settings(demo_mode=True, sse_queue_size=2, event_history_size=4))
    ) as client:
        yield client

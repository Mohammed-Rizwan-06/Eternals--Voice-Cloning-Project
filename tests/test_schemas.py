from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from voxshield.schemas import AnalysisStatus, AuthenticityResult
from voxshield.time import utc_now


def make(**overrides):
    values = dict(
        status=AnalysisStatus.READY,
        human_probability=0.4,
        ai_probability=0.6,
        timestamp=utc_now(),
        sequence=1,
    )
    values.update(overrides)
    return AuthenticityResult(**values)


@pytest.mark.parametrize("bad", [-0.1, 1.1, float("nan"), float("inf"), -float("inf")])
def test_invalid_nan_infinite_probability(bad):
    with pytest.raises(ValidationError):
        make(ai_probability=bad)


def test_inconsistent_probability_pair():
    with pytest.raises(ValidationError):
        make(human_probability=0.7, ai_probability=0.4)


def test_failure_state_cannot_fabricate_prediction():
    with pytest.raises(ValidationError):
        make(status=AnalysisStatus.UNAVAILABLE)


@pytest.mark.parametrize(
    "timestamp",
    [datetime.now(), datetime.now(timezone(timedelta(hours=5, minutes=30)))],
)
def test_timestamp_requires_timezone_aware_utc(timestamp):
    with pytest.raises(ValidationError):
        make(timestamp=timestamp)


def test_assignment_cannot_bypass_probability_validation():
    result = make()
    with pytest.raises(ValidationError):
        result.ai_probability = float("nan")

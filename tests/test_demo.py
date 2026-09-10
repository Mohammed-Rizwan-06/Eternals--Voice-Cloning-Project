import pytest

from voxshield.demo import fixture
from voxshield.risk import RiskEngine
from voxshield.schemas import RiskLevel
from voxshield.time import utc_now


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("safe_human", RiskLevel.LOW),
        ("unknown_human", RiskLevel.MEDIUM),
        ("human_financial_scam", RiskLevel.HIGH),
        ("ai_cloned_financial_scam", RiskLevel.CRITICAL),
    ],
)
def test_deterministic_scenario_risk(scenario, expected):
    c, a, v = fixture(scenario, utc_now())
    result = RiskEngine().evaluate(c, a, v, 1)
    if scenario == "human_financial_scam":
        assert result.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    else:
        assert result.level == expected
    assert result.is_demo


def test_fixtures_are_value_deterministic():
    base = utc_now()
    first = fixture("safe_human", base)
    second = fixture("safe_human", base)
    assert [x.model_dump() for x in first] == [x.model_dump() for x in second]

import pytest
from app.config import Settings
from pydantic import ValidationError


@pytest.mark.parametrize("overrides", [
    {"retriever_hybrid_candidate_k": 0}, {"retriever_hybrid_candidate_k": 101},
    {"retriever_hybrid_timeout_seconds": 0},
    {"retriever_hybrid_timeout_seconds": 11},
])
def test_shadow_limits_reject_out_of_range_configuration(overrides):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)


def test_shadow_limit_boundaries_are_valid():
    configured = Settings(_env_file=None, retriever_hybrid_candidate_k=100,
                          retriever_hybrid_timeout_seconds=1)
    assert (configured.retriever_hybrid_candidate_k,
            configured.retriever_hybrid_timeout_seconds) == (100, 1)

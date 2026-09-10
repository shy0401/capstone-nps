from types import SimpleNamespace
import pytest
from nps.config import Settings
from nps.artifacts import eligible


@pytest.mark.parametrize("environment", ["prod", "offline", "test"])
def test_review_bypass_rejected_outside_dev(environment):
    with pytest.raises(ValueError, match="only in dev"):
        Settings(environment=environment, review_mode="prototype-pass")


def test_prototype_output_never_official_even_with_later_approval():
    version = SimpleNamespace(
        qa_status="PASS",
        approval_status="APPROVED",
        provenance={"official_template": True, "mock": False, "review_mode": "prototype-pass"},
    )
    assert not eligible(version)

import pytest
from pydantic import ValidationError
from nps.config import Settings
from nps.contracts import SlidePlanContract


def test_insecure_production_rejected():
    with pytest.raises(ValidationError):
        Settings(environment="prod", scan_mode="mock", dev_insecure_cookie=True)


def test_contract_rejects_unstructured_plan():
    with pytest.raises(ValidationError):
        SlidePlanContract.model_validate({"text": "free form"})

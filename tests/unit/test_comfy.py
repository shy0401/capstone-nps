import base64
import io
from unittest.mock import patch, Mock
import pytest
from PIL import Image
from nps.comfy import MockComfyAdapter, RealComfyAdapter
from nps.contracts import VisualPlan
from nps.errors import DomainError


def test_mock_asset_real_png_and_metadata():
    result = MockComfyAdapter().generate(VisualPlan(mode="controlnet", controlnet="canny"))
    image = Image.open(io.BytesIO(base64.b64decode(result["image_base64"])))
    assert image.size == (960, 540)
    assert result["provenance"]["mock"]
    assert len(result["provenance"]["workflow_sha256"]) == 64


def test_real_mode_not_fake_success():
    with pytest.raises(DomainError, match="COMFY_WORKFLOW_NOT_CONFIGURED"):
        RealComfyAdapter().generate(VisualPlan(mode="generate"))


def test_real_comfy_protocol_contract():
    image = MockComfyAdapter().generate(VisualPlan(mode="generate"))
    prompt, history, view = Mock(), Mock(), Mock()
    prompt.json.return_value = {"prompt_id": "synthetic-prompt"}
    history.json.return_value = {
        "synthetic-prompt": {"outputs": {"1": {"images": [{"filename": "output.png"}]}}}
    }
    view.content = base64.b64decode(image["image_base64"])
    with (
        patch(
            "nps.comfy.workflow_metadata",
            return_value=(
                {"mode": "real", "graph": {"1": {"inputs": {"seed": 1}}}, "supported_modes": ["generate"]},
                {},
            ),
        ),
        patch("nps.comfy.local_url", return_value="http://comfyui-image:8188"),
        patch("httpx.Client") as client,
    ):
        transport = client.return_value.__enter__.return_value
        transport.post.return_value = prompt
        transport.get.side_effect = [history, view]
        assert RealComfyAdapter().generate(VisualPlan(mode="generate"))["provenance"]["mock"] is False
        assert transport.post.call_args.kwargs["json"]["prompt"]["1"]["inputs"]["seed"] == 42

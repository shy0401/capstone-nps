import json
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/api"))
from nps.main import app  # noqa: E402
from nps.contracts import NormalizedDocument, SemanticChunk, SlidePlanContract, VisualPlan  # noqa: E402


def export():
    directory = ROOT / "packages/contracts"
    directory.mkdir(parents=True, exist_ok=True)
    for model, name in [
        (NormalizedDocument, "document"),
        (SemanticChunk, "chunk"),
        (SlidePlanContract, "slide-plan"),
        (VisualPlan, "visual-plan"),
    ]:
        (directory / (name + ".schema.json")).write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    (ROOT / "openapi").mkdir(exist_ok=True)
    (ROOT / "openapi/openapi.yaml").write_text(
        yaml.safe_dump(app.openapi(), allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


if __name__ == "__main__":
    export()

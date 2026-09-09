import secrets
from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse
from nps.config import settings
from nps.contracts import Contract
from nps.errors import DomainError
from nps.llm import backend
from nps.contracts import VisualPlan

llm_app = FastAPI(title="Internal LLM Adapter", version="1.0")
comfy_app = FastAPI(title="Internal Comfy Adapter", version="1.0")


def internal_auth(x_adapter_key: str = Header(default="")):
    if len(settings().adapter_secret) < 32 or not secrets.compare_digest(
        x_adapter_key, settings().adapter_secret
    ):
        raise DomainError("ADAPTER_AUTH_REQUIRED", 401)


async def handler(request, exc):
    return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code}})


for application in (llm_app, comfy_app):
    application.add_exception_handler(DomainError, handler)


@llm_app.get("/health")
def llm_health():
    return {"status": "alive", "mode": settings().llm_mode}


@comfy_app.get("/health")
def comfy_health():
    return {"status": "alive", "mode": settings().comfy_mode}


class GenerateInput(Contract):
    task: str
    payload: dict


@llm_app.post("/generate", dependencies=[Depends(internal_auth)])
def generate(data: GenerateInput):
    if data.task not in {"document_summary", "key_messages", "slide_outline", "slide_plan", "visual_plan"}:
        raise DomainError("LLM_TASK_UNSUPPORTED")
    return backend().generate(data.task, data.payload)


@comfy_app.post("/generate", dependencies=[Depends(internal_auth)])
def generate_visual(data: VisualPlan):
    from nps.comfy import MockComfyAdapter, RealComfyAdapter

    adapter = MockComfyAdapter() if settings().comfy_mode == "mock" else RealComfyAdapter()
    return adapter.generate(data)

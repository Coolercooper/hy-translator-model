import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import List, Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from llama_cpp import Llama
from pydantic import BaseModel, Field, model_validator

MODEL_FILE = os.getenv("MODEL_FILE", "/models/HY-MT1.5-1.8B-Q4_K_M.gguf")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
LLAMA_THREADS = int(os.getenv("LLAMA_THREADS", "4"))
LLAMA_CTX_SIZE = int(os.getenv("LLAMA_CTX_SIZE", "2048"))
LLAMA_PARALLEL = int(os.getenv("LLAMA_PARALLEL", "1"))
LLAMA_BACKEND = os.getenv("LLAMA_BACKEND", "cpu").strip().lower()
LLAMA_MAIN_GPU = int(os.getenv("LLAMA_MAIN_GPU", "0"))


def resolve_gpu_layers() -> int:
    configured = os.getenv("LLAMA_N_GPU_LAYERS")
    if configured is not None and configured.strip():
        return int(configured)
    if LLAMA_BACKEND in {"metal", "auto"} and sys.platform == "darwin":
        return -1
    return 0


LLAMA_N_GPU_LAYERS = resolve_gpu_layers()

MODEL: dict = {}
INFER_LOCK = Lock()


def validate_api_key(x_api_key: Optional[str], api_key: Optional[str], authorization: Optional[str]) -> None:
    expected_key = (os.getenv("APIKEY", "QWERTYUIOP") or "").strip()
    if not expected_key:
        return

    provided_key = (x_api_key or api_key or "").strip()
    if not provided_key and authorization:
        auth = authorization.strip()
        provided_key = auth[7:].strip() if auth.lower().startswith("bearer ") else auth

    if provided_key != expected_key:
        raise HTTPException(status_code=401, detail="无效的APIKEY")


def load_model():
    if not Path(MODEL_FILE).exists():
        raise RuntimeError(f"GGUF 模型文件不存在: {MODEL_FILE}")
    llama_options = dict(
        model_path=MODEL_FILE,
        n_ctx=LLAMA_CTX_SIZE,
        n_threads=LLAMA_THREADS,
        n_threads_batch=LLAMA_THREADS,
        n_batch=512,
        flash_attn=True,
    )

    if LLAMA_N_GPU_LAYERS != 0:
        llama_options["n_gpu_layers"] = LLAMA_N_GPU_LAYERS
        llama_options["main_gpu"] = LLAMA_MAIN_GPU

    MODEL["llm"] = Llama(**llama_options)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield
    MODEL.clear()


app = FastAPI(title="HY-MT1.5-1.8B GGUF FastAPI", version="2.0.0", lifespan=lifespan)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class TranslateRequest(BaseModel):
    text: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    model: Optional[str] = None
    max_new_tokens: Optional[int] = Field(default=None)
    temperature: Optional[float] = Field(default=0.2)

    @model_validator(mode="after")
    def validate_input(self):
        if not (self.text and self.text.strip()) and not self.messages:
            raise ValueError("`text` 和 `messages` 至少提供一个")
        return self


def build_messages(req: TranslateRequest) -> List[dict]:
    if req.messages:
        return [{"role": m.role, "content": m.content} for m in req.messages if m.content and m.content.strip()]
    return [{"role": "user", "content": req.text.strip()}]


def infer(req: TranslateRequest) -> str:
    llm: Llama = MODEL["llm"]
    messages = build_messages(req)
    max_tokens = min(req.max_new_tokens or MAX_NEW_TOKENS, MAX_NEW_TOKENS)
    with INFER_LOCK:
        result = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=req.temperature if req.temperature is not None else 0.2,
        )
    # result = llm.create_chat_completion(
    #     messages=messages,
    #     max_tokens=max_tokens,
    #     temperature=req.temperature if req.temperature is not None else 0.2,
    # )
    return result["choices"][0]["message"]["content"]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": "llm" in MODEL,
        "model_file": MODEL_FILE,
        "parallel": LLAMA_PARALLEL,
        "backend": LLAMA_BACKEND,
        "gpu_layers": LLAMA_N_GPU_LAYERS,
    }


@app.post("/translate")
def translate(
    req: TranslateRequest,
    x_api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    api_key: Optional[str] = Header(default=None, alias="api-key"),
    authorization: Optional[str] = Header(default=None),
):
    validate_api_key(x_api_key, api_key, authorization)
    try:
        return {"translation": infer(req)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@app.post("/v1/chat/completions")
def chat_completions(
    req: TranslateRequest,
    x_api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    api_key: Optional[str] = Header(default=None, alias="api-key"),
    authorization: Optional[str] = Header(default=None),
):
    validate_api_key(x_api_key, api_key, authorization)
    try:
        content = infer(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")
    return {
        "id": f"chatcmpl-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or "HY-MT1.5-1.8B-Q4_K_M",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }

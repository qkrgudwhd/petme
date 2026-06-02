from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import emotions, generate, settings as settings_router, upload
from .services import secrets as secrets_service

app = FastAPI(title="PetMe-Moji API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# storage 디렉터리를 정적 파일로 노출 (미리보기 표시용)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/files/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")
app.mount("/files/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")

app.include_router(upload.router)
app.include_router(emotions.router)
app.include_router(generate.router)
app.include_router(settings_router.router)


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "gemini_key_set": secrets_service.is_configured()
        or (
            bool(settings.gemini_api_key)
            and not settings.gemini_api_key.startswith("your_")
        ),
        "model": settings.gemini_image_model,
    }

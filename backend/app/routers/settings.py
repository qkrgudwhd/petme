"""API 키 등록/조회/삭제 (암호화 저장)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services import secrets

router = APIRouter(prefix="/api/settings", tags=["settings"])


class KeyIn(BaseModel):
    api_key: str = Field(..., min_length=10, max_length=512)


@router.get("/key")
def get_key_status():
    key = secrets.load_api_key()
    return {
        "configured": key is not None,
        "masked": secrets.mask(key or ""),
    }


@router.post("/key")
def set_key(body: KeyIn):
    try:
        secrets.save_api_key(body.api_key)
    except ValueError as e:
        raise HTTPException(400, str(e))
    # 응답에는 마스킹된 값만
    return {"configured": True, "masked": secrets.mask(body.api_key)}


@router.delete("/key")
def delete_key():
    removed = secrets.delete_api_key()
    return {"removed": removed, "configured": False}


@router.post("/key/verify")
def verify_key():
    """저장된 키가 실제로 Gemini 호출에 유효한지 검증 (가벼운 요청 1회)."""
    try:
        api_key = secrets.get_api_key_required()
    except RuntimeError as e:
        raise HTTPException(400, str(e))

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        # 모델 목록 조회 = 텍스트/이미지 생성 없이 인증만 검증
        _ = list(client.models.list())
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, f"키 검증 실패: {type(e).__name__}: {e}")

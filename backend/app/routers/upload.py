"""사진 업로드 → 누끼 → 360x360 미리보기 PNG 생성 + 종(species) 메타 저장."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..config import settings
from ..prompts.emotions import DEFAULT_PET_TYPE, PET_TYPES, SPECIES_DESCRIPTOR
from ..services.images import fit_square, remove_background, save_png_optimized
from ..services.label_generator import generate_dynamic_labels
from ..services.species_detect import DETECT_SENTINEL, detect_pet_type
from ..services.subject_analyzer import analyze_subjects

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _read_pet_type(session_dir: Path) -> str:
    """세션의 meta.json에서 pet_type을 읽음. 없으면 디폴트."""
    meta_path = session_dir / "meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text("utf-8")).get("pet_type", DEFAULT_PET_TYPE)
        except Exception:
            pass
    return DEFAULT_PET_TYPE


def _read_dynamic_labels(session_dir: Path) -> dict:
    meta_path = session_dir / "meta.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text("utf-8")).get("dynamic_labels", {}) or {}
        except Exception:
            pass
    return {}


@router.post("/{session_id}/pet-type")
def update_pet_type(session_id: str, pet_type: str = Form(...)):
    """사용자가 자동 감지 결과를 수동으로 override 할 때 사용."""
    sess = settings.upload_dir / session_id
    if not sess.exists():
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    if pet_type not in PET_TYPES:
        raise HTTPException(400, f"지원하지 않는 종: {pet_type}")
    meta_path = sess / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text("utf-8"))
        except Exception:
            meta = {}
    meta["pet_type"] = pet_type
    meta["auto_detected"] = False  # 사용자가 수동 설정
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return {"pet_type": pet_type}


@router.get("/{session_id}")
def get_upload(session_id: str):
    sess = settings.upload_dir / session_id
    if not sess.exists():
        raise HTTPException(404, "세션을 찾을 수 없습니다.")
    items: dict = {}
    for label in ("person", "pet"):
        preview = sess / f"{label}_preview.png"
        if not preview.exists():
            raise HTTPException(404, f"{label} 미리보기 없음")
        items[label] = {
            "preview_url": f"/files/uploads/{session_id}/{preview.name}",
            "bytes": preview.stat().st_size,
        }
    return {
        "session_id": session_id,
        "items": items,
        "pet_type": _read_pet_type(sess),
        "dynamic_labels": _read_dynamic_labels(sess),
    }


@router.post("")
async def upload(
    person: UploadFile = File(...),
    pet: UploadFile = File(...),
    pet_type: str = Form(DETECT_SENTINEL),
):
    """인물 + 반려동물 2장 업로드. pet_type='auto'면 자동 감지."""
    for f in (person, pet):
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, f"지원하지 않는 파일 형식: {f.content_type}")

    auto_detect = pet_type == DETECT_SENTINEL
    if not auto_detect and pet_type not in PET_TYPES:
        pet_type = DEFAULT_PET_TYPE

    max_bytes = settings.max_upload_mb * 1024 * 1024
    session_id = uuid.uuid4().hex[:12]
    sess_dir: Path = settings.upload_dir / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {"session_id": session_id, "items": {}, "auto_detected": False, "confidence": 0.0}
    for label, f in (("person", person), ("pet", pet)):
        data = await f.read()
        if len(data) > max_bytes:
            raise HTTPException(413, f"{label} 파일이 {settings.max_upload_mb}MB를 초과합니다.")
        original_path = sess_dir / f"{label}_original{Path(f.filename or '').suffix.lower() or '.png'}"
        original_path.write_bytes(data)

        cut = remove_background(data)
        preview = fit_square(cut, 360)
        preview_path = sess_dir / f"{label}_preview.png"
        size = save_png_optimized(preview, preview_path)

        result["items"][label] = {
            "preview_url": f"/files/uploads/{session_id}/{preview_path.name}",
            "bytes": size,
        }

    # 업로드 자체는 누끼/리사이즈까지만 빠르게 끝낸다 (~3초)
    # 종 감지·라벨 생성 같은 무거운 Gemini 호출은 별도 /analyze 엔드포인트에서.
    (sess_dir / "meta.json").write_text(
        json.dumps({
            "pet_type": pet_type,
            "auto_detected": auto_detect,
            "analyze_pending": auto_detect,  # auto면 분석 필요
            "dynamic_labels": {},
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    result["pet_type"] = pet_type
    result["analyze_pending"] = auto_detect  # 프론트가 이걸 보고 분석 호출
    return result


@router.post("/{session_id}/analyze")
def analyze_session(session_id: str):
    """세션의 두 이미지를 1회 분석 (Gemini Vision 1 call, 5~8s):
    - 종 자동 감지
    - 인물/피사체 상세 외모 설명 (32장 일관성 확보용)
    - 32 동적 라벨
    """
    sess = settings.upload_dir / session_id
    person_preview = sess / "person_preview.png"
    pet_preview = sess / "pet_preview.png"
    if not (person_preview.exists() and pet_preview.exists()):
        raise HTTPException(404, "세션을 찾을 수 없습니다.")

    meta_path = sess / "meta.json"
    meta: dict = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text("utf-8"))
        except Exception:
            meta = {}

    # 통합 분석 호출
    a = analyze_subjects(person_preview, pet_preview)

    auto_detected = meta.get("auto_detected", True) and bool(a["pet_type"])
    if auto_detected and a["pet_type"] in PET_TYPES:
        pet_type = a["pet_type"]
    else:
        pet_type = meta.get("pet_type", DEFAULT_PET_TYPE)

    meta.update({
        "pet_type": pet_type,
        "auto_detected": auto_detected,
        "person_description": a["person_description"],
        "pet_description": a["pet_description"],
        "dynamic_labels": a["labels"],
        "analyze_pending": False,
    })
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    return {
        "pet_type": pet_type,
        "auto_detected": auto_detected,
        "confidence": a["confidence"],
        "person_description": a["person_description"],
        "pet_description": a["pet_description"],
        "dynamic_labels": a["labels"],
    }

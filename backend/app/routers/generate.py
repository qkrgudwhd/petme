"""이모티콘 생성: 단일 + 32종 일괄(SSE) + 개별 재생성."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import json

from ..config import settings
from ..prompts.emotions import ALL_EMOTIONS, DEFAULT_PET_TYPE, Emotion
from ..services.gemini import generate_emoticon, normalize_to_emoticon
from ..services.images import extract_palette, make_icon, save_png_optimized
from ..services.packaging import build_zip
from ..services.rate_limit import (
    approve_paid_budget,
    get_usage_today,
    reset_monthly_budget,
)

# 아이콘 소스로 우선 선택할 감정 키 (있는 것 중 첫 번째 사용)
ICON_PREFERRED_KEYS = ("hello", "love", "thanks", "congrats", "laugh", "ok")

router = APIRouter(prefix="/api/generate", tags=["generate"])


@router.get("/usage")
def get_usage():
    """일일/월간 사용량 + 동의된 한도."""
    return get_usage_today()


class ApprovalRequest(BaseModel):
    krw: int


@router.post("/approve-paid")
def approve_paid(req: ApprovalRequest):
    """사용자가 모달에서 추가 비용 동의 → 월 한도 증액."""
    try:
        m = approve_paid_budget(req.krw)
        return {"approved_cap_krw": m["approved_cap_krw"], "spent_krw": m["spent_krw"]}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/revoke-paid")
def revoke_paid():
    """사용자가 추가 비용 더 안 쓴다고 동의 회수."""
    m = reset_monthly_budget()
    return {"approved_cap_krw": m["approved_cap_krw"], "spent_krw": m["spent_krw"]}

# 무료 티어(분당 10 RPM, 일 100장) 안에서만 동작하도록 동시성 1.
# 실제 속도 제어는 services/rate_limit.py가 호출 직전에 sleep 7초.
# 32장 = 약 4분, 비용 0원.
CONCURRENCY = 1


def _reference_paths(session_id: str) -> list[str]:
    sess = settings.upload_dir / session_id
    person = sess / "person_preview.png"
    pet = sess / "pet_preview.png"
    if not person.exists() or not pet.exists():
        raise HTTPException(404, "업로드 세션을 찾을 수 없습니다. 다시 업로드 해주세요.")
    return [str(person), str(pet)]


# 세션 색상 팔레트 캐시: 한 번 추출하면 32회 모두 재사용
_palette_cache: dict[str, tuple[list[str], list[str]]] = {}


def _palettes_for_session(session_id: str) -> tuple[list[str], list[str]]:
    if session_id in _palette_cache:
        return _palette_cache[session_id]
    sess = settings.upload_dir / session_id
    person_pal = extract_palette(sess / "person_preview.png", n_colors=5)
    pet_pal = extract_palette(sess / "pet_preview.png", n_colors=5)
    _palette_cache[session_id] = (person_pal, pet_pal)
    return person_pal, pet_pal


def _build_icon(out_dir: Path, items: list[dict]) -> dict | None:
    """완성된 32 PNG 중 적절한 것을 골라 78x78 키보드 아이콘 생성."""
    if not items:
        return None
    done_keys = {it["key"] for it in items}
    # 선호 키 중 실제 생성된 것 찾기 → 없으면 첫 항목으로 폴백
    src_key = next((k for k in ICON_PREFERRED_KEYS if k in done_keys), items[0]["key"])
    src_path = out_dir / f"{src_key}.png"
    if not src_path.exists():
        return None
    icon_path = out_dir / "icon.png"
    try:
        bytes_written = make_icon(src_path, icon_path)
    except Exception:
        return None
    return {
        "source_key": src_key,
        "url": f"/files/outputs/{out_dir.name}/{icon_path.name}",
        "bytes": bytes_written,
        "size": 78,
    }


def _read_session_pet_type(session_id: str) -> str:
    meta = settings.upload_dir / session_id / "meta.json"
    if meta.exists():
        try:
            return json.loads(meta.read_text("utf-8")).get("pet_type", DEFAULT_PET_TYPE)
        except Exception:
            pass
    return DEFAULT_PET_TYPE


def _read_session_labels(session_id: str) -> dict[str, str]:
    """세션의 dynamic_labels 반환. 비었으면 {}."""
    meta = settings.upload_dir / session_id / "meta.json"
    if meta.exists():
        try:
            return json.loads(meta.read_text("utf-8")).get("dynamic_labels", {}) or {}
        except Exception:
            pass
    return {}


def _read_session_descriptions(session_id: str) -> tuple[str, str]:
    """세션의 person/pet 상세 설명. 비어 있으면 종 기반 폴백 생성."""
    from ..prompts.emotions import SPECIES_DESCRIPTOR, DEFAULT_PET_TYPE
    person, pet = "", ""
    pet_type = DEFAULT_PET_TYPE
    meta = settings.upload_dir / session_id / "meta.json"
    if meta.exists():
        try:
            d = json.loads(meta.read_text("utf-8"))
            person = d.get("person_description", "") or ""
            pet = d.get("pet_description", "") or ""
            pet_type = d.get("pet_type", DEFAULT_PET_TYPE)
        except Exception:
            pass
    # 폴백: 분석 실패 시에도 일관성 블록이 생기도록
    if not pet:
        species = SPECIES_DESCRIPTOR.get(pet_type, SPECIES_DESCRIPTOR[DEFAULT_PET_TYPE])
        pet = f"{species} exactly as shown in the reference image (same species, breed, color, pattern)"
    if not person:
        person = "the same person as shown in the reference image (same face, hair, glasses, clothing)"
    return person, pet


def _find_emotion(key: str) -> Emotion:
    for e in ALL_EMOTIONS:
        if e.key == key:
            return e
    raise HTTPException(404, f"감정 키를 찾을 수 없음: {key}")


def _generate_one(
    refs: list[str], emo: Emotion, style: str, out_dir: Path,
    pet_type: str,
    person_palette: list[str], pet_palette: list[str],
    session_labels: dict[str, str] | None = None,
    person_description: str = "",
    pet_description: str = "",
) -> dict:
    # 종에 맞는 라벨/프롬프트로 변환
    label_ko, prompt = emo.resolve(pet_type)
    if session_labels and emo.key in session_labels:
        label_ko = session_labels[emo.key]
    raw = generate_emoticon(
        reference_paths=refs,
        emotion_prompt=prompt,
        label_ko=label_ko,
        style_key=style,
        pet_type=pet_type,
        person_palette=person_palette,
        pet_palette=pet_palette,
        person_description=person_description,
        pet_description=pet_description,
    )
    img = normalize_to_emoticon(raw, label_ko=label_ko)
    out_path = out_dir / f"{emo.key}.png"
    bytes_written = save_png_optimized(img, out_path)
    return {
        "key": emo.key,
        "label_ko": label_ko,
        "url": f"/files/outputs/{out_dir.name}/{out_path.name}",
        "bytes": bytes_written,
    }


# --- 단일 생성 (Stage 2 검증용) ---
class SingleRequest(BaseModel):
    session_id: str
    emotion_key: str
    style: str = "cartoon2d"


@router.post("/single")
async def generate_single(req: SingleRequest):
    refs = _reference_paths(req.session_id)
    pet_type = _read_session_pet_type(req.session_id)
    person_pal, pet_pal = _palettes_for_session(req.session_id)
    session_labels = _read_session_labels(req.session_id)
    person_desc, pet_desc = _read_session_descriptions(req.session_id)
    emo = _find_emotion(req.emotion_key)
    out_dir = settings.output_dir / req.session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        item = await asyncio.to_thread(
            _generate_one, refs, emo, req.style, out_dir, pet_type, person_pal, pet_pal,
            session_labels, person_desc, pet_desc,
        )
    except Exception as e:
        raise HTTPException(500, f"생성 실패: {e}")
    return item


# --- 32종 일괄 + SSE 진행률 ---
@router.get("/batch")
async def generate_batch(
    session_id: str = Query(...),
    style: str = Query("cartoon2d"),
):
    """Server-Sent Events 스트림.
    이벤트: start / progress / item / done / error
    """
    refs = _reference_paths(session_id)
    pet_type = _read_session_pet_type(session_id)
    person_pal, pet_pal = _palettes_for_session(session_id)
    session_labels = _read_session_labels(session_id)
    person_desc, pet_desc = _read_session_descriptions(session_id)
    out_dir = settings.output_dir / session_id
    out_dir.mkdir(parents=True, exist_ok=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    queue: asyncio.Queue = asyncio.Queue()

    async def worker(emo: Emotion):
        async with sem:
            # 워커 슬롯 확보 직후: "시작" 이벤트. 라벨은 종에 맞게 변환된 것.
            label_ko, _ = emo.resolve(pet_type)
            if emo.key in session_labels:
                label_ko = session_labels[emo.key]
            await queue.put(("item_start", {"key": emo.key, "label_ko": label_ko}))
            t0 = time.monotonic()
            try:
                item = await asyncio.to_thread(
                    _generate_one, refs, emo, style, out_dir, pet_type, person_pal, pet_pal,
                    session_labels, person_desc, pet_desc,
                )
                item["ms"] = int((time.monotonic() - t0) * 1000)
                await queue.put(("item", item))
            except Exception as e:
                await queue.put(("error", {"key": emo.key, "message": str(e)}))

    async def runner():
        tasks = [asyncio.create_task(worker(e)) for e in ALL_EMOTIONS]
        await asyncio.gather(*tasks, return_exceptions=True)
        await queue.put(("__end__", None))

    async def event_stream():
        total = len(ALL_EMOTIONS)
        yield _sse("start", {
            "total": total, "style": style, "concurrency": CONCURRENCY,
            "person_palette": person_pal, "pet_palette": pet_pal,
        })
        runner_task = asyncio.create_task(runner())
        done_count = 0
        items: list[dict] = []
        errors: list[dict] = []
        try:
            while True:
                kind, payload = await queue.get()
                if kind == "__end__":
                    break
                if kind == "item_start":
                    # 처리 시작 알림 — 프론트가 "현재 처리 중"으로 표시
                    yield _sse("item_start", payload)
                elif kind == "item":
                    done_count += 1
                    items.append(payload)
                    yield _sse("item", payload)
                    yield _sse("progress", {"done": done_count, "total": total,
                                           "percent": round(done_count / total * 100, 1)})
                elif kind == "error":
                    done_count += 1
                    errors.append(payload)
                    yield _sse("error", payload)
                    yield _sse("progress", {"done": done_count, "total": total,
                                           "percent": round(done_count / total * 100, 1)})
            # 32장 완료 후 키보드 메인 아이콘 자동 생성 (78x78, 16KB 이하)
            icon_info = _build_icon(out_dir, items)
            if icon_info:
                yield _sse("icon", icon_info)

            zip_path = build_zip(
                out_dir,
                manifest={
                    "session_id": session_id,
                    "style": style,
                    "items": items,
                    "errors": errors,
                    "icon": icon_info,
                },
            )
            yield _sse("done", {
                "zip_url": f"/files/outputs/{session_id}/{zip_path.name}",
                "icon": icon_info,
            })
        finally:
            runner_task.cancel()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# --- 개별 재생성 ---
class RegenerateRequest(BaseModel):
    session_id: str
    emotion_key: str
    style: str = "cartoon2d"


class IconRequest(BaseModel):
    session_id: str
    source_key: str  # 어떤 이모티콘을 아이콘 소스로 쓸지


@router.post("/icon")
async def set_icon(req: IconRequest):
    """사용자가 32종 중 원하는 이모티콘을 키보드 아이콘으로 지정."""
    out_dir = settings.output_dir / req.session_id
    src_path = out_dir / f"{req.source_key}.png"
    if not src_path.exists():
        raise HTTPException(404, f"{req.source_key} 이모티콘이 없습니다.")
    icon_path = out_dir / "icon.png"
    try:
        bytes_written = await asyncio.to_thread(make_icon, src_path, icon_path)
    except Exception as e:
        raise HTTPException(500, f"아이콘 생성 실패: {e}")

    # ZIP을 다시 패키징해 새 아이콘 반영
    icon_info = {
        "source_key": req.source_key,
        "url": f"/files/outputs/{req.session_id}/icon.png",
        "bytes": bytes_written,
        "size": 78,
    }
    return icon_info


@router.post("/regenerate")
async def regenerate_one(req: RegenerateRequest):
    refs = _reference_paths(req.session_id)
    pet_type = _read_session_pet_type(req.session_id)
    person_pal, pet_pal = _palettes_for_session(req.session_id)
    session_labels = _read_session_labels(req.session_id)
    person_desc, pet_desc = _read_session_descriptions(req.session_id)
    emo = _find_emotion(req.emotion_key)
    out_dir = settings.output_dir / req.session_id
    try:
        item = await asyncio.to_thread(
            _generate_one, refs, emo, req.style, out_dir, pet_type, person_pal, pet_pal,
            session_labels, person_desc, pet_desc,
        )
    except Exception as e:
        raise HTTPException(500, f"재생성 실패: {e}")
    return item

"""업로드 후 분석 1회 호출로 모든 정보 추출:
- 인물 상세 외모 설명 (consistency용)
- 피사체 상세 외모 설명 (consistency용)
- 피사체 종 분류 (pet_type)
- 32 동적 라벨

Gemini Vision 한 번에 두 이미지 + JSON 응답으로 끝낸다 (이전 2~3회 호출 → 1회).
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from ..prompts.emotions import ALL_EMOTIONS, DEFAULT_PET_TYPE, PET_TYPES
from . import secrets

MODEL = "gemini-2.5-flash"


def _build_prompt() -> str:
    valid_types = "/".join(PET_TYPES)
    emotion_lines = "\n".join(
        f'  "{e.key}": (default "{e.label_ko}", meaning: {e.prompt[:50]})'
        for e in ALL_EMOTIONS
    )
    return (
        "You will analyze two reference images for a sticker pack project.\n"
        "Image 1 = the person. Image 2 = the second subject (animal/plant/toy/object/etc).\n\n"
        "Return a SINGLE JSON object with these exact keys:\n"
        "1) `pet_type`: classify the second subject as ONE of these EXACT words:\n"
        f"   {valid_types}\n"
        "   Use 'monkey' for monkeys/apes/primates. Use 'other' if unsure.\n"
        "2) `confidence`: float 0.0~1.0 — your certainty for pet_type\n"
        "3) `person_description`: a SHORT specific visual description of the person "
        "(8~20 words). Include: gender hint, hair color/style, glasses?, "
        "clothing color/type, distinguishing features. "
        'Example: "Asian man, short black hair, round glasses, navy suit, white shirt, friendly face"\n'
        "4) `pet_description`: a SHORT specific visual description of the second subject "
        "(8~20 words). Include: species/type, color, pattern, distinguishing features. "
        "Be specific enough that anyone reading it could draw the same subject. "
        'Example for a monkey: "small brown capuchin monkey, lighter cream face and chest, "'
        '"long curly tail, expressive dark eyes"\n'
        "5) `labels`: an object with all 32 keys below, mapped to NEW short Korean captions "
        "(1~8 한글, playful, tailored to THIS specific subject — reference its sound/shape/trait):\n"
        f"{emotion_lines}\n\n"
        "Output: pure JSON, no markdown, no code fences, no explanation. Start with `{`."
    )


def analyze_subjects(person_path: Path | str, pet_path: Path | str) -> dict:
    """두 이미지를 분석. 실패 시 안전한 기본값으로 채운 dict 반환."""
    fallback = {
        "pet_type": DEFAULT_PET_TYPE,
        "confidence": 0.0,
        "person_description": "",
        "pet_description": "",
        "labels": {},
    }

    try:
        api_key = secrets.get_api_key_required()
    except Exception:
        return fallback

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        img1 = Image.open(person_path).convert("RGB")
        img2 = Image.open(pet_path).convert("RGB")
        img1.thumbnail((512, 512), Image.LANCZOS)
        img2.thumbnail((512, 512), Image.LANCZOS)
        response = client.models.generate_content(
            model=MODEL,
            contents=[_build_prompt(), img1, img2],
        )
        text = (response.text or "").strip()
    except Exception:
        return fallback

    # 코드 펜스 제거
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.lstrip("\n")
    if text.endswith("```"):
        text = text[:-3].rstrip()

    try:
        data = json.loads(text)
    except Exception:
        return fallback

    result = dict(fallback)
    pet_type = str(data.get("pet_type", "")).lower().strip()
    if pet_type in PET_TYPES:
        result["pet_type"] = pet_type
    try:
        result["confidence"] = float(data.get("confidence", 0.0))
    except Exception:
        pass
    result["person_description"] = str(data.get("person_description", ""))[:300]
    result["pet_description"] = str(data.get("pet_description", ""))[:300]

    valid_keys = {e.key for e in ALL_EMOTIONS}
    labels = data.get("labels", {}) or {}
    cleaned: dict[str, str] = {}
    for k, v in labels.items():
        if k in valid_keys and isinstance(v, str):
            label = v.strip()
            if 0 < len(label) <= 20:
                cleaned[k] = label
    result["labels"] = cleaned
    return result

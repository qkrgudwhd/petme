"""반려동물 종(species) 자동 감지 — Gemini Vision 1회 호출 분류기.

업로드 직후 펫 누끼 이미지를 Gemini에 보내 dog/cat/rabbit/hamster/bird/other
중 하나로 분류한다. 호출 1회당 ~1초, 약 $0.001.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from ..prompts.emotions import DEFAULT_PET_TYPE, PET_TYPES
from . import secrets

DETECTION_MODEL = "gemini-2.5-flash"  # 텍스트 위주, 이미지 입력 가능, 빠르고 저렴
DETECT_SENTINEL = "auto"  # 프론트가 자동감지를 요청할 때 보내는 값

_PROMPT = (
    "Identify the most prominent subject in this image.\n"
    "Respond with EXACTLY ONE WORD from this list, lowercase, no punctuation, "
    "no explanation:\n"
    "  dog, cat, rabbit, hamster, bird, plant, toy, object, food, character, other\n"
    "Rules:\n"
    "- 'dog' = any dog breed (poodle, retriever, dachshund, mixed, etc.)\n"
    "- 'cat' = any cat\n"
    "- 'rabbit' = rabbit/bunny\n"
    "- 'hamster' = hamster, guinea pig, gerbil, or similar small rodent\n"
    "- 'bird' = any bird (parrot, canary, parakeet, etc.)\n"
    "- 'plant' = potted plant, flower, succulent, tree, etc.\n"
    "- 'toy' = stuffed animal, doll, plush, action figure (non-character)\n"
    "- 'object' = inanimate object (mug, bag, car, phone, book, etc.)\n"
    "- 'food' = food item, dish, fruit, snack, drink\n"
    "- 'character' = known character, mascot, anime/cartoon figure\n"
    "- 'other' = anything that doesn't fit above, or unclear\n"
    "Output: one word only."
)


def detect_pet_type(image_path: str | Path) -> tuple[str, float]:
    """이미지에서 종 감지. (종_키, 확신도 0~1) 반환. 실패 시 (default, 0.0).

    확신도는 단순 휴리스틱: 응답에 키워드가 정확히 단독으로 들어있으면 1.0,
    다른 단어와 섞여 있으면 0.6.
    """
    try:
        api_key = secrets.get_api_key_required()
    except Exception:
        return DEFAULT_PET_TYPE, 0.0

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        img = Image.open(image_path).convert("RGB")
        # 분류용이라 큰 해상도 불필요 → 256px로 다운샘플 (응답 시간/비용 절감)
        img.thumbnail((256, 256), Image.LANCZOS)
        response = client.models.generate_content(
            model=DETECTION_MODEL,
            contents=[_PROMPT, img],
        )
        text = (response.text or "").strip().lower()
    except Exception:
        return DEFAULT_PET_TYPE, 0.0

    # 응답 파싱: 정확히 한 단어인지, 키워드가 포함됐는지
    cleaned = "".join(c for c in text if c.isalnum() or c.isspace()).strip()
    tokens = cleaned.split()
    for word in PET_TYPES:
        if tokens == [word]:           # 완벽한 단일 토큰
            return word, 1.0
    for word in PET_TYPES:
        if word in tokens:             # 다른 단어와 섞임
            return word, 0.7
    for word in PET_TYPES:
        if word in cleaned:            # 토큰화 실패해도 substring 매칭
            return word, 0.5
    return DEFAULT_PET_TYPE, 0.0

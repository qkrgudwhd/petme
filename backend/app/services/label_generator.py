"""피사체에 맞는 32종 상징 라벨을 한 번에 생성 (Gemini 1회 호출).

푸들 강아지면: 안녕! → 왈왈안녕!, 파이팅 → 꼬리치며파이팅!
선인장이면:   안녕! → 뾰족안녕!, 파이팅 → 쑥쑥파이팅!
커피잔이면:   안녕! → 한모금?,   파이팅 → 카페인충전!

업로드 1회당 비용 ~$0.001, 약 3~5초.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from ..prompts.emotions import ALL_EMOTIONS
from . import secrets

MODEL = "gemini-2.5-flash"

# JSON 응답에서 코드 펜스 제거용
_FENCE_PREFIXES = ("```json", "```")


def _build_prompt(species_descriptor: str) -> str:
    emotion_list = "\n".join(
        f'  {e.key}: 기본="{e.label_ko}"  의미={e.prompt[:60]}'
        for e in ALL_EMOTIONS
    )
    return (
        "You are designing a 32-sticker KakaoTalk emoticon pack.\n"
        f"The pack stars: {species_descriptor}.\n\n"
        "For each of the 32 slots below, output a SHORT Korean caption that:\n"
        "- 1~8 Korean characters (한글 1~8자), VERY short\n"
        "- Reflects THIS specific subject — its species sound, shape, color, behavior, or signature trait\n"
        "- Preserves the EMOTIONAL MEANING of the slot (don't write 'love' for a 'goodbye' slot)\n"
        "- Uses only Korean characters + simple punctuation (! ? ~ . ㅋ ㅎ ㅠ)\n"
        "- Sounds native and playful, like real Korean sticker text\n\n"
        "Examples of tailoring:\n"
        "  Poodle dog 'hello'    → '왈왈안녕!'\n"
        "  Cactus     'hello'    → '뾰족안녕!'\n"
        "  Coffee cup 'hello'    → '한모금?'\n"
        "  Teddy bear 'love'     → '꼬옥사랑'\n"
        "  Cactus     'sleep'    → '뾰족꿈나라'\n"
        "  Coffee cup 'tired'    → '카페인필요'\n"
        "  Poodle     'fighting' → '꼬리파이팅!'\n\n"
        "32 slots (use these exact keys in the output JSON):\n"
        f"{emotion_list}\n\n"
        "Output: ONE JSON object with all 32 keys mapped to new Korean labels.\n"
        'Format: {"hello": "...", "bye": "...", ...}\n'
        "No markdown, no code fences, no explanation. Just the JSON."
    )


def generate_dynamic_labels(image_path: Path | str, species_descriptor: str) -> dict[str, str]:
    """피사체 이미지를 보고 32 라벨 생성. 실패 시 빈 dict (호출자가 기본값 사용)."""
    try:
        api_key = secrets.get_api_key_required()
    except Exception:
        return {}

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((512, 512), Image.LANCZOS)
        response = client.models.generate_content(
            model=MODEL,
            contents=[_build_prompt(species_descriptor), img],
        )
        text = (response.text or "").strip()
    except Exception:
        return {}

    # 코드 펜스 제거
    for fence in _FENCE_PREFIXES:
        if text.startswith(fence):
            text = text[len(fence):].lstrip()
            break
    if text.endswith("```"):
        text = text[:-3].rstrip()

    try:
        data = json.loads(text)
    except Exception:
        return {}

    valid_keys = {e.key for e in ALL_EMOTIONS}
    cleaned: dict[str, str] = {}
    for k, v in (data or {}).items():
        if k in valid_keys and isinstance(v, str):
            label = v.strip()
            if 0 < len(label) <= 20:
                cleaned[k] = label
    return cleaned

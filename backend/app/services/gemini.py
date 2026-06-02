"""Gemini 2.5 Flash Image — 캐릭터 일관성을 유지한 이모티콘 1장 생성."""
from __future__ import annotations

import time
from io import BytesIO
from typing import Iterable

from PIL import Image

from ..config import settings
from . import rate_limit, secrets

# 일시적 오류로 보는 키워드 (대소문자 무시). 이런 오류는 백오프 후 재시도.
# 주의: 영구 오류(spending cap 등)는 TRANSIENT가 아니다 — 별도 처리.
TRANSIENT_MARKERS = (
    "503", "unavailable", "high demand", "overloaded",
    "deadline", "timeout",
    "rate limit",  # 단순 속도 제한 (RPM)
    "internal error",
)

# 영구 오류 키워드 — 재시도 무의미. 사용자가 결제/한도 조치해야 함.
PERMANENT_BILLING_MARKERS = (
    "spending cap",
    "monthly spending",
    "billing account",
    "budget exceeded",
    "exceeded its monthly",
    "permission denied",
    "billing is not enabled",
    "free tier",  # 일부 무료 할당량 초과 메시지
    "daily_limit",  # 우리 rate_limit이 발생시킨 일일 한도
    "need_paid_confirm",  # 무료 한도 초과 — 사용자 동의 필요
)

MAX_RETRIES = 3
BACKOFF_SECONDS = (1.0, 3.0, 7.0)  # 1차 실패 후 1s, 2차 3s, 3차 7s

# Gemini가 안전/정책 사유로 "텍스트만" 돌려보내며 거부하는 패턴
REFUSAL_MARKERS = (
    "i cannot generate", "i can't generate",
    "i'm unable to", "i am unable to",
    "cannot create", "can't create",
    "not able to", "unable to combine",
    "policy", "safety", "guideline",
    "i cannot help", "i can't help",
)

# 화풍별 동적 디스크립터.
# - look:      Gemini에게 그릴 화풍의 시각적 특징 명시
# - transform: 변환 동사구 ("rendered as ...", "drawn as ...") — SUBJECTS 라인에 들어감
# - art_form:  결과물의 명사형 ("watercolor painting", "pixel art") — INSTRUCTION 라인에 들어감
# 화풍을 바꾸면 프롬프트 전체 톤이 바뀌도록 설계.
# 화풍별 시각 디스크립터. 각 화풍의 가장 특징적인 시각 요소를 극단적으로 강조해
# 결과물이 서로 명확히 구분되도록 작성. Gemini가 혼동하지 않게 핵심 단서들을 풍부히.
STYLE_DIRECTIVES: dict[str, dict[str, str]] = {
    "watercolor": {
        "look": (
            "TRADITIONAL WATERCOLOR PAINTING on cold-press paper. "
            "Visible paper grain and fiber texture throughout. "
            "Wet-on-wet bleeding edges, color halos around shapes, soft pigment pooling. "
            "Translucent washes layered (you can see paper through colors). "
            "Soft pencil under-sketch barely visible. "
            "Asymmetric organic shapes — no perfect lines. "
            "Palette: dusty muted tones, slightly washed-out. "
            "NO heavy black outlines. NO flat colors. NO digital cleanness."
        ),
        "transform": "painted as a delicate traditional watercolor",
        "art_form":  "watercolor painting on paper",
    },
    "pastel": {
        "look": (
            "SOFT PASTEL CHALK DRAWING on textured paper. "
            "VISIBLE chalk grain and powder dust. Smudged blending with finger marks. "
            "Crayon-like soft edges that fade into paper. "
            "Dusty muted color palette: mauve, sage, cream, peach, lavender — "
            "everything looks slightly faded/desaturated. "
            "Strokes show pastel stick direction. "
            "Hatching and crosshatching visible in shadow areas. "
            "Looks hand-drawn, slightly rough, child-art charm. "
            "NO crisp lines. NO digital perfection."
        ),
        "transform": "drawn with soft pastel chalks",
        "art_form":  "pastel chalk drawing on textured paper",
    },
    "cartoon2d": {
        "look": (
            "FLAT 2D CARTOON / STICKER ILLUSTRATION. "
            "THICK BOLD BLACK OUTLINES (4-6px equivalent) around every shape. "
            "100% FLAT solid colors — NO gradients, NO texture, NO airbrush. "
            "Cel-shading: exactly TWO tones per surface (base + one shadow). "
            "Super-deformed CHIBI proportions: oversized head, tiny body, large eyes. "
            "Bright saturated palette: candy colors, high vibrancy. "
            "Vector-art cleanness, crisp geometric shapes. "
            "Looks like a vinyl sticker or kakao emoticon. "
            "NO watercolor softness. NO halftone. NO pixels."
        ),
        "transform": "drawn as a flat chibi cartoon sticker",
        "art_form":  "flat 2D cartoon sticker",
    },
    "webtoon": {
        "look": (
            "MODERN KOREAN WEBTOON ILLUSTRATION (Naver/Kakao webtoon aesthetic). "
            "VERY THIN clean ink lines (1px), smooth digital inking. "
            "Soft cell shading with 2-3 tones per surface, gentle gradients on hair/skin. "
            "REALISTIC body proportions (NOT chibi) — slim modern figure. "
            "LARGE detailed eyes with multiple highlight reflections, glossy effect. "
            "Glossy hair with selective shine. "
            "Sophisticated muted palette with one accent color. "
            "Magazine-quality polish. "
            "NO chunky outlines. NO chibi heads. NO retro pixel look."
        ),
        "transform": "drawn in polished Korean webtoon style",
        "art_form":  "Korean webtoon panel illustration",
    },
    "pixel": {
        "look": (
            "16-BIT PIXEL ART SPRITE (Super Famicom / SNES era). "
            "EVERY pixel is a perfect square — VISIBLE PIXEL GRID. "
            "Sprite resolution about 48x48 to 64x64 scaled up — chunky pixels. "
            "STRICT LIMITED PALETTE (16-24 colors maximum total). "
            "ZERO anti-aliasing — pure hard pixel edges everywhere. "
            "Dithering used for gradients (checkerboard pattern between two colors). "
            "Single-pixel highlights and shadows. "
            "Retro RPG/game character look — Pokemon Gold, Stardew Valley, Terraria. "
            "NO smooth curves. NO watercolor. NO halftone."
        ),
        "transform": "rendered as a 16-bit pixel art sprite",
        "art_form":  "16-bit pixel art sprite",
    },
    "popart": {
        "look": (
            "POP ART POSTER in Roy Lichtenstein / Warhol style. "
            "VISIBLE BEN-DAY HALFTONE DOTS — large evenly-spaced dot patterns "
            "filling skin and shaded areas. "
            "STRICTLY LIMITED 4-COLOR PALETTE: black, red, yellow, blue (CMYK-ish). "
            "Maybe a fifth accent (pink or cyan). "
            "ULTRA THICK BLACK OUTLINES (5-8px), comic book style. "
            "FLAT solid color fills inside outlines — no gradients. "
            "Graphic, decorative, screen-printed poster look. "
            "Bold, loud, retro 1960s comic aesthetic. "
            "NO realism. NO watercolor softness. NO pixel grid."
        ),
        "transform": "rendered as a Lichtenstein-style pop art poster",
        "art_form":  "pop art halftone poster",
    },
}


def _build_prompt(
    emotion_prompt: str,
    label_ko: str,
    style_key: str,
    pet_type: str = "dog",
    person_palette: list[str] | None = None,
    pet_palette: list[str] | None = None,
    safer: bool = False,
    person_description: str = "",
    pet_description: str = "",
) -> str:
    """이모티콘 1장 생성 프롬프트. 한글 캡션은 PIL 후처리에서 합성.

    화풍에 따라 "transform"·"art_form" 표현이 동적으로 바뀐다.
    `safer=True` 면 안전 정책 거부 후 폴백용 — 더 부드러운 표현으로 재작성.
    """
    from ..prompts.emotions import get_species_descriptor
    style = STYLE_DIRECTIVES.get(style_key, STYLE_DIRECTIVES["cartoon2d"])
    style_look = style["look"]
    style_transform = style["transform"]       # 예: "painted in a soft watercolor style"
    style_art_form = style["art_form"]         # 예: "original watercolor artwork"
    species = get_species_descriptor(pet_type)

    person_pal_str = ", ".join(person_palette or []) or "(see reference image)"
    pet_pal_str = ", ".join(pet_palette or []) or "(see reference image)"

    # 두 모드 차이는 "강조 수준"만. 핵심 메시지(화풍에 맞는 변환)는 동일.
    if safer:
        person_phrase = (
            f"a character {style_transform}, loosely inspired by the person in the reference"
        )
        creative_note = (
            f"Use the reference photos ONLY as loose visual inspiration. "
            f"The output is an {style_art_form} — a brand new illustration in the "
            f"chosen style, NOT a photo trace or photo edit."
        )
    else:
        person_phrase = (
            f"a character {style_transform}, inspired by the person in the reference"
        )
        creative_note = (
            f"This is an {style_art_form}, not a photo edit. Use the references for "
            f"color, clothing, and feature inspiration. Fully transform into the "
            f"selected style — render every element in that artistic medium."
        )

    # ─── 일관성 강제 (모든 호출에 절대 적용) ───
    # 사용자 설명이 없어도 종 디스크립터 + 팔레트로 폴백 설명을 만들어 항상 채운다.
    if not pet_description:
        pet_pal_short = ", ".join((pet_palette or [])[:3]) or "as in the reference image"
        pet_description = f"{species} (colors: {pet_pal_short})"
    if not person_description:
        person_pal_short = ", ".join((person_palette or [])[:3]) or "as in the reference image"
        person_description = f"the person from reference image (colors: {person_pal_short})"

    consistency_block = (
        "\n"
        "════════════════════════════════════════════════════════════\n"
        " ABSOLUTE CHARACTER CONSISTENCY — NON-NEGOTIABLE — HIGHEST PRIORITY\n"
        "════════════════════════════════════════════════════════════\n"
        " This sticker is part of a 32-piece pack. ALL 32 stickers MUST show\n"
        " the EXACT SAME two characters — no exceptions, no substitutions.\n"
        "\n"
        f"   1) PERSON     : {person_description}\n"
        f"   2) SECOND ONE : {pet_description}\n"
        "\n"
        " RULES (ALL MANDATORY):\n"
        f"   • The second subject MUST be a {species}. NOT a different animal.\n"
        "   • If reference shows a monkey → draw a monkey, NOT a cat/dog.\n"
        "   • If reference shows a poodle → draw a poodle, NOT a shiba/golden.\n"
        "   • If reference shows a cat    → draw a cat,    NOT a dog/rabbit.\n"
        "   • If reference shows a plant  → draw that plant, NOT a flower bouquet.\n"
        "   • If reference shows a toy    → draw that toy,   NOT a different toy.\n"
        "   • Preserve species, breed, color, pattern, body proportions, distinct features.\n"
        "   • The person's face shape/hairstyle/glasses/clothing must match the description.\n"
        "   • This is NON-NEGOTIABLE. Substituting the species or person breaks the sticker pack.\n"
        "════════════════════════════════════════════════════════════\n"
    )

    return (
        f"Create a single original sticker (KakaoTalk-style emoticon) as a {style_art_form}.\n"
        f"{consistency_block}"
        "\n"
        f"★★★ MANDATORY STYLE ★★★\n"
        f"{style_look}\n"
        f"The output MUST be unmistakably a {style_art_form}. Do not blend with other styles.\n"
        "\n"
        f"SUBJECTS: {person_phrase}, together with {species}, both rendered consistently "
        f"in the same {style_art_form} style. Both characters MUST match the descriptions above exactly.\n"
        f"CREATIVE NOTE: {creative_note}\n"
        "\n"
        "★ COLOR REFERENCE (style hints) ★\n"
        f"  • Person palette: {person_pal_str}\n"
        f"    Apply these colors to the character's hair, outfit, and accessories.\n"
        f"  • Second subject palette: {pet_pal_str}\n"
        f"    Apply these colors to the subject's fur/feathers/leaves/surface as appropriate.\n"
        "  • Aim for visual consistency across the 32-sticker set.\n"
        "\n"
        "BEHAVIOR per subject type:\n"
        "  - Pet animals: species-appropriate actions (dog bark/wag, cat meow/knead, "
        "rabbit hop, bird chirp/flap, hamster squeak).\n"
        "  - Plants: leaves wave like hands, sway, sparkle when healthy.\n"
        "  - Stuffed toys/dolls: anthropomorphized — arms wave, body bouncy.\n"
        "  - Objects: anthropomorphized with a cute face on the surface.\n"
        "  - Food: cute face on the food surface, steam/sparkle.\n"
        "  - Characters: in-character signature poses.\n"
        "Express the emotion clearly within the chosen artistic style.\n"
        "\n"
        f"SCENE / ACTION: {emotion_prompt}.\n"
        "\n"
        "TEXT: DO NOT include any text, letters, captions, words, numbers, or speech "
        "bubbles with text. No Korean, English, or any language. Keep the TOP 25% of "
        "the image visually clear/uncluttered — caption will be added later by post-processing.\n"
        "COMPOSITION: subject centered in the bottom portion of the canvas, "
        "square 1:1 framing, FULLY TRANSPARENT background "
        "(no scenery, no border, no drop shadow). Single sticker only.\n"
        "\n"
        "═══ FINAL CHECK BEFORE OUTPUT ═══\n"
        f"  ✓ Is the second character a {species}? (NOT a different species)\n"
        "  ✓ Do both characters match the PERSON/SECOND ONE descriptions above?\n"
        "  ✓ Is the style 100% the specified " + style_art_form + "?\n"
        "  ✓ Is the background fully transparent?\n"
        "  ✓ Is there NO text in the image?\n"
        "If any answer is NO, regenerate before responding.\n"
        "\n"
        "Output: one image."
    )


def _references_to_images(reference_paths: Iterable[str]) -> list[Image.Image]:
    return [Image.open(p).convert("RGBA") for p in reference_paths]


def generate_emoticon(
    *,
    reference_paths: list[str],
    emotion_prompt: str,
    label_ko: str,
    style_key: str,
    pet_type: str = "dog",
    person_palette: list[str] | None = None,
    pet_palette: list[str] | None = None,
    person_description: str = "",
    pet_description: str = "",
) -> bytes:
    """Gemini 호출 → 생성된 이미지 바이트(PNG/JPEG 원본) 반환.

    호출자가 PIL로 열어 360x360 정사각 정규화 + 누끼 보정 + 압축 처리.
    """
    # 매 호출마다 디스크에서 복호화 → 로컬 변수로만 사용 (글로벌 보관 X)
    api_key = secrets.get_api_key_required()

    # google-genai SDK는 import 비용이 있어 lazy
    from google import genai

    # 무료 티어 강제: 분당 10회 미만 + 일 95장 한도 체크 (초과 시 RuntimeError)
    rate_limit.reserve_one()

    client = genai.Client(api_key=api_key)
    refs = _references_to_images(reference_paths)

    def _call(safer: bool):
        prompt = _build_prompt(
            emotion_prompt, label_ko, style_key, pet_type,
            person_palette=person_palette, pet_palette=pet_palette,
            safer=safer,
            person_description=person_description,
            pet_description=pet_description,
        )
        return client.models.generate_content(
            model=settings.gemini_image_model,
            contents=[prompt, *refs],
        )

    # 1차: 일반 프롬프트 + 일시 오류만 백오프 재시도
    response = None
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = _call(safer=False)
            break
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            # 영구 오류(spending cap 등)는 재시도 안 하고 명확한 메시지로 즉시 실패
            if any(m in msg for m in PERMANENT_BILLING_MARKERS):
                raise RuntimeError(
                    "BILLING_LIMIT: Google Cloud 프로젝트의 결제 한도/spending cap에 도달했습니다. "
                    "console.cloud.google.com/billing 에서 한도를 확인·조정하거나 새 API 키를 발급받으세요. "
                    f"원본 메시지: {str(e)[:200]}"
                )
            if not any(m in msg for m in TRANSIENT_MARKERS) or attempt >= MAX_RETRIES:
                raise
            time.sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])

    if response is None and last_err:
        raise last_err

    # 응답 점검: 이미지가 없고 텍스트만 있으며 거부 패턴이 있으면 safer 프롬프트로 1회 재시도
    if not _has_image(response):
        text = _collect_text(response).lower()
        if any(m in text for m in REFUSAL_MARKERS):
            # 짧게 쉰 뒤 safer 모드로 재시도
            time.sleep(1.0)
            response = _call(safer=True)

    # 응답에서 첫 inline_data(image) 추출
    for cand in response.candidates or []:
        for part in cand.content.parts if cand.content else []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data

    # 텍스트만 돌아온 경우 → 거부인지 명시
    text = _collect_text(response)
    if any(m in text.lower() for m in REFUSAL_MARKERS):
        raise RuntimeError(
            f"Gemini가 안전 정책으로 거부했습니다 (safer 폴백도 실패): {text[:200]}"
        )
    raise RuntimeError(f"Gemini가 이미지를 반환하지 않았습니다. 응답: {text[:300] or '(empty)'}")


def _has_image(response) -> bool:
    for cand in response.candidates or []:
        for part in cand.content.parts if cand.content else []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return True
    return False


def _collect_text(response) -> str:
    out = ""
    for cand in response.candidates or []:
        for part in cand.content.parts if cand.content else []:
            if getattr(part, "text", None):
                out += part.text
    return out


def normalize_to_emoticon(raw_bytes: bytes, label_ko: str = "") -> Image.Image:
    """생성 결과를 카카오 규격으로 정규화 + 한글 캡션 직접 합성.
    1) rembg로 배경 한 번 더 제거 (Gemini가 못 지운 경우 대비)
    2) 360x360 정사각 패딩
    3) PIL로 한글 캡션 상단 합성 (Gemini는 한글을 그리지 못함)
    """
    from .images import fit_square, remove_background
    from .text_overlay import overlay_caption

    cut = remove_background(raw_bytes)
    square = fit_square(cut, 360)
    if label_ko:
        square = overlay_caption(square, label_ko)
    return square


def open_raw_bytes(raw: bytes) -> Image.Image:
    return Image.open(BytesIO(raw)).convert("RGBA")

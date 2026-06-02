"""한글 텍스트를 이미지 상단에 직접 합성.

Gemini 2.5 Flash Image는 비라틴 문자(한글) 렌더링이 매우 불안정해
"안녕"이 "안념"으로 깨지는 등 글자가 잘못 나온다. 그래서 그림은 Gemini가,
텍스트는 PIL로 우리가 직접 그린다.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Windows에 기본 설치된 한글 폰트. 없으면 NanumGothic, 그것도 없으면 기본 폰트.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgunbd.ttf",            # 맑은 고딕 Bold
    "C:/Windows/Fonts/malgun.ttf",              # 맑은 고딕
    "C:/Windows/Fonts/NanumGothicExtraBold.ttf",
    "C:/Windows/Fonts/NanumGothicBold.ttf",
    "C:/Windows/Fonts/NanumGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # macOS 폴백
]


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _measure(font, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def overlay_caption(img: Image.Image, text: str) -> Image.Image:
    """이모티콘 상단에 한글 캡션을 합성. 글자 길이에 맞춰 자동 크기 조정."""
    if not text:
        return img

    img = img.convert("RGBA")
    w, h = img.size
    target_width = int(w * 0.78)  # 가로 78% 안에 들어오도록

    # 적당한 폰트 사이즈 찾기 (이진 탐색 대신 단순 감소)
    size = int(h * 0.18)  # 시작: 캔버스 높이의 18%
    font = _find_font(size)
    text_w, text_h = _measure(font, text)
    while text_w > target_width and size > 24:
        size -= 4
        font = _find_font(size)
        text_w, text_h = _measure(font, text)

    # 상단 중앙 배치 (위에서 6% 여백)
    x = (w - text_w) // 2
    y = max(8, int(h * 0.06))

    draw = ImageDraw.Draw(img)
    stroke = max(3, size // 10)  # 외곽선 두께

    # 흰색 두꺼운 외곽선 + 진한 색상 글자 → 어떤 배경에도 잘 보임
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(20, 20, 20, 255),       # 거의 검정
        stroke_width=stroke,
        stroke_fill=(255, 255, 255, 255),  # 흰색 테두리
    )
    return img

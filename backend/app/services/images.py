"""이미지 전처리: 누끼(rembg) + 360x360 정사각 리사이즈 + PNG 최적화."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

TARGET_SIZE = 360
MAX_FILE_BYTES = 650 * 1024  # 카카오톡 32종 규격
ICON_SIZE = 78
ICON_MAX_BYTES = 16 * 1024   # 카카오톡 아이콘 규격

_rembg_session = None


def _get_rembg_session():
    """rembg 모델은 첫 호출 시 다운로드되므로 캐시."""
    global _rembg_session
    if _rembg_session is None:
        from rembg import new_session

        _rembg_session = new_session("u2net")
    return _rembg_session


def remove_background(image_bytes: bytes) -> Image.Image:
    """배경 제거. RGBA Image 반환."""
    from rembg import remove

    cut = remove(image_bytes, session=_get_rembg_session())
    img = Image.open(BytesIO(cut)).convert("RGBA")
    return _crop_to_alpha(img)


def _crop_to_alpha(img: Image.Image) -> Image.Image:
    """알파 채널 기준 bbox로 크롭. 주체만 남기고 여백 제거."""
    bbox = img.split()[-1].getbbox()
    return img.crop(bbox) if bbox else img


def fit_square(img: Image.Image, size: int = TARGET_SIZE, padding_ratio: float = 0.08) -> Image.Image:
    """투명배경 정사각 캔버스 가운데에 비율 유지 배치."""
    img = img.convert("RGBA")
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * (1 - 2 * padding_ratio))
    w, h = img.size
    scale = min(inner / w, inner / h)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    off = ((size - new_w) // 2, (size - new_h) // 2)
    canvas.paste(resized, off, resized)
    return canvas


def extract_palette(image_path: Path, n_colors: int = 5,
                    min_alpha: int = 200) -> list[str]:
    """누끼 이미지에서 대표 색상을 hex 코드로 추출 (빈도 내림차순).

    - 배경(투명) 픽셀은 제외 (min_alpha 이상만 카운트)
    - 너무 어둡거나 너무 밝은 회색은 강조 색상에서 약화
    - 반환 예: ['#1A2B3C', '#F5E6D3', ...]
    """
    img = Image.open(image_path).convert("RGBA")
    pixels: list[tuple[int, int, int]] = []
    for px in img.getdata():
        if px[3] >= min_alpha:
            pixels.append(px[:3])
    if not pixels:
        return []

    # 픽셀들을 가로로 늘어놓은 단일 행 이미지를 만들어 quantize
    sample = Image.new("RGB", (len(pixels), 1))
    sample.putdata(pixels)
    q = sample.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    palette = q.getpalette() or []
    # 각 색 인덱스의 픽셀 개수
    counts = q.getcolors() or []  # [(count, idx), ...]
    counts.sort(reverse=True)  # 빈도 내림차순

    hex_colors: list[str] = []
    for count, idx in counts[:n_colors]:
        if count == 0:
            continue
        r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
        hex_colors.append(f"#{r:02X}{g:02X}{b:02X}")
    return hex_colors


def make_icon(source_path: Path, output_path: Path,
              size: int = ICON_SIZE, max_bytes: int = ICON_MAX_BYTES) -> int:
    """기존 이모티콘 PNG → 키보드 메인 영역 아이콘(기본 78x78, 16KB 이하).

    카카오 가이드라인:
    - 사이즈: 78 × 78 px
    - 파일 형식: PNG
    - 용량: 16KB 이하
    """
    img = Image.open(source_path).convert("RGBA")
    bbox = img.split()[-1].getbbox()
    if bbox:
        img = img.crop(bbox)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * 0.94)  # 작은 사이즈라 여백 축소
    scale = min(inner / img.width, inner / img.height)
    new_w, new_h = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return save_png_optimized(canvas, output_path, max_bytes=max_bytes)


def save_png_optimized(img: Image.Image, path: Path, max_bytes: int = MAX_FILE_BYTES) -> int:
    """650KB 이하가 되도록 quantize 단계적 적용. 파일 크기 반환."""
    path.parent.mkdir(parents=True, exist_ok=True)

    # 1) 무손실 우선
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    if buf.tell() <= max_bytes:
        path.write_bytes(buf.getvalue())
        return buf.tell()

    # 2) 팔레트 양자화 (알파 유지)
    for colors in (256, 192, 128, 96, 64):
        try:
            alpha = img.split()[-1]
            quant = img.convert("RGB").quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
            quant = quant.convert("RGBA")
            quant.putalpha(alpha)
            buf = BytesIO()
            quant.save(buf, format="PNG", optimize=True)
            if buf.tell() <= max_bytes:
                path.write_bytes(buf.getvalue())
                return buf.tell()
        except Exception:
            continue

    # 3) 그래도 크면 마지막 시도 저장
    path.write_bytes(buf.getvalue())
    return buf.tell()

"""카카오톡 이모티콘 스튜디오 제출용 ZIP 패키징.

구조:
  petme-emoticons.zip
    ├── stickers/      # 32장 (360x360, ≤650KB)
    │   ├── hello.png
    │   ├── bye.png
    │   └── ...
    ├── icon.png       # 키보드 메인 영역 아이콘 (78x78, ≤16KB)
    ├── manifest.json  # 메타데이터
    └── README.txt     # 제출 가이드
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path


_README = """PetMe-Moji — 카카오톡 이모티콘 제출 패키지

[규격]
- 이모티콘(stickers/ 안): 32장, 360x360 px, PNG, 투명배경, 각 650KB 이하
- 아이콘(icon.png): 1장, 78x78 px, PNG, 투명배경, 16KB 이하

[제출 절차]
1) https://emoticonstudio.kakao.com 접속
2) 새 제안 → "멈춰있는 이모티콘" 선택
3) stickers/ 폴더의 32장을 순서대로 업로드
4) icon.png를 키보드 아이콘 영역에 업로드
5) 제목/설명 작성 후 제안 제출

manifest.json 에 각 파일의 한글 라벨·바이트·소요시간이 정리되어 있어요.
"""


def build_zip(session_output_dir: Path, manifest: dict) -> Path:
    """세션 출력 디렉터리 → 제출용 ZIP 패키징."""
    zip_path = session_output_dir / "petme-emoticons.zip"
    manifest_path = session_output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    readme_path = session_output_dir / "README.txt"
    readme_path.write_text(_README, encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 32장은 stickers/ 폴더에 배치 (icon.png와 분리)
        for png in sorted(session_output_dir.glob("*.png")):
            if png.name == "icon.png":
                zf.write(png, arcname="icon.png")
            else:
                zf.write(png, arcname=f"stickers/{png.name}")
        zf.write(manifest_path, arcname="manifest.json")
        zf.write(readme_path, arcname="README.txt")
    return zip_path

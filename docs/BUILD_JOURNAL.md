# PetMe-Moji 빌드 저널

> 인물 + 반려동물 사진으로 카카오톡 이모티콘 32종을 자동 생성하는 AI 앱을
> 기획서 한 장에서 출발해 실행 가능한 데스크톱 애플리케이션까지 만든 기록.
> AI 페어 프로그래밍 워크플로의 실제 예시이자, Gemini 2.5 Flash Image,
> FastAPI, Next.js, Tkinter, Fernet 암호화 같은 기술을 한 프로젝트에서
> 어떻게 엮는지를 보여주는 튜토리얼.

**대상 독자**

- 직접 LLM/이미지 생성 API로 무언가 만들어 보고 싶은 개발자
- 기획서를 동작하는 코드로 옮기는 과정의 의사결정을 보고 싶은 분
- Windows 환경에서 GUI 런처 + 웹앱 하이브리드 배포를 고민하는 분

**완성 산출물**

- 더블클릭으로 실행되는 Windows 앱 (콘솔창 없음)
- 첫 화면에서 API 키 입력 + 사진 2장 선택 + 자동 업로드
- Gemini 2.5 Flash Image로 32종 이모티콘 동시 생성
- 실시간 진행률 차트, 활동 로그, ZIP 패키징
- 외부(디스크) + 내부(메모리) API 키 암호화

---

## 목차

- [1장. 기획서에서 출발하기](#1장-기획서에서-출발하기)
- [2장. 기술 스택 결정](#2장-기술-스택-결정)
- [3장. 백엔드 골격 — FastAPI + 누끼 파이프라인](#3장-백엔드-골격--fastapi--누끼-파이프라인)
- [4장. 32종 감정 프롬프트 템플릿 설계](#4장-32종-감정-프롬프트-템플릿-설계)
- [5장. Next.js 프론트엔드 + 업로드 UI](#5장-nextjs-프론트엔드--업로드-ui)
- [6장. Gemini 2.5 Flash Image 연동](#6장-gemini-25-flash-image-연동)
- [7장. 32종 일괄 생성 + SSE 진행률 + ZIP](#7장-32종-일괄-생성--sse-진행률--zip)
- [8장. 실행 검증 & 의존성 트러블슈팅](#8장-실행-검증--의존성-트러블슈팅)
- [9장. 원클릭 배치 실행 파일](#9장-원클릭-배치-실행-파일)
- [10장. API 키 GUI + Fernet 암호화](#10장-api-키-gui--fernet-암호화)
- [11장. Tkinter GUI 런처](#11장-tkinter-gui-런처)
- [12장. 게이트 화면 + 실시간 대시보드 + 콘솔 숨김](#12장-게이트-화면--실시간-대시보드--콘솔-숨김)
- [13장. 런처에서 직접 키 등록](#13장-런처에서-직접-키-등록)
- [14장. 런처에서 사진 선택 + 자동 업로드](#14장-런처에서-사진-선택--자동-업로드)
- [부록 A. 전체 폴더 구조](#부록-a-전체-폴더-구조)
- [부록 B. 명령어 치트시트](#부록-b-명령어-치트시트)
- [부록 C. 배운 점 정리](#부록-c-배운-점-정리)

**제2부 — 실전 피드백 반영**

- [15장. API 키 — 표시·기억·검증의 세 가지 함정](#15장-api-키--표시기억검증의-세-가지-함정)
- [16장. 글자가 깨진다 — Gemini의 비라틴 문자 한계](#16장-글자가-깨진다--gemini의-비라틴-문자-한계)
- [17장. 한 번의 실수 — 사진 선택 패널의 추가와 제거](#17장-한-번의-실수--사진-선택-패널의-추가와-제거)
- [18장. 503 오류 — 일시적 장애를 자동 복구로](#18장-503-오류--일시적-장애를-자동-복구로)
- [19장. 진행률을 사람에게 보여주는 법](#19장-진행률을-사람에게-보여주는-법)
- [제2부 부록 — 변경 파일 요약](#제2부-부록--변경-파일-요약)
- [제2부 회고 — 8가지 추가 교훈](#제2부-회고--8가지-추가-교훈)

---

## 1장. 기획서에서 출발하기

### 1.1 받은 기획서 요약

> 인물·반려동물 사진을 기반으로 감정 표현이 극대화된 카카오톡 이모티콘 32종을
> 자동 생성하는 AI 애플리케이션 (가칭: **PetMe-Moji**).

| 항목 | 카카오톡 공식 규격 |
| --- | --- |
| 수량 | **32장** |
| 사이즈 | **360 × 360 px**, RGB |
| 포맷 | **PNG, 투명배경 필수** |
| 용량 | 1장당 **650KB 이하** |
| 감정 | 일상 대화, 희로애락의 직관적 표현 |

### 1.2 기획서가 제안한 기술과, 실제 채택한 기술

기획서는 SAM, Stable Diffusion LoRA, OpenCV 등 무거운 옵션을 제안했지만
MVP 단계에서는 **간단함이 곧 속도**다. 다음과 같이 다이어트했다.

| 기획서 | 채택 | 이유 |
| --- | --- | --- |
| SAM (Segment Anything) | **rembg (U2Net)** | CPU에서 1초, 모델 170MB, 코드 3줄. |
| Stable Diffusion + LoRA | **Gemini 2.5 Flash Image** | 캐릭터 일관성(consistency)이 multi-image 입력만으로 매우 강함. 파인튜닝 불필요. |
| OpenCV 텍스트 오버레이 | **Gemini 프롬프트에 한글 포함** | 한 번에 결과가 나옴. 별도 합성 단계 제거. |

이 결정은 "1장 = 5분, 1주 = 32시간" 같은 비대한 일정을 막아주는
**가장 큰 단일 결정**이었다. 기획서의 모든 항목을 그대로 구현하려 하지 말 것.

---

## 2장. 기술 스택 결정

### 2.1 사용자에게 물어본 4가지

기획자(= 의뢰인)와 첫 정렬을 위해 다음 네 질문에 답을 받았다.
이 4가지는 폴더 구조와 의존성을 완전히 바꿔놓는 결정이다.

1. **플랫폼**: 웹앱 / 데스크톱 앱 / Python CLI 중 무엇?
2. **AI 백엔드**: Replicate, Gemini, Stability AI, 로컬 SD 중 무엇?
3. **API 키 보유 여부**
4. **MVP 범위**: 전체 한 번에 / 핵심부터 단계적 / 백엔드만 CLI

**선택 결과**

- 플랫폼: 웹앱 (Next.js + FastAPI)
- AI: **Gemini 2.5 Flash Image** (Nano Banana — 캐릭터 일관성 강점)
- 키: Google AI Studio 키 보유
- 범위: 핵심부터 단계적 진행

### 2.2 최종 아키텍처

```
사용자 사진 2장
   │
   ▼
[프론트엔드: Next.js + Tailwind]
   │  (multipart upload)
   ▼
[백엔드: FastAPI]
   ├── /api/upload          rembg로 누끼 → 360x360 패딩
   ├── /api/generate/batch  Gemini 호출 32회 (asyncio.Semaphore=4)
   │                        ↓ SSE 진행률 스트림
   │                        ↓ ZIP 패키징 + manifest.json
   └── /api/settings/key    Fernet 암호화 (AES-128 + HMAC)

[런처: Tkinter]
   └── 서버 spawn (콘솔창 숨김) + 키 등록 + 사진 선택 + 자동 업로드
```

---

## 3장. 백엔드 골격 — FastAPI + 누끼 파이프라인

### 3.1 디렉터리 한 번에 만들기

```bash
mkdir -p backend/app/{routers,services,prompts,storage/{uploads,outputs}}
mkdir -p frontend/app/components frontend/lib
```

### 3.2 의존성 (`backend/requirements.txt`)

처음에는 명시적인 버전 핀을 박았지만, Python 3.14에서
`pydantic-core`가 Rust 빌드를 요구하며 깨졌다 — **8장에서 교훈으로 다룸**.
지금은 범위 표기로 완화된 상태:

```text
fastapi>=0.115
uvicorn[standard]>=0.32
python-multipart>=0.0.12
pydantic>=2.11
pydantic-settings>=2.6
Pillow>=12.1,<13.0
rembg>=2.0.75
onnxruntime
google-genai>=1.0,<3.0
python-dotenv>=1.0
cryptography>=42.0
```

### 3.3 누끼 + 정사각 패딩 + 650KB 압축 (`services/images.py`)

카카오 가이드를 만족하는 세 단계를 한 함수씩.

```python
def remove_background(image_bytes: bytes) -> Image.Image:
    """배경 제거 후 알파 채널 bbox로 크롭."""
    from rembg import remove
    cut = remove(image_bytes, session=_get_rembg_session())
    img = Image.open(BytesIO(cut)).convert("RGBA")
    return _crop_to_alpha(img)


def fit_square(img: Image.Image, size: int = 360, padding_ratio: float = 0.08):
    """투명배경 정사각 캔버스 가운데에 비율 유지 배치."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * (1 - 2 * padding_ratio))
    scale = min(inner / img.width, inner / img.height)
    new_w, new_h = int(img.width * scale), int(img.height * scale)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas.paste(resized, ((size - new_w) // 2, (size - new_h) // 2), resized)
    return canvas


def save_png_optimized(img, path, max_bytes=650 * 1024):
    """650KB 이하가 되도록 256→192→128→96→64 단계적 팔레트 양자화."""
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    if buf.tell() <= max_bytes:
        path.write_bytes(buf.getvalue()); return buf.tell()
    for colors in (256, 192, 128, 96, 64):
        alpha = img.split()[-1]
        quant = img.convert("RGB").quantize(colors=colors).convert("RGBA")
        quant.putalpha(alpha)
        buf = BytesIO()
        quant.save(buf, format="PNG", optimize=True)
        if buf.tell() <= max_bytes:
            path.write_bytes(buf.getvalue()); return buf.tell()
    path.write_bytes(buf.getvalue()); return buf.tell()
```

**핵심 포인트**

- `rembg`의 세션은 처음 호출 시에만 모델을 다운로드하므로 모듈 전역에 캐시.
- 8% 패딩으로 카카오 가이드라인 여백 확보.
- 650KB 제한은 무손실 PNG가 안 되면 팔레트 양자화로 단계적으로 줄임.

### 3.4 업로드 라우터 (`routers/upload.py`)

```python
@router.post("")
async def upload(person: UploadFile = File(...), pet: UploadFile = File(...)):
    session_id = uuid.uuid4().hex[:12]
    sess_dir = settings.upload_dir / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    result = {"session_id": session_id, "items": {}}
    for label, f in (("person", person), ("pet", pet)):
        data = await f.read()
        cut = remove_background(data)
        preview = fit_square(cut, 360)
        out_path = sess_dir / f"{label}_preview.png"
        size = save_png_optimized(preview, out_path)
        result["items"][label] = {
            "preview_url": f"/files/uploads/{session_id}/{out_path.name}",
            "bytes": size,
        }
    return result
```

세션 id는 짧은 UUID로. 한 번의 요청에 인물+반려동물 두 장을 묶어
같은 폴더에 보관 — 32장 생성 단계에서 같은 폴더를 다시 참조한다.

---

## 4장. 32종 감정 프롬프트 템플릿 설계

기획서는 32개를 3개 카테고리로 나눴다.

- **기본 감정 10**: 인사, 감사, 사과, 축하, 사랑, 웃음, 눈물, 분노, 당황, 놀람
- **반려동물 일상 12**: 밥 줘, 산책 가자, 간식, 멍때리기, 하품, 꿀잠, 삐짐 …
- **인물+반려동물 협동 10**: 머리 위 펫, 같이 좌절, 같이 파이팅, 돈 좋아 …

`prompts/emotions.py`에 데이터 클래스로 정리.

```python
@dataclass(frozen=True)
class Emotion:
    key: str        # 파일명 (예: "hello")
    label_ko: str   # 이모티콘에 합성될 한글 (예: "안녕!")
    prompt: str     # 영문 행동/표정 묘사
```

**왜 영문 프롬프트?**
Gemini가 영문 액션 묘사에 가장 안정적이다. 한글 라벨은 별도로
이미지 안에 합성된다. 두 언어의 역할을 분리하는 게 핵심.

예시 한 항목:

```python
Emotion("congrats", "축하해!",
        "confetti and party popper, joyful jump, huge grin, sparkles")
```

마지막에 32개가 정확히 들어있는지 `assert`로 보장한다.

```python
ALL_EMOTIONS = [*BASIC, *PET_DAILY, *DUO]
assert len(ALL_EMOTIONS) == 32
```

---

## 5장. Next.js 프론트엔드 + 업로드 UI

### 5.1 왜 Next.js?

- 1) 추후 모바일 래핑(PWA)으로 자연스럽게 확장 가능
- 2) `next.config.js`의 rewrites로 dev 환경 CORS 우회가 쉬움

```js
// frontend/next.config.js
async rewrites() {
  return [
    { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    { source: "/files/:path*", destination: "http://localhost:8000/files/:path*" },
  ];
}
```

### 5.2 UploadCard — 드래그 앤 드롭 + 클릭

```tsx
<div onClick={() => inputRef.current?.click()}
     onDragOver={(e) => e.preventDefault()}
     onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files?.[0]); }}>
  <input ref={inputRef} type="file" accept="image/*" hidden onChange={...} />
  {preview ? <img src={preview} /> : "사진을 끌어다 놓으세요"}
</div>
```

`URL.createObjectURL`로 즉시 미리보기, 컴포넌트 언마운트 시
`revokeObjectURL`로 메모리 누수 방지.

---

## 6장. Gemini 2.5 Flash Image 연동

### 6.1 캐릭터 일관성을 어떻게 유지할까

문제: 32장에서 같은 펫이 유지되어야 한다.
해결: Gemini는 **multi-image input**을 지원한다. 누끼 처리된
인물 + 누끼 처리된 펫 두 장을 항상 같이 보낸다.

```python
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt_text, person_pil, pet_pil],
)
```

### 6.2 프롬프트 템플릿

영문으로 작성하되, 마지막에 한글 라벨을 명시.

```python
def _build_prompt(emotion_prompt, label_ko, style_key):
    style = STYLE_DIRECTIVES.get(style_key, STYLE_DIRECTIVES["cartoon2d"])
    return (
        "Create a single KakaoTalk-style sticker image.\n"
        f"STYLE: {style}.\n"
        "SUBJECTS: keep the SAME person and the SAME pet from references — "
        "preserve identity (hair, fur color, body shape). "
        "Exaggerate emotion chibi-style.\n"
        f"SCENE / ACTION: {emotion_prompt}.\n"
        f'TEXT: include Korean caption "{label_ko}" in bold playful font, '
        "placed where it does not cover faces.\n"
        "COMPOSITION: subject centered, 1:1 square, FULLY TRANSPARENT background.\n"
        "Output: one image."
    )
```

### 6.3 화풍 다변화

6가지 디렉티브를 단일 dict로 관리. 사용자가 화풍을 바꾸면
한 줄만 교체되므로 32장 전체가 일관된 톤을 갖는다.

```python
STYLE_DIRECTIVES = {
    "watercolor": "soft watercolor illustration, gentle brush strokes, ...",
    "cartoon2d":  "clean 2D cartoon style, thick bold outlines, ...",
    "webtoon":    "Korean webtoon style, clean line art, ...",
    "pixel":      "16-bit pixel art, limited palette, ...",
    # ...
}
```

### 6.4 결과 정규화

Gemini가 배경을 깔끔히 못 지운 경우를 대비해 한 번 더 rembg.

```python
def normalize_to_emoticon(raw_bytes: bytes) -> Image.Image:
    from .images import fit_square, remove_background
    cut = remove_background(raw_bytes)
    return fit_square(cut, 360)
```

---

## 7장. 32종 일괄 생성 + SSE 진행률 + ZIP

### 7.1 동시성 = 4

Gemini의 분당 RPM 한도를 고려해 `asyncio.Semaphore(4)` 로
동시 호출을 제한. 큐로 진행률을 전달한다.

```python
CONCURRENCY = 4

@router.get("/batch")
async def generate_batch(session_id: str, style: str):
    refs = _reference_paths(session_id)
    out_dir = settings.output_dir / session_id
    sem = asyncio.Semaphore(CONCURRENCY)
    q = asyncio.Queue()

    async def worker(emo):
        async with sem:
            try:
                item = await asyncio.to_thread(_generate_one, refs, emo, style, out_dir)
                await q.put(("item", item))
            except Exception as e:
                await q.put(("error", {"key": emo.key, "message": str(e)}))

    async def runner():
        await asyncio.gather(*(worker(e) for e in ALL_EMOTIONS))
        await q.put(("__end__", None))

    async def event_stream():
        yield _sse("start", {"total": 32, "style": style})
        asyncio.create_task(runner())
        done = 0; items = []; errors = []
        while True:
            kind, payload = await q.get()
            if kind == "__end__": break
            done += 1
            if kind == "item":  items.append(payload);  yield _sse("item",  payload)
            else:               errors.append(payload); yield _sse("error", payload)
            yield _sse("progress", {"done": done, "total": 32})
        zip_path = build_zip(out_dir, {"items": items, "errors": errors})
        yield _sse("done", {"zip_url": f"/files/outputs/{session_id}/{zip_path.name}"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 7.2 Server-Sent Events 형식

SSE는 단순 텍스트 프로토콜이다. 한 이벤트당 두 줄:

```
event: progress
data: {"done": 7, "total": 32}

```

(마지막 빈 줄이 구분자)

### 7.3 클라이언트 측

```typescript
export function streamBatch(sessionId, style, onEvent) {
  const url = `/api/generate/batch?session_id=${sessionId}&style=${style}`;
  const es = new EventSource(url);
  ["start","item","progress","error","done"].forEach(name => {
    es.addEventListener(name, (ev) => {
      onEvent({ type: name, data: JSON.parse((ev as MessageEvent).data) });
      if (name === "done") es.close();
    });
  });
  return () => es.close();
}
```

### 7.4 ZIP + manifest

생성된 32 PNG + `manifest.json`을 묶음. manifest에는 세션 id,
화풍, 각 항목의 생성 소요시간(ms), 실패 목록까지 적어 재현 가능성 확보.

---

## 8장. 실행 검증 & 의존성 트러블슈팅

### 8.1 Python 3.14에서 깨진 것들

처음 핀을 박았던 버전들이 Python 3.14에서 wheel이 없어
**Rust로 소스 빌드를 시도하다 실패**했다. 교훈:

> Python 메이저 버전이 오르면 사전 컴파일된 wheel이 늦게 따라온다.
> 가능하면 **범위 표기**로 두고, 최소 버전만 보장하라.

| 패키지 | 문제 | 해결 |
| --- | --- | --- |
| `pydantic==2.9.2` | `pydantic-core` wheel 없음 → Rust 빌드 실패 | `pydantic>=2.11` |
| `Pillow==10.4.0` | rembg가 Pillow 12+ 요구 | `Pillow>=12.1,<13.0` |
| `onnxruntime==1.19.2` | 3.14 wheel 없음 | 핀 제거, 최신 자동 선택 |
| `google-genai==0.3.0` | 2.x로 메이저 점프된 라이브러리 | `>=1.0,<3.0` |

### 8.2 검증 절차

```bash
# 1) 모든 파이썬 파일 syntax check
python -c "import ast, pathlib;
[ast.parse(p.read_text('utf-8')) for p in pathlib.Path('app').rglob('*.py')]"

# 2) FastAPI app import + 라우트 dump
python -c "
from app.main import app
for r in app.routes:
    if hasattr(r, 'methods'): print(','.join(r.methods or []), r.path)
"

# 3) 실 서버 부팅 + 헬스체크
uvicorn app.main:app --port 8000 &
curl http://localhost:8000/api/health
```

---

## 9장. 원클릭 배치 실행 파일

3개 `.bat` 파일을 만들었다.

| 파일 | 역할 |
| --- | --- |
| `setup.bat` | 첫 1회: venv 생성 + pip + npm install |
| `start.bat` | 백엔드 + 프론트 새 콘솔로 분리 실행 + 브라우저 |
| `stop.bat` | 포트 8000/3000 점유 프로세스 종료 |

핵심 패턴: `start "PetMe Backend" cmd /k "..."` 로 별도 콘솔에 띄우고
제목으로 식별 → `taskkill /F /FI "WINDOWTITLE eq PetMe Backend*"` 로 종료.

> 이 단계까지만 해도 "실행 가능"하지만 일반 사용자에게는 여전히
> 콘솔창이 보이고 키 입력이 번거롭다. → **10·11장에서 GUI 도입.**

---

## 10장. API 키 GUI + Fernet 암호화

### 10.1 위협 모델

- 사용자는 `.env` 평문 파일을 그대로 두고 PC를 공유할 수 있다.
- 백업/실수로 git에 키가 올라갈 수 있다.
- 다른 사용자가 파일만 카피해 키를 빼낼 수 있다.

→ **외부(파일) + 내부(메모리) 양쪽에서 보호**가 필요.

### 10.2 Fernet — AES-128-CBC + HMAC-SHA256

```python
from cryptography.fernet import Fernet
import base64, hashlib, os, platform
from pathlib import Path

APP_SALT = b"PetMe-Moji::v1::do-not-change"

def _machine_fingerprint() -> bytes:
    parts = [
        platform.node(),
        os.environ.get("USERNAME") or os.environ.get("USER") or "",
        os.environ.get("COMPUTERNAME", ""),
        str(Path(__file__).resolve().parents[2]),  # 설치 경로
    ]
    return "|".join(parts).encode("utf-8")

def _fernet() -> Fernet:
    raw = hashlib.pbkdf2_hmac("sha256",
                              _machine_fingerprint(),
                              APP_SALT,
                              iterations=200_000,
                              dklen=32)
    return Fernet(base64.urlsafe_b64encode(raw))

def save_api_key(value: str):
    token = _fernet().encrypt(value.encode("utf-8"))
    (Path("storage") / "secrets.bin").write_bytes(token)

def load_api_key() -> str | None:
    try:
        return _fernet().decrypt(Path("storage/secrets.bin").read_bytes()).decode()
    except Exception:
        return None
```

### 10.3 검증

```text
[저장]   AIzaSyTEST-fake-key-1234567890abcdef
[디스크] 67 41 41 41 41 41 ...  ← 평문 'AIza' 발견 없음
[로드]   AIzaSyTEST-fake-key-1234567890abcdef  ← round-trip 성공
[USERNAME 변경]  복호화 실패 (None)  ← 머신 지문 검증 동작 ✓
```

> **핵심**: PBKDF2의 입력으로 머신 지문(호스트+사용자+경로)을 쓰기 때문에
> 파일만 다른 PC/계정으로 복사해서는 절대 풀 수 없다.

### 10.4 프로그램 내 암호화

`settings.gemini_api_key` 같은 전역에 평문을 두지 않는다.
**호출 직전에만** `secrets.get_api_key_required()` 호출 → 로컬 변수 →
함수 종료와 함께 폐기.

```python
def generate_emoticon(*, reference_paths, emotion_prompt, label_ko, style_key):
    api_key = secrets.get_api_key_required()  # ← 매 호출마다 디스크에서 복호화
    client = genai.Client(api_key=api_key)
    # ... 사용 후 함수 끝나면 자동 폐기
```

---

## 11장. Tkinter GUI 런처

`.bat` 파일은 콘솔창이 보인다. 일반 사용자에게는 부담스럽다.
Python 표준 라이브러리 **Tkinter** 로 GUI 런처를 만들었다.
의존성 추가 0개.

### 11.1 핵심 구조

```python
class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🐾 PetMe-Moji 런처")
        self.procs = {"backend": None, "frontend": None}
        self.log_queue = queue.Queue()
        self._build_ui()
        self._refresh_status()
        self.after(2000, self._tick_status)  # 2초마다 상태 갱신
```

### 11.2 상태 자동 진단

- Python 버전, Node 버전 (`shutil.which`)
- venv 존재 여부 (`VENV_PY.exists()`)
- node_modules 존재 여부
- API 키 등록 여부 (`secrets.bin` 존재)
- 백엔드/프론트엔드 포트 사용 여부 (`socket.connect_ex`)

이 모든 걸 2초마다 폴링해서 상태 행에 표시 + 버튼 활성/비활성 자동 제어.

### 11.3 서브프로세스 출력 스트리밍

```python
def _spawn(self, cmd, cwd, tag, shell=False):
    p = subprocess.Popen(cmd, cwd=cwd, shell=shell, text=True, bufsize=1,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         encoding="utf-8", errors="replace",
                         **_no_window_kwargs())  # 12장에서 추가
    threading.Thread(target=self._reader, args=(p, tag), daemon=True).start()
    return p

def _reader(self, p, tag):
    for line in p.stdout:
        self.log_queue.put((line, tag))
    p.wait()
    self.log_queue.put((f"({tag}) 종료 (exit {p.returncode})", "info"))
```

GUI 스레드는 100ms 마다 큐를 비워 텍스트 위젯에 색상 태그로 출력.

---

## 12장. 게이트 화면 + 실시간 대시보드 + 콘솔 숨김

### 12.1 첫 화면 API 키 게이트

키가 없으면 메인 UI 자체를 막아버린다 — 사용자가 헤맬 여지 0.

```tsx
export function ApiKeyGate({ onReady, children }) {
  const [status, setStatus] = useState(null);
  useEffect(() => {
    getKeyStatus().then(s => { setStatus(s); if (s.configured) onReady(s); });
  }, []);
  if (!status) return <Loading/>;
  if (status.configured) return <>{children}</>;
  return <KeyInputScreen onSaved={onReady} />;
}
```

저장 직후 **자동으로 검증 API**(`POST /api/settings/key/verify`)를 호출 →
실제 인증되는지 확인 후에야 메인으로 전환.

### 12.2 실시간 진행률 대시보드

세 카드 + 활동 로그:

1. **원형 진행률** — SVG ring, 부드러운 strokeDasharray 애니메이션
2. **통계** — 완료/실패/경과/장당평균/**ETA** (1초마다 재계산)
3. **시간별 스파크라인** — 시작→현재를 40 버킷으로 나눠 누적 완료 곡선
4. **활동 로그** — SSE 이벤트를 시간순으로 색상 코딩

ETA 계산:

```typescript
const avgMsPerItem = done > 0 ? elapsed / done : 0;
const eta = (total - done) * avgMsPerItem;
```

`useTick` 훅으로 1초마다 강제 리렌더:

```typescript
function useTick(intervalMs: number, enabled: boolean) {
  const [, setN] = useState(0);
  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => setN(x => x + 1), intervalMs);
    return () => clearInterval(id);
  }, [enabled, intervalMs]);
}
```

### 12.3 콘솔창 완전 숨김

Windows에서 `subprocess`는 기본적으로 검은 창을 띄운다.
두 가지 플래그를 같이 줘야 깔끔하다:

```python
CREATE_NO_WINDOW = 0x08000000

def _no_window_kwargs() -> dict:
    kw = {"creationflags": CREATE_NO_WINDOW}
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kw["startupinfo"] = si
    return kw
```

`PetMe.bat`도 `pythonw.exe`(콘솔 없는 파이썬)로 런처를 띄우므로
**처음부터 끝까지 검은 창이 한 번도 안 보인다.**

---

## 13장. 런처에서 직접 키 등록

브라우저 UI까지 가지 않고 런처에서 바로 키를 넣고 싶다는 요청.
한 가지 까다로움이 있다 — **런처는 시스템 Python으로 도는데,
`cryptography`는 venv에만 깔려 있다.**

해법: **venv Python을 subprocess로 호출**해 백엔드의 `secrets` 모듈을
직접 실행. 동일한 Fernet 암호화 그대로 사용.

```python
def _save_key_thread(self, key: str):
    code = (
        "import sys; sys.path.insert(0, '.'); "
        "from app.services.secrets import save_api_key; "
        "save_api_key(sys.argv[1]); print('OK')"
    )
    subprocess.run([str(VENV_PY), "-c", code, key],
                   cwd=str(BACKEND), capture_output=True, text=True,
                   timeout=15, **_no_window_kwargs())
```

- 키는 명령행 인자로 전달 (`sys.argv[1]`) → 환경변수보다 깔끔
- 콘솔창 숨김 플래그 그대로 적용
- 실패 시 stderr를 로그 영역에 그대로 표시

---

## 14장. 런처에서 사진 선택 + 자동 업로드

### 14.1 두 슬롯 (인물 / 반려동물)

```python
for key, ko in [("person", "① 인물"), ("pet", "② 반려동물")]:
    r = tk.Frame(photo_box); r.pack(fill="x")
    tk.Label(r, text=ko, width=10).pack(side="left")
    lbl = tk.Label(r, text="(선택 안 됨)"); lbl.pack(side="left", fill="x", expand=True)
    self.photo_labels[key] = lbl
    tk.Button(r, text="📁 찾아보기", command=lambda k=key: self.do_pick_photo(k)).pack(side="left")
    tk.Button(r, text="📷 촬영",   command=self.do_open_camera).pack(side="left")
    tk.Button(r, text="지우기",     command=lambda k=key: self.do_clear_photo(k)).pack(side="left")
```

### 14.2 카메라 — Windows 카메라 앱 UWP 프로토콜

OpenCV 같은 무거운 의존성을 도입하지 않고, Windows가 이미 갖고 있는
카메라 앱을 그대로 띄운다:

```python
os.startfile("microsoft.windows.camera:")
```

촬영 후 사용자는 다시 `📁 찾아보기`로 사진을 선택. 두 단계지만 OS 수준
무료 솔루션이다.

### 14.3 [2) 시작] 시 자동 업로드

```python
def open_browser_when_ready():
    # 백엔드 + 프론트 응답 대기
    for _ in range(60):
        if port_open(BACKEND_PORT) and port_open(FRONTEND_PORT): break
        time.sleep(0.5)

    url = FRONTEND_URL
    person, pet = self.photo_paths["person"], self.photo_paths["pet"]
    if person and pet:
        sid = self._upload_via_api(person, pet)   # venv 파이썬 + requests
        if sid: url = f"{FRONTEND_URL}/?session={sid}"

    webbrowser.open(url)
```

`_upload_via_api`도 13장과 같은 패턴 — venv Python으로
`requests.post(..., files={...})` 을 실행.

### 14.4 프론트엔드에서 세션 복구

URL 쿼리에 `?session=xxx` 가 있으면 `GET /api/upload/{sid}` 로
미리보기를 받아 와 상태 복구.

```typescript
useEffect(() => {
  const sid = new URLSearchParams(window.location.search).get("session");
  if (sid) getUploadSession(sid).then(setUpload);
}, []);
```

**최종 사용자 경험**

1. PetMe.bat 더블클릭
2. 런처 GUI: API 키 입력 + [암호화 저장] + 사진 2장 [📁 찾아보기]
3. [2) 시작]
4. 브라우저 자동 오픈 — 키 화면 통과, 누끼 미리보기까지 완료
5. 화풍 선택 → [생성 시작] → 32장 실시간 생성 → ZIP

---

## 부록 A. 전체 폴더 구조

```
petme/
├── PetMe.bat                       ← 더블클릭 진입점 (pythonw)
├── launcher.py                     ← Tkinter GUI 런처
├── setup.bat / start.bat / stop.bat ← 백업 진입점
├── README.md
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── .env / .env.example
│   ├── .venv/                      ← Python 가상환경
│   └── app/
│       ├── main.py                 ← FastAPI 앱 + CORS + 정적 마운트
│       ├── config.py               ← Settings (.env 로드)
│       ├── routers/
│       │   ├── upload.py           ← POST/GET /api/upload
│       │   ├── emotions.py         ← GET /api/emotions
│       │   ├── generate.py         ← single / batch(SSE) / regenerate
│       │   └── settings.py         ← API 키 CRUD + verify
│       ├── services/
│       │   ├── images.py           ← rembg, fit_square, save_png_optimized
│       │   ├── gemini.py           ← Gemini 호출 + 프롬프트 빌드
│       │   ├── packaging.py        ← ZIP + manifest
│       │   └── secrets.py          ← Fernet 암호화 (머신 지문 PBKDF2)
│       ├── prompts/
│       │   └── emotions.py         ← 32종 감정 데이터
│       └── storage/
│           ├── uploads/{session}/  ← 누끼 미리보기
│           ├── outputs/{session}/  ← 생성된 32 PNG + manifest + ZIP
│           └── secrets.bin         ← 암호화된 API 키 (gitignored)
│
├── frontend/
│   ├── package.json
│   ├── next.config.js              ← /api /files proxy → :8000
│   ├── tailwind.config.js
│   ├── lib/api.ts                  ← fetch 헬퍼 + SSE
│   └── app/
│       ├── layout.tsx
│       ├── page.tsx                ← 메인 화면 (게이트로 감쌈)
│       ├── globals.css
│       └── components/
│           ├── ApiKeyGate.tsx      ← 첫 화면 (키 없으면 잠금)
│           ├── ApiKeyModal.tsx     ← 메인에서 다시 열 수 있는 모달
│           ├── UploadCard.tsx
│           ├── EmoticonGrid.tsx
│           └── ProgressDashboard.tsx
│
└── docs/
    └── BUILD_JOURNAL.md            ← 이 문서
```

---

## 부록 B. 명령어 치트시트

### 사용자 입장

```text
1. PetMe.bat 더블클릭
2. 런처에서 API 키 입력 → 암호화 저장
3. 사진 2장 선택 → [2) 시작]
4. 브라우저 자동 오픈 → 화풍 선택 → 32종 생성
5. ZIP 다운로드 → 카카오 이모티콘 스튜디오에 제출
```

### 개발자 입장

```powershell
# 의존성 설치
cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..\frontend; npm install

# 서버 직접 실행
cd backend; .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

cd frontend; npm run dev

# 라우트 dump
.\.venv\Scripts\python.exe -c "from app.main import app; [print(r.path) for r in app.routes]"

# 암호화 round-trip 테스트
.\.venv\Scripts\python.exe -c "
from app.services.secrets import save_api_key, load_api_key
save_api_key('test123'); print(load_api_key())
"
```

---

## 부록 C. 배운 점 정리

### 1. 기획서를 그대로 구현하지 말 것

SAM 대신 rembg, LoRA 대신 Gemini multi-image. **각 컴포넌트의 최소
충분 기술**을 고르는 것이 일정의 80%를 좌우한다.

### 2. AI 페어 프로그래밍은 "결정"을 사람이 한다

플랫폼 4가지, AI 백엔드 4가지를 한 번에 질문해서 답을 받은 뒤 진행 →
이후 코드 결정에는 흔들림이 없었다. 처음에 묻지 않으면 두 번 만든다.

### 3. 검증 사이클을 짧게

각 단계 끝마다:
- Python `ast.parse` 전수 검사
- FastAPI app import + 라우트 dump
- 실제 HTTP 호출
- TS `tsc --noEmit`

이 네 가지로 1분 안에 큰 회귀를 잡았다.

### 4. 의존성 핀은 "범위"로

`X==1.2.3` 보다 `X>=1.2,<2.0` 이 미래의 자신을 살린다.
Python 메이저 점프(3.13→3.14)는 wheel 가용성을 흔든다.

### 5. 비밀은 두 군데에서 막는다

디스크 = Fernet + PBKDF2(머신 지문)
메모리 = 전역 변수 금지, 함수 로컬에서만 사용 후 폐기
이 둘을 같이 적용해야 "프로그램 내·외 암호화"가 완성된다.

### 6. 콘솔창은 끝까지 적이다

`pythonw.exe` + `CREATE_NO_WINDOW` + `STARTUPINFO.wShowWindow=SW_HIDE`
**세 가지를 모두** 적용해야 npm·uvicorn·taskkill까지 전부 조용해진다.

### 7. 마지막 1마일 — 자동 업로드

기능적으로 "사진은 브라우저에서 업로드"여도 동작은 한다. 하지만
런처에서 한 번에 끝낼 수 있게 만드는 것이 **사용자 경험의 마지막 1마일**이다.
HTTP 호출을 별도 프로세스(venv python + requests)로 빼는 작은 결정이
시스템 Python에 의존성을 끌어들이지 않는 깔끔한 분리를 만든다.

---

## 제2부 — 실전 피드백 반영

여기까지가 "사용자에게 처음 전달한" 버전이다.
이제부터는 실제로 돌려보면서 발견된 문제들을 하나씩 해결하는 진짜 디버깅
일지다. 코드를 한 번에 잘 만드는 게 아니라, **잘못된 가정을 빨리 찾아
빠르게 고치는 사이클**이 어떻게 굴러가는지를 보여준다.

---

## 15장. API 키 — 표시·기억·검증의 세 가지 함정

### 15.1 사용자 보고

> "키를 저장했는데 다음 실행에 사라져요. 그리고 저장됐는지 알기 어렵네요."

### 15.2 진단

`secrets.bin`은 디스크에 잘 저장됐다. 문제는 **UI 상태가 키 존재 여부를
반영하지 않는 것**. 저장 후 입력칸이 비워졌고, 재실행 시에도 비어 있어서
"안 저장된 것처럼 보임".

### 15.3 해결 — 3-상태 머신

```python
self.key_state: str = "saved" if SECRETS_BIN.exists() else "none"
# none    : 미등록    → 빈칸 + [암호화 저장]
# saved   : 저장됨    → "●●●●…   ✓ 저장됨" 읽기전용 + [새 키로 변경]
# editing : 입력 중   → 빈칸 + [암호화 저장] (saved에서 [변경] 누른 직후)

def _apply_key_state(self):
    e = self.key_entry
    e.configure(state="normal", show="")  # Tcl `show` 잔류 방지를 위해 먼저 풀기
    e.delete(0, "end")
    if self.key_state == "saved":
        e.insert(0, "●" * 28 + "   ✓ 저장됨 (이 PC에서만 복호화 가능)")
        e.configure(state="readonly", readonlybackground="#f0fdf4", fg="#15803d")
        self.btn_key_save.configure(text="🔄 새 키로 변경")
    else:
        e.configure(show="●")
        ...
```

**교훈**: 위젯 상태 변경이 여러 속성에 걸쳐 있을 때 (`state`, `show`,
`fg`, `bg`...) "한 번에 모두 풀고 다시 세팅"하는 idempotent 함수로
캡슐화한다. 부분 갱신은 Tcl/Tk가 잔류 속성을 안 지워서 디버깅 지옥.

### 15.4 두 번째 보고

> "키를 넣었는데 `API key not valid` 에러가 나요."

길이가 53자. 표준 Gemini 키는 `AIzaSy`로 시작하는 39자.

### 15.5 진단 — 디스크에 뭐가 들었는지 직접 본다

```bash
.venv/Scripts/python.exe -c "
from app.services.secrets import load_api_key, mask
k = load_api_key()
print('길이:', len(k))
print('마스킹:', mask(k))
print('AIza?:', k.startswith('AIza'))
"
```

결과: 길이 53, `AQ.A...-Iyg`, AIza? **False**.

**`AQ.A`는 OAuth 액세스 토큰 형식.** 사용자가 AI Studio가 아닌 다른
곳에서 키를 복사했거나, 키 외의 텍스트까지 붙여넣은 것.

### 15.6 두 가지 방어 추가

**1) 붙여넣기 오염 방지 — 공백/non-ASCII 완전 제거**

```python
def _sanitize_key(value: str) -> str:
    """탭, 줄바꿈, NBSP(U+00A0), 제로폭 공백(U+200B)까지 전부 제거."""
    return "".join(c for c in value if c.isascii() and not c.isspace())
```

테스트:
| 입력 | 출력 |
|---|---|
| `"  AIza...key  "` (앞뒤 공백) | `"AIza...key"` |
| `"AIza\nkey"` (개행) | `"AIzakey"` |
| `"AIza​key"` (제로폭) | `"AIzakey"` |
| `"AIza key"` (NBSP) | `"AIzakey"` |

**2) 저장 직후 자동 검증 + 진단**

저장 성공 직후 venv Python으로 `genai.Client(...).models.list()`를
호출해 Google이 실제로 키를 받아들이는지 확인. 실패하면 **저장된 키의
길이/접두사까지 함께 표시**해서 사용자가 즉시 무엇이 잘못됐는지 알게 한다.

```
📋 저장된 키 진단: 길이=53자, AIza 접두사=X, 마스킹=AQ.A...-Iyg
⚠ 키 길이가 비정상입니다. 표준 Gemini 키는 보통 39자입니다.
✗ 검증 실패: API key not valid.
💡 진단: 저장된 키 길이가 53자입니다. 표준 Gemini 키는 보통 39자라
    키가 잘못 복사됐을 가능성이 큽니다.
```

**교훈**: 사용자가 "키가 안 돼요"라고 했을 때
"어떻게 안 되냐"를 다섯 번 묻는 대신, **자동으로 진단해서 답을
같이 출력하라**. 진단 코드는 디버깅이 끝나도 영구히 남는다 — 다음 사용자가
같은 함정에 빠질 때도 똑같이 도와준다.

---

## 16장. 글자가 깨진다 — Gemini의 비라틴 문자 한계

### 16.1 사용자 보고

> "32장 중 절반의 한글이 깨져요. `안녕→안념`, `돈 좋아→돈 쫗아`,
> `망했다→망헲타`. 모양은 한글인데 글자가 틀려요."

### 16.2 진단

Gemini 2.5 Flash Image는 텍스트를 **픽셀 단위로 그린다** — OCR된 글자를
폰트로 합성하는 게 아니라 매번 새로 그려낸다. 라틴 문자는 학습량이
충분해서 그럭저럭 맞추지만, **한글·일본어·중국어·아랍어** 같은 비라틴
문자는 형태가 비슷한 다른 글자가 자주 섞인다. **모델의 근본적 한계**라
프롬프트로는 해결 불가.

### 16.3 해결 — 그림은 AI, 글자는 PIL

**역할 분리**:

```
Gemini : 인물 + 펫 + 감정 → 텍스트 없는 그림
   ↓
rembg  : 배경 한 번 더 누끼
   ↓
PIL    : 360x360 정사각 패딩
   ↓
PIL    : 맑은 고딕 Bold + 외곽선으로 한글 캡션 합성  ← 신규
```

핵심 코드 (`services/text_overlay.py`):

```python
FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgunbd.ttf",       # 맑은 고딕 Bold (Win 기본)
    "C:/Windows/Fonts/malgun.ttf",         # 맑은 고딕
    "C:/Windows/Fonts/NanumGothicBold.ttf",
]

def overlay_caption(img: Image.Image, text: str) -> Image.Image:
    w, h = img.size
    target_width = int(w * 0.78)
    size = int(h * 0.18)  # 캔버스 18%에서 시작
    font = _find_font(size)
    text_w, _ = _measure(font, text)
    # 가로 78% 안에 들어올 때까지 사이즈 감소
    while text_w > target_width and size > 24:
        size -= 4
        font = _find_font(size)
        text_w, _ = _measure(font, text)

    x = (w - text_w) // 2
    y = max(8, int(h * 0.06))
    stroke = max(3, size // 10)
    draw = ImageDraw.Draw(img)
    draw.text((x, y), text, font=font,
              fill=(20, 20, 20, 255),               # 검정 글자
              stroke_width=stroke,
              stroke_fill=(255, 255, 255, 255))     # 흰색 외곽선
    return img
```

그리고 Gemini 프롬프트는 텍스트를 **완전히 금지**:

```python
"TEXT: ABSOLUTELY DO NOT INCLUDE ANY TEXT, LETTERS, CAPTIONS, WORDS, "
"NUMBERS, OR SPEECH BUBBLES with text inside. No Korean, English, or any "
"language. Keep the TOP 25% of the image visually clear/uncluttered "
"(no faces or important details there) — caption will be added later by post-processing."
```

상단 25%를 비워두라고 명시해서 합성 시 얼굴을 가리지 않게 한다.

**교훈**: AI 모델의 약점이 명확하면 **그 부분만 빼서 결정적(deterministic)
도구로 처리**한다. 모델에 더 많은 프롬프트로 압박하는 것보다 훨씬 안정적이다.
"AI에 모든 걸 맡기지 말고, AI가 잘하는 것만 맡겨라."

### 16.4 보너스 — 사용자 환경 가정 줄이기

`FONT_CANDIDATES`에 Windows 맑은 고딕, NanumGothic, macOS Apple SD Gothic까지
세 환경의 폴백 경로를 모두 넣었다. 어디서 돌리든 한글이 깨지지 않는다.

---

## 17장. 한 번의 실수 — 사진 선택 패널의 추가와 제거

### 17.1 추가 (요청 1)

> "런처 첫 화면에서 사진 2장을 넣을 수 있게 [찾아보기] / [촬영] 버튼."

런처에 사진 슬롯 2개를 추가하고, Windows 카메라 앱을 UWP 프로토콜로 띄우는
기능까지 완성:

```python
os.startfile("microsoft.windows.camera:")  # Windows 기본 카메라
```

`[2) 시작]` 시 자동 업로드까지 구현 — venv Python으로 `requests` 모듈을
호출해 multipart POST → 세션 ID 받고 → 브라우저는 `?session=` 으로 오픈.

프론트는 URL 쿼리를 읽어 누끼 미리보기까지 자동 복원.

### 17.2 제거 (요청 2)

> "사진은 웹에서 올리면 되니까 런처의 사진 패널은 빼주세요."

3시간 들여 만든 기능을 한 줄로 거둬들이는 순간. 그래도 거둬들였다.

**교훈**:

- **만든 기능에 미련 갖지 말 것.** 사용자가 안 쓰면 만든 의미가 없다.
  유지보수 비용은 0이 아니라 영원하다.
- **이 정도로 큰 제거가 한 커밋에 들어가는 게 정상이다.** 좋은 추상화로
  만들었다면 (런처와 백엔드가 결합되어 있지 않았다면) 제거도 깔끔하다.

남은 흔적은 백엔드의 `GET /api/upload/{session_id}` 한 줄 — 이건 향후
다른 세션 복원 기능에 재활용될 수 있어 남겨뒀다.

---

## 18장. 503 오류 — 일시적 장애를 자동 복구로

### 18.1 사용자 보고

```
[21:01:22] ✓ 망했다... (16.0초, 110KB)
[21:01:22] ✗ 간식 주세요 실패 — 503 UNAVAILABLE.
           'This model is currently experiencing high demand.'
```

### 18.2 진단

- "동작 중이냐 멈춘 거냐"는 사용자의 자연스러운 질문.
- 같은 시각에 한 칸은 성공, 한 칸은 503. **앱이 멈춘 게 아니라
  Gemini 서버가 일시적으로 거부한 것**.
- 그런데도 사용자 입장에선 "왜 한 장 빠졌지?" 가 됨.

### 18.3 해결 — 지수 백오프 자동 재시도

```python
TRANSIENT_MARKERS = (
    "503", "unavailable", "high demand", "overloaded",
    "429", "rate limit", "quota", "resource_exhausted",
    "deadline", "timeout",
)
MAX_RETRIES = 3
BACKOFF_SECONDS = (1.0, 3.0, 7.0)  # 1s → 3s → 7s

for attempt in range(MAX_RETRIES + 1):
    try:
        response = client.models.generate_content(...)
        break
    except Exception as e:
        msg = str(e).lower()
        transient = any(m in msg for m in TRANSIENT_MARKERS)
        if not transient or attempt >= MAX_RETRIES:
            raise
        time.sleep(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
```

**왜 지수 백오프인가**: 첫 실패 후 즉시 재시도하면 서버 부하에 기여만
한다. 1→3→7초로 늘려 서버에 회복 시간을 주면서, 동시에 본인의 비용도
지출(돈 + 시간)을 최소화한다.

**키워드 기반 분류**가 핵심이다. 모든 예외를 재시도하면 "잘못된 API 키"
같은 영구적 오류까지 3번씩 호출하게 된다. **일시적 vs 영구적**을
분리하는 게 비용 폭주를 막는다.

**교훈**: API 호출은 항상 두 가지를 같이 갖춰야 한다 —
(1) **일시적 오류의 자동 재시도** + (2) **재시도가 무의미한 오류의 즉시 실패**.
사용자 시점에서는 "그냥 잘 됨"으로 보인다.

---

## 19장. 진행률을 사람에게 보여주는 법

### 19.1 사용자 보고

> "한 번 32장 처리하니 시간이 많이 걸리고 진행 상황 예측하기 힘들어요.
> 2~3장씩 만들고 진행 상황 그래프와 %를 동기화해주세요."

### 19.2 진단

기술적으로는 이미 SSE로 실시간 스트리밍 중이고 진행률 바도 있다.
그런데도 "예측하기 힘들다". 왜?

→ 사용자는 "**지금 무엇이 처리되고 있는지**"를 알고 싶다. "n/32"만으로는
부족하다. 작업이 살아있다는 **모션**이 필요하다.

### 19.3 해결 — 세 가지 변경

**1) 동시성 4 → 3**

```python
CONCURRENCY = 3  # was 4
```

같은 시각에 처리되는 항목 수를 줄여서 "한 번에 너무 많이 빠르게 끝나서
무엇이 무엇인지 안 보임"을 완화. 503 발생률도 같이 떨어진다.

**2) `item_start` SSE 이벤트 추가**

이전엔 완료/실패만 알렸지만, 이제 **워커가 작업을 잡는 순간**에도 이벤트를 보낸다:

```python
async def worker(emo):
    async with sem:
        await queue.put(("item_start", {"key": emo.key, "label_ko": emo.label_ko}))
        ...
```

**3) 프론트: "지금 처리 중" 칩 패널**

`inFlight` 상태(완료 안 된 것 전체가 아닌, **워커 슬롯에 있는 것**)를
별도로 추적해 분홍 칩으로 표시 + 깜빡이는 점:

```tsx
{currentlyProcessing.length > 0 && (
  <div className="bg-pink-50 border border-pink-200 rounded-2xl p-4">
    <div className="text-xs font-semibold text-pink-700">
      <span className="inline-block w-2 h-2 rounded-full bg-pink-500 animate-pulse" />
      지금 동시에 처리 중 ({currentlyProcessing.length}개)
    </div>
    <div className="flex flex-wrap gap-2">
      {currentlyProcessing.map((label) => (
        <span key={label} className="px-3 py-1.5 rounded-full bg-white border border-pink-300">
          {label}
        </span>
      ))}
    </div>
  </div>
)}
```

### 19.4 사용자 시점

```
0초:    원형 0%   처리 중: [안녕!] [잘 가~] [고마워]      활동: ▷ 시작
~15초:  원형 3%   처리 중: [안녕!] [잘 가~] [미안해]      활동: ✓ 고마워
~30초:  원형 6%   처리 중: [잘 가~] [미안해] [축하해!]    활동: ✓ 잘 가~
...
```

% 게이지가 **매 워커 사이클마다** 움직이고, 분홍 칩이 회전하면서 무엇이
진행 중인지 한눈에 보인다. 멈춘 느낌이 사라진다.

**교훈**: "진척률 X%"보다 "**지금 무엇이**"가 더 중요하다.
숫자보다 라벨이, 라벨보다 움직이는 라벨이 사람에게 안정감을 준다.

---

## 제2부 부록 — 변경 파일 요약

| 파일 | 변경 요약 |
| --- | --- |
| `backend/app/services/secrets.py` | `_sanitize_key()` 추가 (공백/non-ASCII 제거) |
| `backend/app/services/text_overlay.py` | **신규** — 한글 PIL 합성 |
| `backend/app/services/gemini.py` | 텍스트 금지 프롬프트, 503 재시도, `normalize_to_emoticon(label_ko=...)` |
| `backend/app/routers/generate.py` | `CONCURRENCY=3`, `item_start` 이벤트, `percent` 필드 |
| `backend/app/routers/upload.py` | `GET /api/upload/{session_id}` (세션 복원용) |
| `launcher.py` | API 키 3-상태 머신, 자동 검증, 키 진단, 사진 패널 제거 |
| `frontend/lib/api.ts` | `item_start` 이벤트 타입, `getUploadSession()` |
| `frontend/app/page.tsx` | `inFlight` 분리, `syncedFromLauncher` 배지 |
| `frontend/app/components/ProgressDashboard.tsx` | "지금 처리 중" 칩 패널 |
| `frontend/app/components/ApiKeyGate.tsx` | **신규** — 풀스크린 키 게이트 |

---

## 제2부 회고 — 8가지 추가 교훈

1. **위젯 상태는 idempotent 함수로 일괄 갱신**. 부분 갱신은 잔류 속성으로
   디버깅 지옥을 만든다.
2. **사용자가 "안 돼요"라고 하면 진단 코드를 자동으로 출력**시켜라.
   디버깅이 끝나도 그 코드는 영구히 다음 사용자를 돕는다.
3. **AI에 모든 걸 맡기지 말고 약점은 결정적 도구로 보강**. (한글 → PIL)
4. **API 호출은 일시 오류 재시도 + 영구 오류 즉시 실패**. 키워드 기반
   분류가 비용 폭주를 막는다.
5. **"진척률 X%" < "지금 무엇이 처리 중"**. 숫자보다 움직임.
6. **만든 기능에 미련 갖지 말 것**. 안 쓰는 기능은 유지보수 비용 ∞.
   추상화가 잘 됐다면 제거도 깔끔하다.
7. **공백 sanitize는 trim 한 줄로 끝나지 않는다**. NBSP, 제로폭 공백,
   탭, 개행 — 모두 보이지 않는 적이다.
8. **사용자 환경에 가정을 두지 마라**. Windows 맑은 고딕만 가정하면
   macOS에서 깨진다. 폴백 경로를 미리 열어둬라.

---

**이 책은 살아있다.** 이후로 추가할 가능성:

- 20장. 화풍 변환 LoRA 미세조정 (Replicate)
- 21장. 모바일 PWA 래핑 + 카메라 직접 촬영
- 22장. 카카오톡 자동 제출 워크플로
- 23장. 다국어(영문/일문 라벨) 지원
- 24장. 사용량 통계 / 비용 추적 대시보드

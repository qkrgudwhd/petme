# 🐾 PetMe-Moji

> **내 사진 + 반려동물/식물/사물 사진 → 카카오톡 이모티콘 32종 자동 생성**
> 한 번 설치하고 클릭 한 번이면 끝. Google Gemini AI 사용.

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](#)
[![Node](https://img.shields.io/badge/Node.js-18+-green.svg)](#)
[![Windows](https://img.shields.io/badge/Platform-Windows-blue.svg)](#)

## ✨ 무엇을 하나요

- 사진 2장(인물 + 어떤 피사체든)을 업로드하면 **카카오톡 이모티콘 32종 + 키보드 아이콘** 자동 생성
- **AI가 사진을 보고** 종류(강아지/고양이/식물/인형/음식 등)를 자동 인식
- **피사체에 맞는 한글 라벨**을 동적으로 만들어줌 (푸들→"왈왈안녕!", 선인장→"뾰족안녕!")
- 6가지 화풍 선택: 2D 카툰 / 수채화 / 파스텔 / 웹툰 / 픽셀아트 / 팝아트
- 카카오톡 스튜디오 규격으로 **즉시 제출 가능한 ZIP** 패키징

## 📥 다운로드

| 출처 | 링크 |
|---|---|
| **GitHub Releases** | [최신 버전 다운로드](https://github.com/YOUR_GH/petme-moji/releases/latest) |
| **Google Drive** | [공유 링크](#) |

다운받은 `PetMe-Moji-source.zip` 을 원하는 폴더에 압축 해제하면 끝.

## 🔧 사전 요구사항

- **Windows 10/11**
- **Python 3.11 이상** — https://www.python.org/downloads/ (설치 시 "Add to PATH" 체크)
- **Node.js 18 이상** — https://nodejs.org/
- **Google AI Studio API 키** — https://aistudio.google.com/apikey (무료 발급)

## 🚀 사용법 (3단계)

### 1️⃣ 첫 1회만 — 설치

`setup.bat` 더블클릭 → 3~5분 대기 (백엔드 venv + 프론트엔드 npm install)

### 2️⃣ 매번 — 실행

`start.bat` 더블클릭 → 10초 후 브라우저 자동 오픈

### 3️⃣ 브라우저에서

```
첫 화면: Gemini API 키 입력 → [암호화 저장 & 검증]
  ↓ (다음 실행부터 자동 통과)
메인 화면:
  ├ 사진 2장 업로드 (인물 + 반려동물/식물/사물 등)
  │   → AI가 자동으로 종류 인식 + 32개 라벨 맞춤 생성
  ├ 화풍 선택 (6가지 중)
  └ [생성 시작]
      ↓
  실시간 32종 + 아이콘 생성 → [📦 ZIP 다운로드]
```

종료: `stop.bat` 더블클릭

## 💰 비용

- **Gemini API**: 32장 생성 ≈ **$1.25** (이미지 1장당 약 $0.039)
- **본 앱**: 무료, 광고 없음, 사용량 추적 없음
- 모든 API 호출은 **사용자 본인의 키**로 직접 Google에 청구됨

## 🔐 API 키 보안

- 저장 위치: `backend/app/storage/secrets.bin`
- **암호화**: Fernet (AES-128 + HMAC) + PBKDF2-SHA256(200k iter)
- **머신 지문 도출**: 호스트명·사용자명·설치경로 조합으로 키 생성
- **다른 PC로 파일 복사해도 복호화 불가**
- 변경/삭제: 메인 화면 우측 상단 ⚙ 버튼

## 🏗 기술 스택

- **Backend**: FastAPI · rembg(U2Net) · Pillow · cryptography
- **Frontend**: Next.js 14 · TypeScript · Tailwind
- **AI**: Google Gemini 2.5 Flash Image (이미지 생성) · Gemini 2.5 Flash (분류/라벨)

## 📋 카카오톡 이모티콘 스튜디오 규격 자동 준수

| 항목 | 32장 이모티콘 | 키보드 아이콘 |
|---|---|---|
| 사이즈 | 360×360 px | 78×78 px |
| 포맷 | PNG (투명배경) | PNG (투명배경) |
| 용량 | ≤ 650KB | ≤ 16KB |
| 수량 | 32장 | 1장 |

ZIP 안에 `stickers/`(32장), `icon.png`, `manifest.json`, `README.txt` 자동 패키징.

## ❓ 자주 묻는 질문

**Q. 인터넷 없이 되나요?**
A. 아니요. Google Gemini API를 호출하므로 인터넷 필요. 단, 사진은 사용자 PC에만 저장되고 외부 서버에 안 갑니다(키 외).

**Q. 다른 사람이 내 키를 훔칠 수 있나요?**
A. `secrets.bin` 파일은 이 PC의 머신 지문으로 암호화됐기 때문에 다른 PC에서 복사해 가도 풀리지 않습니다.

**Q. Mac/Linux에서 쓸 수 있나요?**
A. 백엔드는 가능, 배치 파일은 Windows 전용. 수동 명령(uvicorn / npm run dev)으로는 됩니다.

**Q. 카카오 외 플랫폼에도 쓸 수 있나요?**
A. 네. 생성된 360×360 PNG는 라인/네이버/페이스북 스티커 만들기에도 적용 가능.

## 🐛 문제 해결

| 증상 | 해결 |
|---|---|
| `start.bat` 더블클릭해도 아무 일 없음 | `setup.bat` 먼저 실행 |
| "API key not valid" | 키 형식 확인 (AIza…로 시작). 화면 ⚙에서 재입력 |
| Gemini 503 에러 | 자동 재시도됨. 그래도 실패 시 `[↻ 다시]` 버튼 |
| 한글이 깨져 보임 | Windows 명령창은 정상. 결과 이미지는 맑은 고딕 사용 |

## 📖 개발 일지

전체 개발 과정은 [docs/BUILD_JOURNAL.md](docs/BUILD_JOURNAL.md) 에 110쪽 분량으로 기록 (e-book 형식).

## 🤝 기여

이슈/PR 환영합니다. 코드는 MIT 라이선스입니다.

## 📜 라이선스

MIT — 자유롭게 사용·수정·재배포 가능.
API 사용료는 사용자 본인 부담입니다 ([LICENSE](LICENSE) 참조).

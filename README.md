# 🐾 PetMe-Moji

> **내 사진 + 반려동물/식물/사물 사진 → 카카오톡 이모티콘 32종 자동 생성**

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](#)
[![Node](https://img.shields.io/badge/Node.js-18+-green.svg)](#)
[![Android](https://img.shields.io/badge/Android-7.0+-green.svg)](#)
[![Play Store](https://img.shields.io/badge/Play_Store-심사중-blue.svg)](#)

---

## ✨ 주요 기능

- 📸 **사진 2장 → 카카오톡 이모티콘 32종 자동 생성**
  - 360×360 PNG, 투명배경, 650KB 이하 (카카오 규격 자동 준수)
- 🎨 **6가지 화풍**: 2D 카툰 / 수채화 / 파스텔 / 웹툰 / 픽셀아트 / 팝아트
- 🔍 **AI 자동 종 인식**: 강아지 / 고양이 / 토끼 / 햄스터 / 새 / 원숭이 / 식물 / 인형 / 사물 / 음식 / 캐릭터
- 🎭 **피사체 맞춤 라벨 자동 생성**
  - 푸들 → "왈왈안녕!", 부엉이 → "부엉부엉 안녕!", 선인장 → "뾰족안녕!"
- 🌈 **원본 색상 보존** — 옷·머리·털 색이 32장 모두 일관
- 📦 **키보드 메인 아이콘 78×78** 자동 생성
- 📥 **카카오톡 이모티콘 스튜디오 제출용 ZIP** 한 번에 다운로드

## 🛠 기술 스택

- **백엔드**: FastAPI + rembg + Pillow + Fernet 암호화 + Gemini 2.5 Flash Image
- **프론트엔드**: Next.js 14 + TypeScript + Tailwind + SSE
- **모바일**: Capacitor 8 → Android (AAB 3.2MB)
- **호스팅**: Render Free + GitHub Pages + UptimeRobot

## 🚀 설치 및 실행

### Windows PC (개발자/고급 사용자)

```bash
git clone https://github.com/qkrgudwhd/petme.git
cd petme

# 초기 설정 (1회만)
setup.bat

# 실행
start.bat

# 종료
stop.bat
```

브라우저가 자동으로 열림 → 첫 화면에서 Gemini API 키 입력 → 사진 2장 업로드 → 32종 생성.

### Android 폰 (일반 사용자)

📱 **Google Play Store에서 다운로드** (심사 통과 후)

```
https://play.google.com/store/apps/details?id=com.petmemoji.app
```

## 💰 비용

| 항목 | 비용 | 비고 |
|---|---|---|
| **앱 구매** | ₩3,300 (1회) | 평생 사용 |
| **Gemini API** | 무료 ~ ₩52/장 | 사용자 본인 부담 (BYOK) |
| **무료 한도** | 일 95장까지 비용 0원 | Google 무료 할당량 |

> 💡 32장 한 세트 생성 = 무료 한도 안에서 **비용 0원**

## 🔐 보안

- API 키는 **Fernet (AES-128 + HMAC)** 으로 암호화되어 기기에만 저장
- 기기 고유 정보(머신 지문)로 키 도출 → 다른 PC로 복사해도 복호화 불가
- 광고 / 추적 / 분석 없음
- 사진은 처리 완료 후 24시간 이내 자동 삭제

## 📚 문서

### 사용자용
- 📥 [DISTRIBUTE.md](docs/DISTRIBUTE.md) — 다운로드 + 설치 가이드
- 🔒 [privacy-policy.md](docs/privacy-policy.md) — 개인정보 처리방침

### 개발자용
- 📖 **[BUILD_JOURNAL.md](docs/BUILD_JOURNAL.md)** — **전체 빌드 저널 (220쪽 전자책)**
- 🚀 [PLAYSTORE.md](docs/PLAYSTORE.md) — Google Play 등록 가이드
- 📋 [PLAYSTORE_SUBMIT_DATA.md](docs/PLAYSTORE_SUBMIT_DATA.md) — Play Console 입력값
- 🦉 [KAKAO_EMOTICON_SUBMIT.md](docs/KAKAO_EMOTICON_SUBMIT.md) — 카카오톡 제출
- 🛡 [BACKEND_KEEPALIVE.md](docs/BACKEND_KEEPALIVE.md) — 백엔드 무중단 운영

전체 문서 인덱스: [docs/README.md](docs/README.md)

## 🎨 데모 — 박형종 + 부엉이

본 앱으로 직접 만든 32 부엉이 이모티콘 (개발자 본인 데모):

```
부엉부엉 안녕!    깜빡깜빡 잘 가~     고마부엉~        미안부엉..
🦉🎉 축하해!    내 맘 훔쳤부엉!     후후훗 ㅋㅋㅋ    흐규흐규..
부엉! 화났어!    부엉가 헐!!         빼꼼! 왔부엉!    부엉부엉!
남남 밥 줘!      밤 산책 가자!       간식 내놔라!     멍떼려부엉
하아풀~          꿀잠 부엉           흥! 빼졌부엉     사고친 부엉
이게 뭐부엉?     쓰담쓰담 해줘       내 머리 위 부엉! 망했부엉..
부엉부엉 파이팅! 부엉이 돈방식       퇴근하자 부엉.. 주말에 놀자~
하트 뽐뽐!       꼬옥 안아부엉       절대 안된다 부엉! 부엉 오케이!
```

→ AI가 "부엉" = 부엉이 울음소리임을 인식하고 32 라벨에 자연스럽게 적용. 차별점.

## 🤝 기여

이슈, 풀 리퀘스트 환영합니다.

- 버그 리포트: [Issues](https://github.com/qkrgudwhd/petme/issues)
- 기능 요청: [Discussions](https://github.com/qkrgudwhd/petme/discussions) (활성화 시)

## 📜 라이선스

MIT License — [LICENSE](LICENSE) 참조.

코드 자유 사용·수정·재배포 가능. 단, **API 사용료는 사용자 본인 부담**.

## 👤 개발자

**Auto365Blog · 박형종 (PARK HYUNGJONG)**
- 📧 phjcom3@gmail.com
- 🌐 [github.com/qkrgudwhd](https://github.com/qkrgudwhd)
- 📍 경상남도 김해시 주촌면 선지로 85, 105동 2103호 (50966)

---

## 🎬 만들기 과정

이 앱은 **AI(Claude) + 사람(박형종) 페어 프로그래밍으로 7시간 만에** 완성되었습니다.

기획서 한 장 → 풀스택 개발 → 클라우드 배포 → Android AAB 빌드 → Play Console 등록 → 심사 제출까지 전 과정은 [docs/BUILD_JOURNAL.md](docs/BUILD_JOURNAL.md) 에 220쪽 분량으로 기록되어 있습니다.

> "혼자서는 6개월 걸릴 작업이 AI와 함께 하루 만에 끝났다."

전자책으로 출판될 예정. 관심 있으신 분은 GitHub Watch ⭐.

---

*최종 업데이트: 2026-06-03 · v1.0*

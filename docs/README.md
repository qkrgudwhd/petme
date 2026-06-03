# 📚 PetMe-Moji 문서 인덱스

> **Auto365Blog · 박형종 (PARK HYUNGJONG)**
> phjcom3@gmail.com · [github.com/qkrgudwhd/petme](https://github.com/qkrgudwhd/petme)
> **Play Store**: `com.petmemoji.app` (심사 중)

---

## 🎯 빠른 안내 — 무엇을 찾으시나요?

### 🆕 처음 보신 분이라면

1. **앱 소개부터** → 프로젝트 루트의 [README.md](../README.md)
2. **앱 직접 써보기** → [DISTRIBUTE.md](DISTRIBUTE.md) (다운로드/설치)
3. **개발자라면 전체 과정** → [BUILD_JOURNAL.md](BUILD_JOURNAL.md) (220쪽 전자책)

### 🛠 작업별 가이드

| 하고 싶은 일 | 참고할 문서 |
|---|---|
| **Play Store 등록 진행 중** | [PLAYSTORE_SUBMIT_DATA.md](PLAYSTORE_SUBMIT_DATA.md) |
| **카카오톡 이모티콘 제출** | [KAKAO_EMOTICON_SUBMIT.md](KAKAO_EMOTICON_SUBMIT.md) |
| **백엔드 무중단 운영** | [BACKEND_KEEPALIVE.md](BACKEND_KEEPALIVE.md) |
| **앱 배포 + 사용자 설치** | [DISTRIBUTE.md](DISTRIBUTE.md) |
| **Play Store 일반 가이드** | [PLAYSTORE.md](PLAYSTORE.md) |
| **개인정보 처리방침** | [privacy-policy.md](privacy-policy.md) |

---

## 📖 문서 목록 (가나다순)

### BACKEND_KEEPALIVE.md (5KB, 206줄)

**Render 무료 티어 cold start 방지 가이드**

- UptimeRobot 설정 단계별 안내
- Render Free의 한계와 대응
- 가동률 모니터링 방법
- 대안 (Render Cron, Cron-Job.org)

> 🎯 추천 사용 시점: 출시 직후 또는 출시 전

---

### BUILD_JOURNAL.md ★ (80KB, 2,357줄)

**전자책 — AI 페어 프로그래밍으로 7시간 만에 풀스택 앱 출시**

기획서 한 장에서 시작해 Google Play 등록까지 전 과정을 기록한 220쪽 분량의 전자책.

**구성**:
- **제1부 (14장)** — 0에서 완성까지 (백엔드/프론트엔드/AI 연동)
- **제2부 (5장)** — 실전 피드백 반영 (한글 깨짐/503 오류/UX 개선)
- **제3부 (13장)** — 출시까지 (Render/Capacitor/Play Console/카카오톡)
- **부록 A~F** — 폴더 구조, 명령어, 체크리스트, 자산 인덱스, 비용 정산

> 🎯 추천 독자: AI 페어 프로그래밍, Android 출시, 1인 개발 관심자

> 📝 출판 가능: PDF/EPUB로 변환해 부크크/리디북스 등에 출판 가능

---

### DISTRIBUTE.md (3.5KB, 119줄)

**소스 배포 가이드 (GitHub Release / Google Drive)**

- 사용자가 ZIP을 다운로드해서 직접 실행하는 방식
- 백엔드 클라우드 배포 전 단계의 BYOD(Bring Your Own Device) 모델

> 🎯 추천 사용: 클라우드 호스팅 비용 없이 분배할 때

---

### KAKAO_EMOTICON_SUBMIT.md (10KB, 377줄)

**카카오톡 이모티콘 스튜디오 제출 가이드**

PetMe-Moji로 만든 32장 이모티콘을 카카오톡 이모티콘 상점에 출시하는 방법.

- 작가 등록 + 제안 제출 단계별
- 32장 순서 추천표
- 통과율 높이는 7가지 팁
- 이중 출시 전략 (Play Store + 카카오톡)

> 🎯 추천 사용 시점: Play Store 심사 대기 중 또는 출시 후 부수입 노릴 때

---

### PLAYSTORE.md (9KB, 246줄)

**Play Store 일반 등록 가이드**

처음부터 끝까지의 Google Play Console 등록 절차.

- 사전 준비물 체크리스트
- Capacitor + Android Studio + AAB 빌드
- Play Console 가입 ($25)
- 메타데이터 + 가격 + 출시 흐름

> 🎯 추천 사용: 가입 전 전체 그림 잡을 때

---

### PLAYSTORE_SUBMIT_DATA.md ★ (11KB, 389줄)

**Play Console 입력값 복사·붙여넣기용**

KYC 통과 후 30분~1시간 안에 모든 입력 끝낼 수 있게 정리된 데이터.

- 앱 이름, 짧은 설명, 자세한 설명 (한국어)
- 카테고리, 가격, 국가
- 콘텐츠 등급 / 데이터 보안 설문 답변
- 그래픽 자산 위치
- 단계별 체크리스트

> 🎯 추천 사용: KYC 통과 메일 받은 직후

---

### privacy-policy.md (5KB, 137줄)

**개인정보 처리방침 (한국어)**

- 수집 정보 / 이용 목적 / 제3자 제공
- 데이터 보안 (Fernet 암호화 설명)
- 사용자 권리 / 아동 정보 / 광고·추적 없음
- Auto365Blog · 박형종 · phjcom3@gmail.com

> 🌐 **호스팅 URL**: https://qkrgudwhd.github.io/petme/privacy-policy
>
> 🎯 추천 사용: Play Console "처리방침 URL" 항목에 입력

---

## 🎨 playstore-assets/ — 그래픽 자산 (10개)

```
playstore-assets/
├── app-icon-512.png              (12KB, 512×512)   앱 아이콘
├── feature-graphic-1024x500.png  (32KB, 1024×500)  피처 그래픽
├── screenshot-1-keygate.png      (300KB)           스크린샷 1: API 키 게이트
├── screenshot-2-main.png         (82KB)            스크린샷 2: 메인 (사진 업로드)
├── screenshot-3-generating.png   (1.3MB)           스크린샷 3: 생성 중 (0%)
├── screenshot-3b-half-done.png   (1.3MB)           스크린샷 4: 50% 진행
├── screenshot-4-result.png       (588KB)           스크린샷 5: 100% 완성 ★
├── screenshot-5-0-result.png     (213KB)           스크린샷 6: 결과 1
├── screenshot-5-1-result.png     (156KB)           스크린샷 7: 결과 2
└── screenshot-5-2-result.png     (254KB)           스크린샷 8: 결과 3
```

> 💡 모두 박형종 + 부엉이 조합으로 캡처. Play Store 등록 시 그대로 사용.

---

## 🔗 외부 링크 모음

| 종류 | URL |
|---|---|
| **GitHub 저장소** | https://github.com/qkrgudwhd/petme |
| **백엔드 API** | https://petme-moji-api.onrender.com |
| **처리방침** | https://qkrgudwhd.github.io/petme/privacy-policy |
| **Play Store (심사 후)** | https://play.google.com/store/apps/details?id=com.petmemoji.app |
| **카카오톡 이모티콘 스튜디오** | https://emoticonstudio.kakao.com |

---

## 📊 프로젝트 통계

```
📅 시작: 2026-06-02
📅 출시 제출: 2026-06-02
📅 책 완성: 2026-06-03

📦 코드: 약 6,000줄 (Python + TypeScript)
📚 문서: 약 4,000줄 (7개 마크다운)
🎨 자산: 10개 PNG (총 4.1MB)
📱 AAB: 3.2MB
🔑 키스토어: 2.6KB (3중 백업)

⏰ 개발 시간: 약 7시간 (AI 페어 프로그래밍)
💰 투자: $25 (Google Play Console 1회)
💸 월 운영비: $0 (Render Free + UptimeRobot Free)
```

---

## 🎯 출시 후 로드맵

```
Day 0:   심사 제출 (✅ 완료)
Day 1~7: Google 심사 대기
Day 7+:  🎉 출시!
   ↓
Week 2:  첫 사용자 데이터
Month 1: 영문 메타데이터 추가 (글로벌)
Month 2: 카카오톡 이모티콘 심사 결과
Month 3: 매출 정산 시작
   ↓
Year 1:  Build Journal 후속편 출판
```

---

## 📞 문의

- **이메일**: phjcom3@gmail.com
- **GitHub Issues**: https://github.com/qkrgudwhd/petme/issues
- **개발자**: 박형종 (PARK HYUNGJONG)
- **개발자명**: Auto365Blog
- **주소**: 경상남도 김해시 주촌면 선지로 85, 105동 2103호 (50966)

---

*최종 업데이트: 2026-06-03*

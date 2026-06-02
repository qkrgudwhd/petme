# Google Play Store 출시 가이드 (유료 앱, BYOK 모델)

> 본 가이드는 **PetMe-Moji를 유료 Android 앱으로 출시**하기 위한 절차를 정리합니다.
> 모델: 사용자가 1회 구매(약 ₩3,300) → 본인 Gemini API 키 입력 → 사용량은 사용자 본인 부담.

---

## ☑️ 사전 준비 체크리스트

- [ ] **Google Play 개발자 계정** ($25 1회) — https://play.google.com/console/signup
- [ ] **신용카드 + Google 결제용 본인 인증 (KYC)**
- [ ] **세금 정보 등록** (외국인 개발자라면 W-8BEN 등)
- [ ] **개인정보 처리방침 URL** (정적 HTML로 GitHub Pages 무료 호스팅 권장)
- [ ] **앱 아이콘 512x512 + 피처 그래픽 1024x500 + 스크린샷 최소 2장**
- [ ] **테스트 기기 Android 7.0+ 또는 에뮬레이터** (Android Studio)
- [ ] **PC에 Android Studio 설치** — https://developer.android.com/studio
- [ ] **백엔드 배포 완료** (docs/DEPLOY_BACKEND.md 참고)

---

## 1단계 — 백엔드 클라우드 배포 (Render free tier)

### 1-1. GitHub에 코드 push
프로젝트가 이미 [docs/DISTRIBUTE.md](DISTRIBUTE.md)대로 GitHub에 올라가 있어야 함.

### 1-2. Render 가입 + 배포
1. https://render.com/ 가입 (GitHub 계정으로 가능)
2. Dashboard → **New +** → **Blueprint**
3. 본인 GitHub 저장소 연결 → `petme-moji` 선택
4. Render가 자동으로 `render.yaml`을 감지 → **Apply**
5. 빌드 5~10분 소요 (rembg 모델 다운로드 포함)
6. 완료 후 URL 확인: `https://petme-moji-api-xxxx.onrender.com`

### 1-3. 동작 확인
```
curl https://petme-moji-api-xxxx.onrender.com/api/health
{"ok":true,"gemini_key_set":false,"model":"gemini-2.5-flash-image"}
```

### 1-4. 주의 — free tier 한계
- 15분간 요청 없으면 sleep → 첫 요청 시 ~30초 지연
- 월 750시간 무료 (1개 서비스 24/7 가능)
- 라이브 트래픽이 늘면 Starter ($7/월) 또는 Fly.io로 이전

---

## 2단계 — Capacitor로 Android 앱 빌드

### 2-1. 의존성 설치
```bash
cd frontend
npm install @capacitor/core @capacitor/android @capacitor/cli cross-env
npx cap init PetMe-Moji com.petmemoji.app
```

### 2-2. 환경변수 설정
`frontend/.env.production` 생성:
```
NEXT_PUBLIC_API_BASE=https://petme-moji-api-xxxx.onrender.com
```

### 2-3. 정적 빌드 + Android 프로젝트 생성
```bash
# Windows PowerShell:
$env:BACKEND_URL="https://petme-moji-api-xxxx.onrender.com"
npm run build:mobile          # next export → out/
npx cap add android           # android/ 폴더 생성
npx cap sync android
npx cap open android          # Android Studio 자동 오픈
```

### 2-4. Android Studio에서
1. 첫 실행: SDK·NDK 자동 다운로드 (~30분)
2. **Build > Generate Signed Bundle / APK** → **Android App Bundle (AAB)** 선택
3. **Create new...** 키스토어 생성:
   - 파일명: `petme-release-key.jks` (잘 보관!)
   - 비밀번호: 강력하게 설정 후 안전한 곳에 백업
   - 별칭: `petme`
   - 유효기간: 25년 이상
4. **release** 빌드 → AAB 파일 생성 (`app-release.aab`)

---

## 3단계 — 개인정보 처리방침 작성

플레이스토어는 모든 앱에 필수.

`docs/privacy-policy.md` 템플릿이 함께 제공됨. GitHub Pages로 호스팅:

1. 저장소 Settings → Pages → Source: `main` branch, `/docs` folder
2. URL: `https://본인아이디.github.io/petme-moji/privacy-policy`
3. 이 URL을 Play Console에 입력

---

## 4단계 — Play Console 등록

### 4-1. 앱 만들기
1. Play Console → **앱 만들기**
2. 앱 이름: `PetMe-Moji`
3. 기본 언어: 한국어
4. 앱 또는 게임: 앱
5. 유료/무료: **유료**
6. 가격: ₩3,300 (또는 원하는 금액)

### 4-2. 스토어 등록 정보 (스토어 목록)

**제목 (30자)**:
```
PetMe-Moji - AI 이모티콘 생성
```

**짧은 설명 (80자)**:
```
내 사진을 카카오톡 이모티콘 32종으로 자동 변환. AI가 사진을 보고 맞춤 라벨 생성.
```

**자세한 설명 (4000자)**:
```
🐾 PetMe-Moji

내 인물 사진과 반려동물(또는 사물/식물/인형) 사진 2장을 넣으면
카카오톡 이모티콘 32종 + 키보드 아이콘이 자동으로 만들어지는 AI 앱입니다.

✨ 주요 기능
• 사진 2장 → 카카오톡 규격 이모티콘 32장 자동 생성 (360x360 PNG, 투명배경)
• 키보드 메인 아이콘 78x78 자동 생성 (16KB 이하)
• AI가 사진을 보고 자동 인식: 강아지/고양이/식물/인형/사물/음식 등
• 피사체에 맞는 32개 상징 라벨 자동 작성 (푸들→왈왈안녕, 선인장→뾰족안녕)
• 6가지 화풍 선택: 2D 카툰 / 수채화 / 파스텔 / 웹툰 / 픽셀아트 / 팝아트
• 원본 색상 보존 — 옷·머리·털 색이 32장 모두 일관되게 유지
• 카카오톡 이모티콘 스튜디오 제출용 ZIP 한 번에 다운로드

🔐 API 키 안전
• 본인의 Google AI Studio Gemini API 키를 입력하는 BYOK 방식
• 키는 기기에 암호화 저장 (Fernet AES-128)
• 사용량은 Google이 본인에게 직접 청구 (앱은 광고/추적 없음)

💰 비용 안내
• 앱 구매: 1회 ₩3,300
• Gemini API: 사용자 본인 부담 (32장 약 $1.25, Google 무료 할당량 활용 가능)

🎨 활용 예시
• 내 강아지/고양이로 카카오톡 이모티콘 제작
• 가족 사진 + 반려동물 → 가족용 이모티콘 세트
• 좋아하는 캐릭터/인형 → 인형 캐릭터화
• 음식점 브랜드 마스코트 시안
• 라인/네이버 등 다른 플랫폼 스티커 제작에도 활용

📋 카카오톡 이모티콘 제출
• 모든 결과물이 카카오 가이드라인 규격으로 자동 패키징
• stickers/ 폴더 + icon.png + manifest.json + README.txt 동봉
• ZIP 다운로드 → 그대로 emoticonstudio.kakao.com 제출

문의: 이메일 / GitHub Issues
```

### 4-3. 그래픽 자산 준비

| 자산 | 사이즈 | 비고 |
|---|---|---|
| 앱 아이콘 | 512×512 PNG | 투명 배경 X, 풀컬러 |
| 피처 그래픽 | 1024×500 PNG/JPG | 가로 배너 |
| 폰 스크린샷 | 최소 2장 (1080×1920 권장) | 키 입력 화면, 메인, 32 그리드, 다운로드 |
| 태블릿 스크린샷 | 선택 |

스크린샷은 실제 앱 실행해서 캡처. 또는 [https://app-mockup.com](https://app-mockup.com) 같은 도구로 데모용 생성 가능.

### 4-4. 콘텐츠 등급
1. 앱 콘텐츠 → 콘텐츠 등급 → 설문 작성
2. 사진/AI 생성 앱은 보통 **전체이용가** 가능
3. 폭력/성적 콘텐츠 없음 체크

### 4-5. 데이터 보안
1. 앱 콘텐츠 → **데이터 보안** → 설문
2. **수집/공유하는 데이터**:
   - 사진/동영상: 수집 O (사용자 업로드)
   - 앱 활동: 없음
   - 식별자: 없음
3. **데이터 처리 위치**: 사용자 기기 + 사용자가 선택한 백엔드
4. **데이터 삭제 요청**: 사용자가 앱 내 [삭제] 가능
5. 개인정보 처리방침 URL 입력

### 4-6. 대상 사용자층
- 연령: 13세 이상
- 가족 정책: 해당 없음

### 4-7. AAB 업로드
1. **프로덕션 > 출시 만들기**
2. 2단계에서 만든 `app-release.aab` 업로드
3. 변경사항 메모: "최초 출시"
4. **저장 → 검토 → 출시**

### 4-8. 심사 대기
- 첫 출시: 보통 3~7일
- 거부 시 사유 확인 후 수정 → 재제출

---

## 5단계 — 출시 후

### 모니터링
- Play Console > 통계
- Render Dashboard > Logs / Metrics

### 사용자 지원
- Play Console > 리뷰 답변
- GitHub Issues 활성화 권장

### 업데이트
- 코드 수정 → push → Render 자동 재배포
- Capacitor sync → AAB 다시 빌드 (`versionCode` 증가) → Play Console 새 출시

---

## ⚠️ 출시 시 흔한 거부 사유 + 대응

| 거부 사유 | 대응 |
|---|---|
| 개인정보 처리방침 누락/미흡 | URL 정상 동작 확인, 한국어/영어 둘 다 권장 |
| 데이터 보안 설문과 실제 동작 불일치 | 정직하게 작성, "사진 수집"으로 표시 |
| API 키 입력 안내 부족 | 첫 화면에 Google AI Studio 발급 링크 명시 |
| 광고 SDK 잔류 | 설치한 적 없음 — 무관 |
| AI 생성 콘텐츠 정책 | "AI가 사용자 사진을 변환"임을 명시 |
| 권한 과다 요청 | Capacitor 기본 권한만 — 저장소/카메라 정도 |

---

## 💰 가격/수익 참고

| 가격대 | 예상 수익률 | 비고 |
|---|---|---|
| ₩1,200 (~$0.99) | Google 수수료 30% → 본인 ₩840 | 충동 구매 유도 |
| **₩3,300 (~$2.50)** ⭐ | 본인 ₩2,310 | 유틸 앱 표준 |
| ₩5,500 (~$4.50) | 본인 ₩3,850 | 프리미엄 포지셔닝 |

수익이 $1,000 누적되면 첫 입금. 한국 계좌 가능.

---

## 📚 참고

- [Google Play Console 도움말](https://support.google.com/googleplay/android-developer)
- [Capacitor 공식 문서](https://capacitorjs.com/docs/android)
- [Render Docs](https://render.com/docs)
- [Android Studio 가이드](https://developer.android.com/studio/intro)

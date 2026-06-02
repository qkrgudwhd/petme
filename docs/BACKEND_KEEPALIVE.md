# 백엔드 Keep-Alive 설정 (Cold Start 방지)

> Render Free tier는 15분 무요청 시 sleep → 다음 첫 요청 30~60초 지연.
> 무료 모니터링 서비스로 자동 ping 보내서 항상 깨어있게 유지.

---

## 📊 현재 백엔드 상태

```
URL: https://petme-moji-api.onrender.com
호스팅: Render (Singapore, Free)
스펙: 512MB RAM, 0.1 CPU
도커: backend/Dockerfile

응답 속도:
  Cold start: 22초 (sleep 후 첫 요청)
  Warm:      140~200ms (평균 175ms)
```

---

## 🎯 추천 방법 — UptimeRobot

### 장점
- ✅ **완전 무료** (50개 모니터까지)
- ✅ 5분마다 자동 ping
- ✅ 다운 시 이메일 알림
- ✅ 가동률 통계 (월/연)
- ✅ 한국어 UI

### 가입 + 설정 (5분)

#### 1. 가입
```
https://uptimerobot.com → Sign Up Free
```

이메일 + 비번 입력 → 가입 완료.

#### 2. 모니터 추가

```
[+ Add New Monitor]
```

#### 3. 설정값

| 칸 | 입력값 |
|---|---|
| **Monitor Type** | HTTP(s) |
| **Friendly Name** | PetMe-Moji Backend |
| **URL** | `https://petme-moji-api.onrender.com/api/health` |
| **Monitoring Interval** | 5 minutes |
| **Monitor Timeout** | 30 seconds |
| **HTTP Method** | GET |

#### 4. Alert Contacts

```
✓ Email: phjcom3@gmail.com
```

#### 5. **[Create Monitor]** 클릭

→ 5분마다 자동으로 `/api/health` 호출
→ 사용자 첫 요청 시 cold start 없음 ✓
→ 만약 백엔드 다운되면 이메일 알림 ✓

---

## 📊 결과 확인 — 24시간 후

UptimeRobot 대시보드에서:
- **가동률 (Uptime %)**: 99%+ 정상
- **응답 시간 (Response Time)**: 평균 200ms
- **다운 횟수**: 0 (정상)

---

## ⚠️ Render Free Tier 한계 — 주의사항

```
✓ 5분마다 ping으로 깨어있게 유지 가능
✗ 다만 월 750시간 무료 (1개 서비스 24/7 가능)
   → 모니터링 ping은 시간에 포함됨
   → 한 달 = 720시간 < 750시간 → 안전
✗ 하루 100GB 대역폭 → 텍스트 API라 문제 없음
✗ 디스크 공간 1GB → 세션 데이터 24시간 자동 정리 권장
```

---

## 🔄 대안 — Render Cron Job (별도 가입 X)

Render 자체 Cron Job 기능 사용 (유료, $1~5/월):
```yaml
# render.yaml 에 추가
services:
  - type: cron
    name: keep-alive
    runtime: docker
    schedule: "*/10 * * * *"  # 10분마다
    command: curl https://petme-moji-api.onrender.com/api/health
```

→ 더 통합되지만 비용 발생. **UptimeRobot 무료가 더 나음**.

---

## 📈 대안 — Cron-Job.org (무료)

```
https://cron-job.org
```

- 무료 회원가입
- 비슷한 방식으로 ping 설정
- UptimeRobot의 대안

---

## 🆘 트러블슈팅

### Q. UptimeRobot이 다운으로 보고하는데 실제로는 동작

가능한 원인:
1. `/api/health` 응답 시간이 30초 초과 (cold start) → Timeout 60초로 늘리기
2. Render가 일시 장애 → 잠시 후 자동 복구
3. SSL 인증서 만료 → Render 자동 갱신, 무시 가능

### Q. 무료 한도 초과 (월 750시간)

```
사용 시간 = 24h × 30일 = 720시간 < 750시간
```

→ 정상 사용 시 한도 안에 들어옴.

만약 초과되면:
- **Starter 플랜** ($7/월) 으로 업그레이드
- 또는 야간(00시~6시)에 ping 중단 (5시간 × 30일 = 150시간 절감)

### Q. Cold start가 여전히 발생

원인: ping 간격이 15분 초과
해결: 5분 또는 10분으로 줄이기

---

## 📊 모니터링 대시보드 예시

UptimeRobot 무료 플랜:
```
PetMe-Moji Backend                  🟢 Up
─────────────────────────────────────────
가동률 (지난 24시간):     99.93%
가동률 (지난 7일):       99.91%
가동률 (지난 30일):      99.88%
가동률 (지난 1년):       99.85%

평균 응답 시간:         197ms
최근 다운:              없음

[그래프: 시간대별 응답 속도]
```

---

## 🔗 빠른 참고 — 자동화 스크립트 대안

본인 PC에서 5분마다 직접 ping 보내고 싶다면:

### Windows 작업 스케줄러

```powershell
# C:\ping-petme.ps1
Invoke-WebRequest -Uri "https://petme-moji-api.onrender.com/api/health" -UseBasicParsing | Out-Null
```

작업 스케줄러:
- 트리거: 5분마다
- 동작: powershell -File "C:\ping-petme.ps1"

→ 본인 PC가 켜져있을 때만 동작 (불완전).

**UptimeRobot이 24/7 동작이라 더 나음.**

---

## 🎯 추천 진행

```
□ 1. UptimeRobot 가입 (5분)
□ 2. 모니터 추가 (URL: /api/health, 5분 간격)
□ 3. 이메일 알림 설정 (phjcom3@gmail.com)
□ 4. 24시간 후 가동률 확인
□ 5. 정상이면 그대로 유지
```

설정 후엔 손 안 대도 자동으로 백엔드 항상 깨어있음. 본인 앱 사용자가 30~60초 기다리는 일 없음. ✨

---

*가이드 작성: 2026-06-03*
*PetMe-Moji 백엔드 무중단 운영*

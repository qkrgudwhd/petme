# 배포 가이드 (GitHub / Google Drive)

이 문서는 **앱을 만든 본인**(=배포자)을 위한 안내. 사용자용은 README.md.

---

## 1. 배포 ZIP 만들기

```cmd
release.bat
```

→ `PetMe-Moji-source.zip` 이 프로젝트 루트에 생성됨.
(약 200KB — venv·node_modules·outputs 모두 제외됨)

**포함되는 것**: 백엔드 코드, 프론트엔드 코드, 배치 파일, README, LICENSE, docs/
**제외되는 것**: `.venv/`, `node_modules/`, `secrets.bin`, `.env`, 업로드/출력 폴더, `.git/`, `.next/`

---

## 2. GitHub 배포 (권장)

### 2-1. GitHub 저장소 생성

1. https://github.com/new 접속
2. Repository name: `petme-moji`
3. Public 선택
4. **README/License/gitignore는 추가하지 말 것** (이미 프로젝트에 있음)
5. Create repository

### 2-2. 코드 푸시

프로젝트 폴더에서:

```cmd
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/petme-moji.git
git push -u origin main
```

> **확인**: 푸시 전 `git status`로 `.venv`, `secrets.bin`, `.env`가 목록에 **없는지** 반드시 확인.
> `.gitignore`가 막아주지만 한 번 더 점검 권장.

### 2-3. 첫 Release 만들기

1. GitHub 저장소 → 우측 **Releases** → **Create a new release**
2. Tag: `v1.0.0`
3. Title: `PetMe-Moji v1.0.0 — 첫 정식 출시`
4. Description: 변경사항/주요 기능 요약
5. **Attach binaries**: `release.bat`으로 만든 `PetMe-Moji-source.zip` 업로드
6. **Publish release**

### 2-4. README의 다운로드 링크 업데이트

`README.md` 의 `YOUR_GH`를 본인 GitHub 사용자명으로 교체:

```diff
- [최신 버전 다운로드](https://github.com/YOUR_GH/petme-moji/releases/latest)
+ [최신 버전 다운로드](https://github.com/내아이디/petme-moji/releases/latest)
```

다시 커밋·푸시.

---

## 3. Google Drive 배포 (보조)

GitHub에 익숙하지 않은 사용자를 위한 대안.

1. Google Drive 접속 → `release.bat`으로 만든 `PetMe-Moji-source.zip` 업로드
2. 파일 우클릭 → **공유** → **링크 보기** → **링크가 있는 모든 사용자**
3. 링크 복사
4. README.md 의 Google Drive 행에 링크 붙여넣고 푸시

---

## 4. 새 버전 배포 시

코드 변경 후:

```cmd
release.bat                          REM 새 ZIP 생성
git add -A
git commit -m "버전 설명"
git push
```

GitHub Releases에서 **Draft a new release** → 새 태그(`v1.1.0`) + ZIP 첨부.

Google Drive는 같은 파일명으로 덮어쓰기 (링크 그대로 유지됨).

---

## 5. 점검 체크리스트

배포 전 반드시:

- [ ] `release.bat`로 만든 ZIP을 **다른 폴더**에 풀어서 `setup.bat` → `start.bat`이 깨끗이 도는지 테스트
- [ ] ZIP에 `secrets.bin` / `.env` / `.venv` / `node_modules` 가 없는지 확인 (zip 안을 직접 열어보기)
- [ ] README의 GitHub 링크에 본인 사용자명 들어갔는지
- [ ] LICENSE 의 연도/이름 본인 것으로
- [ ] Gemini API 키가 코드 어디에도 하드코딩 안 됐는지 (grep 'AIzaSy' 확인)

---

## 6. 사용자 지원

GitHub Issues 활성화 → README에 "버그/요청은 Issues로" 안내.
Discussions도 켜면 사용자 Q&A 가능.

---

## 7. 배포 후 모니터링 (선택)

GitHub Insights → Traffic 에서 클론/다운로드 수 확인 가능.
Releases 페이지의 각 자산별 다운로드 카운트도 표시됨.

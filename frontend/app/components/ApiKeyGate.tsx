"use client";
import { useEffect, useState } from "react";
import {
  deleteApiKey,
  getKeyStatus,
  saveApiKey,
  verifyApiKey,
  type KeyStatus,
} from "@/lib/api";

type Props = {
  onReady: (status: KeyStatus) => void;
  children: React.ReactNode;
};

export function ApiKeyGate({ onReady, children }: Props) {
  const [status, setStatus] = useState<KeyStatus | null>(null);
  const [value, setValue] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [checking, setChecking] = useState(true);

  async function refresh() {
    try {
      const s = await getKeyStatus();
      setStatus(s);
      if (s.configured) onReady(s);
      return s;
    } finally {
      setChecking(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function saveAndVerify() {
    setBusy(true);
    setMsg(null);
    try {
      const saved = await saveApiKey(value.trim());
      setMsg({ kind: "ok", text: "암호화 저장 완료. Google 인증 검증 중..." });
      const v = await verifyApiKey();
      if (!v.ok) {
        setMsg({ kind: "err", text: `검증 실패: ${v.message ?? "키를 다시 확인하세요."}` });
        setBusy(false);
        return;
      }
      setMsg({ kind: "ok", text: "✓ 인증 성공! 메인 화면으로 이동합니다..." });
      setStatus(saved);
      setTimeout(() => onReady(saved), 700);
    } catch (e) {
      setMsg({ kind: "err", text: String(e) });
    } finally {
      setBusy(false);
    }
  }

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-neutral-400 text-sm animate-pulse">키 상태 확인 중...</div>
      </div>
    );
  }

  if (status?.configured) return <>{children}</>;

  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-8 bg-gradient-to-br from-pink-50 via-white to-amber-50">
      <div className="bg-white rounded-3xl shadow-2xl max-w-xl w-full p-8 border">
        <div className="flex items-center gap-3 mb-3">
          <div className="text-4xl">🐾</div>
          <div>
            <h1 className="text-2xl font-bold">PetMe-Moji 시작하기</h1>
            <p className="text-sm text-neutral-500">먼저 Google Gemini API 키를 입력해주세요.</p>
          </div>
        </div>

        {/* 안내 박스 */}
        <details className="my-4 rounded-xl bg-blue-50 border border-blue-200 group" open>
          <summary className="px-4 py-3 cursor-pointer font-semibold text-sm text-blue-900 select-none">
            💡 API 키가 뭔가요? 왜 필요하죠? <span className="text-xs font-normal text-blue-600">(클릭해서 펼침/접음)</span>
          </summary>
          <div className="px-4 pb-4 text-xs text-blue-900 leading-relaxed space-y-2">
            <p>
              <b>Gemini는 Google의 AI 이미지 생성 서비스</b>예요. 본 앱은 이 서비스를
              호출해서 이모티콘을 만듭니다.
            </p>
            <p>
              <b>API 키</b>는 "사용자가 Google AI에 직접 요청을 보내는 출입증" 같은 개념.
              본 앱은 키를 가지지 않고 사용자 키를 빌려 호출만 대신해요.
            </p>
            <p className="bg-white/70 rounded-lg p-2.5 border border-blue-200">
              <b>💰 비용 안내</b>
              <br />
              • 키 발급: <b>무료</b> (Google AI Studio)<br />
              • 첫 사용 시 무료 할당량 제공 (분당 15회, 일 1,500회)<br />
              • 32장 생성: 약 <b>$1.25</b> (Google이 키 소유자에게 직접 청구)<br />
              • 본 앱은 어떤 수수료도 받지 않습니다
            </p>
            <p className="bg-white/70 rounded-lg p-2.5 border border-blue-200">
              <b>🔐 보안</b>
              <br />
              • 키는 <b>Fernet(AES-128 + HMAC)</b> 으로 암호화돼 이 PC에만 저장됨<br />
              • 다른 PC로 파일을 복사해도 풀 수 없음 (머신 지문 PBKDF2)<br />
              • 키는 Google 호출 직전에만 메모리에 잠시 복호화
            </p>
          </div>
        </details>

        {/* 발급 절차 박스 */}
        <details className="my-4 rounded-xl bg-emerald-50 border border-emerald-200">
          <summary className="px-4 py-3 cursor-pointer font-semibold text-sm text-emerald-900 select-none">
            🚀 키 발급 방법 (1~2분 소요)
          </summary>
          <ol className="px-4 pb-4 text-xs text-emerald-900 leading-relaxed space-y-1.5 list-decimal list-inside">
            <li>
              <a
                href="https://aistudio.google.com/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-pink-600 underline font-semibold"
              >
                Google AI Studio (aistudio.google.com/apikey)
              </a>{" "}
              에 접속 → Google 계정으로 로그인
            </li>
            <li>우측 상단 <b>[+ Create API key]</b> 클릭</li>
            <li>프로젝트 선택 (없으면 "Create API key in new project")</li>
            <li>나타난 키 옆 <b>📋 복사 아이콘</b> 클릭 (드래그 복사 금지 — 공백 섞임)</li>
            <li>키는 <code className="bg-white px-1 rounded">AIzaSy</code>로 시작하는 39자 문자열</li>
            <li>아래 입력칸에 붙여넣기 → <b>[암호화 저장 & 검증]</b></li>
          </ol>
        </details>

        <label className="block text-sm font-semibold mb-1">API 키</label>
        <div className="flex gap-2">
          <input
            type={show ? "text" : "password"}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && value.trim() && !busy) saveAndVerify();
            }}
            placeholder="AIzaSy..."
            autoComplete="off"
            autoFocus
            className="flex-1 px-4 py-3 border rounded-xl font-mono text-sm focus:border-pink-400 outline-none"
          />
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="px-3 text-sm border rounded-xl hover:border-pink-400"
            title={show ? "숨기기" : "표시"}
          >
            {show ? "🙈" : "👁"}
          </button>
        </div>
        <div className="text-[10px] text-neutral-500 mt-1.5">
          키 형식: <code className="bg-neutral-100 px-1 rounded">AIzaSy</code>로 시작하는 39자
          {value && (
            <>
              {" "}· 현재 길이 {value.trim().length}자{" "}
              {value.trim().startsWith("AIza") ? "✓" : "⚠ AIza로 시작하지 않음"}
            </>
          )}
        </div>

        <button
          onClick={saveAndVerify}
          disabled={busy || !value.trim()}
          className={`w-full mt-4 py-3 rounded-xl font-semibold transition ${
            busy
              ? "btn-working"
              : "bg-pink-500 text-white hover:bg-pink-600 disabled:opacity-40"
          }`}
        >
          {busy ? "🔐 암호화 저장 & Google 인증 검증 중..." : "암호화 저장 & 검증"}
        </button>

        {msg && (
          <div
            className={`mt-4 text-sm px-4 py-3 rounded-xl ${
              msg.kind === "ok"
                ? "bg-green-50 text-green-700 border border-green-200"
                : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            {msg.text}
          </div>
        )}

        <div className="mt-5 pt-4 border-t text-center text-xs text-neutral-500">
          한 번 저장하면 다음 실행 시 자동으로 기억됩니다 · 변경/삭제는 메인 화면 우측 상단 ⚙ 버튼
        </div>
      </div>
    </main>
  );
}

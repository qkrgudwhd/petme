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
  open: boolean;
  onClose: () => void;
  onChanged?: (status: KeyStatus) => void;
};

export function ApiKeyModal({ open, onClose, onChanged }: Props) {
  const [status, setStatus] = useState<KeyStatus | null>(null);
  const [value, setValue] = useState("");
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    if (open) {
      setMsg(null);
      setValue("");
      getKeyStatus().then(setStatus).catch(() => setStatus({ configured: false, masked: "" }));
    }
  }, [open]);

  if (!open) return null;

  async function save() {
    setBusy(true);
    setMsg(null);
    try {
      const s = await saveApiKey(value.trim());
      setStatus(s);
      setValue("");
      onChanged?.(s);
      setMsg({ kind: "ok", text: "암호화 저장 완료." });
    } catch (e) {
      setMsg({ kind: "err", text: String(e) });
    } finally {
      setBusy(false);
    }
  }

  async function verify() {
    setBusy(true);
    setMsg(null);
    const r = await verifyApiKey();
    setMsg(
      r.ok
        ? { kind: "ok", text: "✓ Gemini 인증 성공." }
        : { kind: "err", text: r.message || "검증 실패" },
    );
    setBusy(false);
  }

  async function remove() {
    if (!confirm("저장된 키를 삭제할까요?")) return;
    setBusy(true);
    setMsg(null);
    try {
      await deleteApiKey();
      const s = { configured: false, masked: "" };
      setStatus(s);
      onChanged?.(s);
      setMsg({ kind: "ok", text: "삭제됨." });
    } catch (e) {
      setMsg({ kind: "err", text: String(e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold">🔐 Gemini API 키 설정</h2>
          <button onClick={onClose} className="text-neutral-400 hover:text-neutral-700">✕</button>
        </div>

        <details className="bg-blue-50 rounded-lg border border-blue-200 mb-3 group">
          <summary className="px-3 py-2 cursor-pointer text-xs font-semibold text-blue-900 select-none">
            💡 API 키란? (열어서 자세히 보기)
          </summary>
          <div className="px-3 pb-3 text-xs text-blue-900 leading-relaxed space-y-1.5">
            <p>Gemini는 Google의 AI 이미지 생성 서비스. 본 앱은 사용자 키로 호출만 대신합니다.</p>
            <p>
              <b>발급</b>: <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" className="text-pink-600 underline">aistudio.google.com/apikey</a> → [+ Create API key]
            </p>
            <p>
              <b>비용</b>: 키 발급 무료. 32장 생성 약 $1.25 (Google이 키 소유자에게 직접 청구). 무료 할당량 분당 15회/일 1,500회.
            </p>
            <p>
              <b>보안</b>: Fernet (AES-128 + HMAC), PBKDF2-SHA256 머신 지문에서 도출.
              다른 PC로 secrets.bin 복사해도 복호화 불가. 메모리에는 호출 시점에만 잠시 복호화.
            </p>
          </div>
        </details>

        {status?.configured && (
          <div className="mb-3 px-3 py-2 rounded-lg bg-green-50 border border-green-200 text-sm flex justify-between items-center">
            <span>
              현재 저장됨: <code className="font-mono">{status.masked}</code>
            </span>
            <div className="flex gap-2">
              <button
                onClick={verify}
                disabled={busy}
                className={`text-xs px-2 py-1 rounded border disabled:opacity-40 ${
                  busy ? "btn-working-mini" : "bg-white hover:border-pink-400"
                }`}
              >
                {busy ? "검증 중..." : "검증"}
              </button>
              <button
                onClick={remove}
                disabled={busy}
                className="text-xs px-2 py-1 rounded bg-white border text-red-600 hover:border-red-400 disabled:opacity-40"
              >
                삭제
              </button>
            </div>
          </div>
        )}

        <label className="block text-sm font-semibold mb-1">
          {status?.configured ? "새 키로 변경" : "API 키 입력"}
        </label>
        <div className="flex gap-2">
          <input
            type={show ? "text" : "password"}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="AIza..."
            autoComplete="off"
            className="flex-1 px-3 py-2 border rounded-lg font-mono text-sm focus:border-pink-400 outline-none"
          />
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="px-3 text-sm border rounded-lg hover:border-pink-400"
          >
            {show ? "🙈" : "👁"}
          </button>
        </div>

        <button
          onClick={save}
          disabled={busy || !value.trim()}
          className={`w-full mt-4 py-2.5 rounded-lg font-semibold transition ${
            busy
              ? "btn-working"
              : "bg-pink-500 text-white hover:bg-pink-600 disabled:opacity-40"
          }`}
        >
          {busy ? "🔐 처리 중..." : "암호화 저장"}
        </button>

        {msg && (
          <div
            className={`mt-3 text-sm px-3 py-2 rounded-lg ${
              msg.kind === "ok"
                ? "bg-green-50 text-green-700 border border-green-200"
                : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            {msg.text}
          </div>
        )}

        <div className="mt-4 text-xs text-neutral-500">
          키 발급:{" "}
          <a
            href="https://aistudio.google.com/apikey"
            target="_blank"
            rel="noreferrer"
            className="text-pink-600 hover:underline"
          >
            Google AI Studio
          </a>
        </div>
      </div>
    </div>
  );
}

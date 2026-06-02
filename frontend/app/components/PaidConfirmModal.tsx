"use client";
import { useState } from "react";
import { approvePaid, revokePaid, type UsageInfo } from "@/lib/api";

type Props = {
  open: boolean;
  usage: UsageInfo | null;
  onClose: () => void;
  onApproved: () => void;
};

const PRESETS = [
  { krw: 5000, label: "₩5,000", desc: "약 95장 추가" },
  { krw: 10000, label: "₩10,000", desc: "약 192장 추가" },
  { krw: 20000, label: "₩20,000", desc: "약 384장 추가" },
];

export function PaidConfirmModal({ open, usage, onClose, onApproved }: Props) {
  const [busy, setBusy] = useState(false);
  const [custom, setCustom] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  if (!open) return null;

  async function approve(krw: number) {
    setBusy(true);
    setMsg(null);
    try {
      const r = await approvePaid(krw);
      setMsg(`✓ ₩${r.approved_cap_krw.toLocaleString()} 한도까지 진행 가능합니다.`);
      setTimeout(() => { onApproved(); }, 600);
    } catch (e) {
      setMsg(`실패: ${e}`);
    } finally {
      setBusy(false);
    }
  }

  async function revoke() {
    setBusy(true);
    setMsg(null);
    try {
      await revokePaid();
      setMsg("✓ 추가 결제 비활성화됨. 무료 한도까지만 사용됩니다.");
      setTimeout(() => onClose(), 600);
    } catch (e) {
      setMsg(`실패: ${e}`);
    } finally {
      setBusy(false);
    }
  }

  const customNum = parseInt(custom.replace(/[^0-9]/g, ""), 10);
  const customValid = !isNaN(customNum) && customNum >= 1000 && customNum <= 200000;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-lg font-bold flex items-center gap-2">
              <span className="text-2xl">💳</span>
              무료 한도 모두 사용
            </h2>
            <p className="text-xs text-neutral-500 mt-1">
              추가 진행하려면 비용 동의가 필요합니다.
            </p>
          </div>
          <button onClick={onClose} className="text-neutral-400 hover:text-neutral-700">✕</button>
        </div>

        {/* 현재 상태 */}
        {usage && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 text-xs">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <div className="text-amber-700">오늘 무료 사용</div>
                <div className="font-bold text-amber-900">
                  {usage.daily_used} / {usage.daily_free_limit}장
                </div>
              </div>
              <div>
                <div className="text-amber-700">이번 달 결제</div>
                <div className="font-bold text-amber-900">
                  ₩{usage.monthly_spent_krw.toLocaleString()} / ₩{usage.monthly_approved_cap_krw.toLocaleString()}
                </div>
              </div>
            </div>
            <div className="text-amber-800 mt-2 text-[11px]">
              장당 약 ₩{usage.krw_per_image}, Google이 키 소유자에게 직접 청구합니다.
            </div>
          </div>
        )}

        <div className="text-sm font-semibold mb-2">추가 결제 한도 선택</div>
        <div className="grid grid-cols-3 gap-2 mb-3">
          {PRESETS.map((p) => (
            <button
              key={p.krw}
              onClick={() => approve(p.krw)}
              disabled={busy}
              className={`px-3 py-3 rounded-xl border transition text-center ${
                busy
                  ? "btn-working opacity-60"
                  : "bg-white hover:border-pink-400 hover:bg-pink-50"
              }`}
            >
              <div className="font-bold text-pink-700">{p.label}</div>
              <div className="text-[10px] text-neutral-500 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>

        {/* 커스텀 금액 */}
        <div className="flex gap-2 mb-3">
          <div className="flex-1 relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400">₩</span>
            <input
              type="text"
              inputMode="numeric"
              value={custom}
              onChange={(e) => setCustom(e.target.value.replace(/[^0-9,]/g, ""))}
              placeholder="직접 입력 (1,000~200,000)"
              className="w-full pl-8 pr-3 py-2.5 border rounded-xl text-sm focus:border-pink-400 outline-none"
            />
          </div>
          <button
            onClick={() => customValid && approve(customNum)}
            disabled={!customValid || busy}
            className={`px-4 py-2.5 rounded-xl font-semibold text-sm disabled:opacity-40 ${
              busy
                ? "btn-working"
                : "bg-pink-500 text-white hover:bg-pink-600"
            }`}
          >
            동의
          </button>
        </div>

        <div className="border-t pt-3 mt-3 flex justify-between items-center">
          <button
            onClick={revoke}
            disabled={busy}
            className="text-xs text-neutral-500 hover:text-red-600 underline disabled:opacity-40"
          >
            ← 결제 안 함 (무료 한도까지만)
          </button>
          <div className="text-[10px] text-neutral-400">
            동의 한도는 매월 1일 자동 리셋
          </div>
        </div>

        {msg && (
          <div className={`mt-3 text-xs px-3 py-2 rounded-lg ${
            msg.startsWith("✓") ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
          }`}>
            {msg}
          </div>
        )}
      </div>
    </div>
  );
}

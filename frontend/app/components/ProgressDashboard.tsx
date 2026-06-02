"use client";
import { useEffect, useMemo, useRef, useState } from "react";

export type ActivityEvent = {
  t: number; // unix ms
  kind: "info" | "item" | "error" | "done";
  text: string;
  key?: string;
  ms?: number;
  bytes?: number;
};

type Props = {
  total: number;
  done: number;
  errors: number;
  startedAt: number | null;
  events: ActivityEvent[];
  zipUrl: string | null;
  currentlyProcessing?: string[]; // 현재 처리 중인 한글 라벨들
};

function fmtTime(t: number) {
  const d = new Date(t);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function fmtDuration(ms: number) {
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}초`;
  return `${Math.floor(s / 60)}분 ${s % 60}초`;
}

export function ProgressDashboard({
  total, done, errors, startedAt, events, zipUrl, currentlyProcessing = [],
}: Props) {
  const pct = total > 0 ? done / total : 0;

  const stats = useMemo(() => {
    const completions = events.filter((e) => e.kind === "item").map((e) => e.t);
    const elapsed = startedAt ? Date.now() - startedAt : 0;
    const avgMsPerItem = done > 0 && elapsed > 0 ? elapsed / done : 0;
    const remaining = total - done;
    const eta = remaining > 0 && avgMsPerItem > 0 ? remaining * avgMsPerItem : 0;
    return { completions, elapsed, avgMsPerItem, eta };
  }, [events, startedAt, done, total]);

  // Sparkline 데이터: 시작 후 1초 간격으로 누적 완료 수
  const sparkPoints = useMemo(() => {
    if (!startedAt) return [];
    const buckets = 40;
    const range = Math.max(1000, Date.now() - startedAt);
    const arr: number[] = new Array(buckets).fill(0);
    const ts = stats.completions;
    for (const t of ts) {
      const idx = Math.min(buckets - 1, Math.floor(((t - startedAt) / range) * buckets));
      if (idx >= 0) {
        for (let i = idx; i < buckets; i++) arr[i]++;
      }
    }
    return arr;
  }, [stats.completions, startedAt, done]);

  // 활동 로그 auto-scroll
  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [events.length]);

  // 1초마다 ETA 갱신용 forceUpdate
  const [, force] = useTick(1000, startedAt !== null && done < total);

  return (
    <div className="grid md:grid-cols-3 gap-4">
      {/* 원형 진행률 */}
      <div className="bg-white rounded-2xl border p-5 flex flex-col items-center justify-center">
        <CircularProgress pct={pct} done={done} total={total} />
        {zipUrl && (
          <a
            href={zipUrl}
            download="petme-emoticons.zip"
            className="mt-3 inline-flex items-center gap-1 px-4 py-2 rounded-full bg-pink-500 text-white text-sm font-semibold hover:bg-pink-600"
          >
            📦 ZIP 다운로드
          </a>
        )}
      </div>

      {/* 통계 */}
      <div className="bg-white rounded-2xl border p-5 flex flex-col gap-2 text-sm">
        <Stat label="완료" value={`${done} / ${total}`} hl="text-pink-600" />
        <Stat label="실패" value={String(errors)} hl={errors ? "text-red-600" : "text-neutral-500"} />
        <Stat label="경과" value={startedAt ? fmtDuration(stats.elapsed) : "—"} />
        <Stat
          label="장당 평균"
          value={stats.avgMsPerItem ? `${(stats.avgMsPerItem / 1000).toFixed(1)}초` : "—"}
        />
        <Stat
          label="예상 남은 시간"
          value={stats.eta && done < total ? fmtDuration(stats.eta) : done === total ? "완료" : "—"}
          hl="text-amber-600"
        />
      </div>

      {/* Sparkline */}
      <div className="bg-white rounded-2xl border p-5">
        <div className="text-xs font-semibold text-neutral-600 mb-2">시간별 누적 완료</div>
        <Sparkline data={sparkPoints} total={total} />
        <div className="text-[10px] text-neutral-400 mt-1 flex justify-between">
          <span>시작</span>
          <span>지금</span>
        </div>
      </div>

      {/* 현재 처리 중 (전체 폭) */}
      {currentlyProcessing.length > 0 && (
        <div className="md:col-span-3 bg-pink-50 border border-pink-200 rounded-2xl p-4">
          <div className="text-xs font-semibold text-pink-700 mb-2 flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-pink-500 animate-pulse" />
            지금 동시에 처리 중 ({currentlyProcessing.length}개)
          </div>
          <div className="flex flex-wrap gap-2">
            {currentlyProcessing.map((label, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full bg-white border border-pink-300 text-sm font-medium text-pink-700">
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 활동 로그 (전체 폭) */}
      <div className="md:col-span-3 bg-slate-900 rounded-2xl p-4 text-xs font-mono">
        <div className="flex justify-between items-center mb-2 text-slate-300">
          <span className="font-semibold">📋 실시간 활동 로그</span>
          <span className="text-slate-500">{events.length} 이벤트</span>
        </div>
        <div ref={logRef} className="max-h-48 overflow-y-auto space-y-0.5">
          {events.length === 0 && (
            <div className="text-slate-500">— 대기 중 —</div>
          )}
          {events.map((e, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-slate-500 shrink-0">[{fmtTime(e.t)}]</span>
              <span
                className={
                  e.kind === "item"
                    ? "text-emerald-300"
                    : e.kind === "error"
                    ? "text-red-300"
                    : e.kind === "done"
                    ? "text-amber-300 font-semibold"
                    : "text-sky-300"
                }
              >
                {e.kind === "item" && "✓"}
                {e.kind === "error" && "✗"}
                {e.kind === "done" && "★"}
                {e.kind === "info" && "•"}
              </span>
              <span className="text-slate-200 break-all">{e.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, hl }: { label: string; value: string; hl?: string }) {
  return (
    <div className="flex justify-between items-baseline border-b border-neutral-100 pb-1.5">
      <span className="text-xs text-neutral-500">{label}</span>
      <span className={`font-bold tabular-nums ${hl ?? "text-neutral-800"}`}>{value}</span>
    </div>
  );
}

function CircularProgress({ pct, done, total }: { pct: number; done: number; total: number }) {
  const r = 60;
  const c = 2 * Math.PI * r;
  const dash = c * pct;
  return (
    <svg width="160" height="160" viewBox="0 0 160 160">
      <circle cx="80" cy="80" r={r} stroke="#f3f4f6" strokeWidth="14" fill="none" />
      <circle
        cx="80"
        cy="80"
        r={r}
        stroke="#ec4899"
        strokeWidth="14"
        fill="none"
        strokeLinecap="round"
        strokeDasharray={`${dash} ${c}`}
        transform="rotate(-90 80 80)"
        style={{ transition: "stroke-dasharray 0.5s ease" }}
      />
      <text x="80" y="76" textAnchor="middle" className="fill-neutral-900" style={{ fontSize: 28, fontWeight: 700 }}>
        {Math.round(pct * 100)}%
      </text>
      <text x="80" y="100" textAnchor="middle" className="fill-neutral-400" style={{ fontSize: 12 }}>
        {done} / {total}
      </text>
    </svg>
  );
}

function Sparkline({ data, total }: { data: number[]; total: number }) {
  const W = 220;
  const H = 70;
  if (data.length === 0) {
    return (
      <svg width={W} height={H}>
        <text x={W / 2} y={H / 2} textAnchor="middle" className="fill-neutral-300" style={{ fontSize: 11 }}>
          데이터 없음
        </text>
      </svg>
    );
  }
  const max = Math.max(total, ...data) || 1;
  const stepX = W / (data.length - 1 || 1);
  const points = data.map((v, i) => `${i * stepX},${H - (v / max) * (H - 6) - 3}`);
  const fillPoints = `0,${H} ${points.join(" ")} ${W},${H}`;
  return (
    <svg width={W} height={H} className="w-full">
      <polyline points={fillPoints} fill="rgba(236,72,153,0.15)" stroke="none" />
      <polyline points={points.join(" ")} fill="none" stroke="#ec4899" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

// 간단한 setInterval 훅 (ETA 1초 주기 재계산용)
function useTick(intervalMs: number, enabled: boolean) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!enabled) return;
    const id = setInterval(() => setN((x) => x + 1), intervalMs);
    return () => clearInterval(id);
  }, [enabled, intervalMs]);
  return [n, () => setN((x) => x + 1)] as const;
}

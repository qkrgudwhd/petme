"""3단계 결제 게이트.

[1] 일 95장까지: 무료 티어 (Gemini 2.5 Flash Image)
[2] 95장 초과 시: NEED_PAID_CONFIRM — 사용자가 모달에서 금액 동의 필요
[3] 동의한 한도까지 진행, 한도 도달 시 다시 ②

분당 10회 RPM 보호: 모든 호출 전 7초 sleep으로 강제.
일일 / 월간 카운터는 storage 디스크에 영구 저장 (재시작·하루 후에도 유지).
"""
from __future__ import annotations

import json
import threading
import time
from datetime import date
from pathlib import Path

from ..config import settings

# ── 무료 티어 한도 (Google 공식) ───────────────────────
FREE_TIER_RPM = 10
SAFE_DELAY_SEC = 7.0
FREE_TIER_DAILY = 100
SAFE_DAILY_LIMIT = 95     # 안전 마진 5장

# ── 유료 환산 ────────────────────────────────────────
KRW_PER_IMAGE = 52        # $0.039 × 1330원 = ~52원
USD_PER_IMAGE = 0.039     # Gemini 2.5 Flash Image 공시 단가

_lock = threading.Lock()
_last_call_at: float = 0.0


def _daily_path() -> Path:
    return settings.storage_path / "daily_usage.json"


def _monthly_path() -> Path:
    return settings.storage_path / "monthly_usage.json"


def _today() -> str:
    return str(date.today())


def _this_month() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"


def _read_daily() -> dict:
    p = _daily_path()
    if not p.exists():
        return {"date": _today(), "count": 0}
    try:
        d = json.loads(p.read_text("utf-8"))
        if d.get("date") != _today():
            return {"date": _today(), "count": 0}
        return d
    except Exception:
        return {"date": _today(), "count": 0}


def _read_monthly() -> dict:
    p = _monthly_path()
    if not p.exists():
        return {"month": _this_month(), "spent_krw": 0, "approved_cap_krw": 0}
    try:
        d = json.loads(p.read_text("utf-8"))
        if d.get("month") != _this_month():
            # 월 바뀜 → 사용량/한도 둘 다 0으로 리셋
            return {"month": _this_month(), "spent_krw": 0, "approved_cap_krw": 0}
        return d
    except Exception:
        return {"month": _this_month(), "spent_krw": 0, "approved_cap_krw": 0}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def get_usage_today() -> dict:
    d = _read_daily()
    m = _read_monthly()
    return {
        "date": d["date"],
        "month": m["month"],
        "daily_used": d["count"],
        "daily_free_limit": SAFE_DAILY_LIMIT,
        "daily_remaining_free": max(0, SAFE_DAILY_LIMIT - d["count"]),
        "monthly_spent_krw": m["spent_krw"],
        "monthly_approved_cap_krw": m["approved_cap_krw"],
        "monthly_remaining_krw": max(0, m["approved_cap_krw"] - m["spent_krw"]),
        "krw_per_image": KRW_PER_IMAGE,
        "free_tier_hard_limit": FREE_TIER_DAILY,
    }


def approve_paid_budget(krw: int) -> dict:
    """사용자가 모달에서 추가 결제 동의 → 월 한도 +krw."""
    if krw <= 0:
        raise ValueError("금액은 양수여야 합니다.")
    if krw > 200_000:
        raise ValueError("1회 동의는 최대 ₩200,000입니다.")
    with _lock:
        m = _read_monthly()
        m["approved_cap_krw"] = int(m["approved_cap_krw"]) + int(krw)
        _write(_monthly_path(), m)
        return m


def reset_monthly_budget() -> dict:
    """사용자가 [더 이상 안 함] 클릭 시 호출 — 동의했던 한도 회수."""
    with _lock:
        m = _read_monthly()
        m["approved_cap_krw"] = m["spent_krw"]  # 이미 쓴 만큼만 남기고 잠금
        _write(_monthly_path(), m)
        return m


def reserve_one() -> str:
    """이미지 호출 직전. RuntimeError로 차단 또는 "free"/"paid" 반환."""
    global _last_call_at
    with _lock:
        d = _read_daily()
        m = _read_monthly()

        if d["count"] < SAFE_DAILY_LIMIT:
            # 무료 티어 안
            mode = "free"
        else:
            # 무료 한도 초과 → 동의된 결제 한도 확인
            if m["spent_krw"] + KRW_PER_IMAGE > m["approved_cap_krw"]:
                raise RuntimeError(
                    f"NEED_PAID_CONFIRM: 오늘 무료 한도({SAFE_DAILY_LIMIT}장)를 모두 사용했습니다. "
                    f"추가 진행하려면 비용 동의가 필요합니다. "
                    f"현재 월 동의 한도 ₩{m['approved_cap_krw']:,}, "
                    f"사용 ₩{m['spent_krw']:,}, "
                    f"장당 약 ₩{KRW_PER_IMAGE}."
                )
            mode = "paid"

        # 분당 10회 강제 sleep
        now = time.monotonic()
        gap = now - _last_call_at
        if gap < SAFE_DELAY_SEC:
            time.sleep(SAFE_DELAY_SEC - gap)
        _last_call_at = time.monotonic()

        # 카운터 증가
        d["count"] += 1
        _write(_daily_path(), d)
        if mode == "paid":
            m["spent_krw"] = int(m["spent_krw"]) + KRW_PER_IMAGE
            _write(_monthly_path(), m)
        return mode

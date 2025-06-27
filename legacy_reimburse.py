def legacy_reimburse(d: int, m: int, r: float) -> float:
    """Deterministic reimbursement model (per-diem + mileage tiers).

    Phase-D draft implementing strongest signals:
    1. Per-diem: $100/day base; +$75 bonus for 5-day trips; ≥9-day trips use $90/day.
    2. Mileage: tiered rate – 0-100 mi @ $0.58, 101-275 mi @ $0.45,
       276-916 mi @ $0.30, >916 mi @ $0.35.
    3. Receipts safeguard: reimbursement is never lower than submitted receipts.
    """

    # --- Per-diem component ---
    if d == 5:
        per_diem = 100 * d + 75  # 5-day bonus
    elif d >= 9:
        per_diem = 90 * d  # reduced long-trip rate
    else:
        per_diem = 100 * d

    # --- Mileage component ---
    remaining = m
    mileage = 0.0

    # Tier 1: first 100 miles
    tier = min(remaining, 100)
    mileage += tier * 0.58
    remaining -= tier

    # Tier 2: next up to 175 miles (total 275)
    if remaining > 0:
        tier = min(remaining, 175)
        mileage += tier * 0.45
        remaining -= tier

    # Tier 3: next up to 641 miles (total 916)
    if remaining > 0:
        tier = min(remaining, 641)
        mileage += tier * 0.30
        remaining -= tier

    # Tier 4: beyond 916 miles
    if remaining > 0:
        mileage += remaining * 0.35  # slight rebound in rate for very long drives

    total = per_diem + mileage

    # Ensure reimbursement at least equals receipts amount
    total = max(total, r)

    return round(total, 2)


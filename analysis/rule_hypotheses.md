# Phase C – Rule Mining: Candidate Hypotheses

_This document aggregates clues from_ **EDA**, **PRD.md**, _and_ **INTERVIEWS.md** _into concrete, testable rule hypotheses._

---

## 1. Per-Diem (Days-Driven)

| Days | Hypothesis | Evidence |
|------|------------|----------|
| 1-4  | Base rate ≈ $100/day | Lisa: "\$100 a day seems to be the base." |
| **5** | +$? bonus per day (or lump-sum bump) | Lisa: 5-day trips "almost always get a bonus." Kevin's "sweet-spot combo". |
| 6-8  | Revert to base $100 | Interviews note no consistent bonus. |
| **≥9** | Tier-2 per-diem drops to ≈ $90/day | EDA breakpoint at 9 days; HR notes reimbursements flatten on very long trips. |

Edge cases: extremely long trips (>12 days) might have further diminishing rate.

---

## 2. Mileage Reimbursement (Tiered Miles)

| Mileage band (total) | Hypothesis rate | Evidence |
|----------------------|-----------------|----------|
| 0-100 mi | Full rate ≈ $0.58/mi | Lisa: "First 100 miles… you get the full rate." |
| 101-**~275** mi | Reduced rate ≈ $0.45/mi | EDA derivative spike at 273–275 mi; Marcus & Dave note non-linear drop for 300-mi trips. |
| **~276-916** mi | Further reduced rate ≈ $0.30/mi | Second EDA breakpoint at 916 mi; Marcus's 600-mi vs 800-mi anecdotes show non-monotonic behaviour. |
| **>916** mi | Slight *increase* back to ≈ $0.35/mi (or bonus) | Marcus: 800-mi trip paid better per mile than 600-mi; suggests uplift in high-mileage tier. |

Mileage may also couple with trip length (miles per day efficiency → see Section 3).

---

## 3. Efficiency Bonus (Miles ÷ Days)

Hypothesis: A Gaussian-like bonus centred at **180-220 miles/day**; penalty below 100 or above 300 mi/day.

Evidence: Kevin's "sweet spot" analysis; Marcus mentions 8-day, high-mileage trip yielding great payout.

Implementation idea: `eff = miles / days`; apply multiplier:
* `if 180 <= eff <= 220: +10% reimbursement`
* `elif eff >= 300 or eff <= 100: –10%`

---

## 4. Receipts Adjustment (Diminishing Returns)

* Optimal band: **$600-800** total (Lisa).
* Low receipts (< $50) can *reduce* reimbursement below base (Dave).
* High receipts (> $1 000) saturate → each extra dollar reimbursed at ≤ 25 cents.
* Rounding bug/feature: receipt totals ending in `.49` or `.99` trigger +$2 flat bump (Lisa).

---

## 5. Five-Day "Sweet-Spot Combo"

If **days == 5** **and** `180 mi/day ≤ efficiency ≤ 220` **and** receipts per day ≤ $100 → apply **lump-sum bonus ≈ $75-$100**.

Evidence: Kevin's guaranteed bonus description.

---

## 6. Vacation Penalty

If **days ≥ 8** **and** high spending (> $90/day) → apply −7 % penalty on total.

Evidence: Kevin's "vacation penalty".

---

## 7. Misc. Quirks

* **Rounding policy**: final reimbursement rounded to 2 dp **but** clip at `max(receipts, mileage_component + per_diem)`. Marcus observed returns sometimes equal exactly the receipt cap.
* **Magic cents**: totals ending in `.49` or `.99` in receipts grant an extra rounding-up step (Lisa).

---

### Next Step

1. Translate these hypotheses into DSL fragments.
2. Use oracle (`python -m synthesis.search`) to fit constants precisely.
3. Iteratively validate against `public_cases.json`, logging MAE and counter-examples.
def legacy_reimburse(d: int, m: int, r: float) -> float:
    """Deterministic reimbursement model (synthesised).
    """
    if round(max(min(((1000 - 10) + min(800, m)), ((r * 0.8) + min(800, m))), min(((1000 - 120) + (r * 0.4)), ((r * 0.8) + 500))), 0) < max(min(((1000 - 10) + min(800, m)), ((r * 0.8) + min(800, m))), min(((1000 - 120) + (r * 0.4)), ((r * 0.8) + 500))):
        return round(round(max(min(((1000 - 10) + min(800, m)), ((r * 0.8) + min(800, m))), min(((1000 - 120) + (r * 0.4)), ((r * 0.8) + 500))), 0), 2)
    else:
        return round(max(min(((1000 - 10) + min(800, m)), ((r * 0.8) + min(800, m))), min(((1000 - 120) + (r * 0.4)), ((r * 0.8) + 500))), 2)


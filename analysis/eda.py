import json
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt  # type: ignore

DATA_FILE = Path(__file__).resolve().parent.parent / 'public_cases.json'
FIG_DIR = Path(__file__).resolve().parent / 'figs'
FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_cases(path: Path) -> pd.DataFrame:
    """Load the public cases JSON into a pandas DataFrame."""
    with path.open() as f:
        data = json.load(f)
    rows = []
    for case in data:
        inp = case["input"]
        out = case["expected_output"]
        rows.append({
            "days": inp["trip_duration_days"],
            "miles": inp["miles_traveled"],
            "receipts": inp["total_receipts_amount"],
            "reimbursement": out,
        })
    df = pd.DataFrame(rows)
    # Derived metrics
    df["reimb_per_day"] = df["reimbursement"] / df["days"]
    df["reimb_per_mile"] = df["reimbursement"] / df["miles"].replace(0, np.nan)
    df["receipts_per_day"] = df["receipts"] / df["days"]
    return df


def scatter(df: pd.DataFrame, x: str, y: str, color: str | None = None, fname: Optional[str] = None) -> None:
    plt.figure(figsize=(6, 4))
    if color and color in df.columns:
        plt.scatter(df[x], df[y], c=df[color], cmap='viridis', s=10, alpha=0.6)
        plt.colorbar(label=color)
    else:
        plt.scatter(df[x], df[y], s=10, alpha=0.6)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.tight_layout()
    if fname:
        plt.savefig(FIG_DIR / fname, dpi=150)
    plt.close()


def heatmap(df: pd.DataFrame, x: str, y: str, bins: Tuple[int, int] = (60, 60), fname: Optional[str] = None) -> None:
    plt.figure(figsize=(6, 4))
    plt.hist2d(df[x], df[y], bins=bins, cmap='plasma')
    plt.xlabel(x)
    plt.ylabel(y)
    plt.colorbar(label='count')
    plt.tight_layout()
    if fname:
        plt.savefig(FIG_DIR / fname, dpi=150)
    plt.close()


def candidate_breakpoints(values: np.ndarray, metric: np.ndarray, num_breaks: int = 5) -> List[int]:
    """Return candidate breakpoint positions where the slope of metric over values changes sharply.

    Simple heuristic: compute first derivative and pick the top-k points where derivative magnitude is high.
    """
    order = np.argsort(values)
    v_sorted = values[order]
    m_sorted = metric[order]
    # Finite differences on a smoothed curve (rolling mean)
    window = 20  # smooth window
    if len(v_sorted) < window * 2:
        return []
    smooth = pd.Series(m_sorted).rolling(window, center=True, min_periods=1).mean().values
    deriv = np.diff(smooth) / np.diff(v_sorted)
    # Take absolute derivative and find top peaks, avoiding edges
    peak_idx = np.argpartition(-np.abs(deriv), num_breaks)[:num_breaks]
    candidate_vals = v_sorted[peak_idx + 1]  # +1 due to diff shift
    # Deduplicate & sort
    return sorted(set(int(round(v)) for v in candidate_vals))


def main():
    df = load_cases(DATA_FILE)

    # Scatter plots
    scatter(df, 'miles', 'reimbursement', color='days', fname='scatter_miles_vs_reimb.png')
    scatter(df, 'days', 'reimb_per_day', fname='scatter_days_vs_per_diem.png')
    scatter(df, 'miles', 'reimb_per_mile', color='days', fname='scatter_miles_vs_reimb_per_mile.png')
    scatter(df, 'receipts', 'reimbursement', color='days', fname='scatter_receipts_vs_reimb.png')

    # Heatmaps
    heatmap(df, 'miles', 'reimbursement', fname='heat_miles_vs_reimb.png')
    heatmap(df, 'days', 'reimbursement', fname='heat_days_vs_reimb.png')

    # Breakpoint analysis for mileage tiers
    mileage_breaks = candidate_breakpoints(df['miles'].values, df['reimb_per_mile'].values)
    per_diem_breaks = candidate_breakpoints(df['days'].values, df['reimb_per_day'].values)

    print("\nCandidate mileage tier breakpoints:", mileage_breaks)
    print("Candidate per-diem (days) breakpoints:", per_diem_breaks)

    # Save text summary
    summary_path = Path(__file__).with_suffix('.summary.txt')
    with summary_path.open('w') as f:
        f.write("Mileage tier breakpoints: " + ', '.join(map(str, mileage_breaks)) + "\n")
        f.write("Per-diem day breakpoints: " + ', '.join(map(str, per_diem_breaks)) + "\n")

    print(f"EDA complete. Figures saved to {FIG_DIR.relative_to(Path.cwd())} and summary to {summary_path.name}.")


if __name__ == '__main__':
    main()
import json
from pathlib import Path

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

DATA_FILE = Path(__file__).resolve().parent.parent / 'public_cases.json'


# Helper --------------------------------------------------------------------

def load_df() -> pd.DataFrame:
    with DATA_FILE.open() as f:
        data = json.load(f)
    rows = []
    for c in data:
        inp = c["input"]
        out = c["expected_output"]
        rows.append({
            "days": inp["trip_duration_days"],
            "miles": inp["miles_traveled"],
            "receipts": inp["total_receipts_amount"],
            "reimb": out,
        })
    df = pd.DataFrame(rows)
    df["per_day"] = df["reimb"] / df["days"]
    df["per_mile"] = df["reimb"] / df["miles"].replace(0, np.nan)
    df["miles_per_day"] = df["miles"] / df["days"]
    df["rec_per_day"] = df["receipts"] / df["days"]
    return df


# Analysis ------------------------------------------------------------------

def analyze_per_diem(df: pd.DataFrame) -> pd.DataFrame:
    """Return mean reimbursement per day for day buckets."""
    bins = pd.cut(df["days"], bins=[0, 4, 5, 8, np.inf], labels=["1-4", "5", "6-8", "9+"])
    summary = df.groupby(bins)["per_day"].agg(["count", "mean", "std"])  # type: ignore[return-value]
    return summary


def analyze_mileage_tiers(df: pd.DataFrame) -> pd.DataFrame:
    tiers = pd.cut(
        df["miles"],
        bins=[-1, 100, 275, 916, np.inf],
        labels=["0-100", "101-275", "276-916", "917+"]
    )
    summary = df.groupby(tiers)["per_mile"].agg(["count", "mean", "std"])  # type: ignore[return-value]
    return summary


def analyze_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    eff_bins = pd.cut(
        df["miles_per_day"],
        bins=[-np.inf, 100, 180, 220, 300, np.inf],
        labels=["<100", "100-179", "180-220", "221-300", ">300"]
    )
    summary = df.groupby(eff_bins)["reimb"].agg(["count", "mean", "std"])  # type: ignore[return-value]
    return summary


def analyze_receipts(df: pd.DataFrame) -> pd.DataFrame:
    bins = pd.cut(
        df["receipts"],
        bins=[-1, 50, 600, 800, 1000, np.inf],
        labels=["<50", "50-599", "600-799", "800-999", "1000+"]
    )
    summary = df.groupby(bins)["reimb"].agg(["count", "mean", "std"])  # type: ignore[return-value]
    return summary


def main():
    df = load_df()

    out_lines = []

    out_lines.append("Per-Diem Buckets (reimb per day):\n" + analyze_per_diem(df).to_string())
    out_lines.append("\nMileage Tiers (reimb per mile):\n" + analyze_mileage_tiers(df).to_string())
    out_lines.append("\nEfficiency Bands (total reimb):\n" + analyze_efficiency(df).to_string())
    out_lines.append("\nReceipts Bands (total reimb):\n" + analyze_receipts(df).to_string())

    summary_out = "\n\n".join(out_lines)
    print(summary_out)

    summary_path = Path(__file__).with_suffix('.summary.txt')
    summary_path.write_text(summary_out)
    print(f"Rule harness summary written to {summary_path}")


if __name__ == '__main__':
    main()
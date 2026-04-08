import pandas as pd
import numpy as np
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import math

FILE = "DEVPM_8674_Cal_Poly_Export_dev_activity.csv"
CHUNK_SIZE = 50000
N_WORKERS = 6


def analyze_chunk(chunk: pd.DataFrame) -> dict:
    result = {
        "row_count": len(chunk),
        "missing": chunk.isna().sum().to_dict(),
        "numeric": {},
        "categorical": {},
    }

    numeric_cols = chunk.select_dtypes(include="number").columns
    categorical_cols = chunk.select_dtypes(exclude="number").columns

    for col in numeric_cols:
        s = chunk[col].dropna()
        if len(s) == 0:
            continue
        result["numeric"][col] = {
            "count": int(s.count()),
            "sum": float(s.sum()),
            "min": float(s.min()),
            "max": float(s.max()),
            "sum_sq": float((s ** 2).sum()),
        }

    for col in categorical_cols:
        counts = Counter(chunk[col].astype("string").fillna("<<MISSING>>"))
        result["categorical"][col] = dict(counts)

    return result


def merge_results(results: list[dict]) -> dict:
    merged = {
        "row_count": 0,
        "missing": Counter(),
        "numeric": {},
        "categorical": {},
    }

    for res in results:
        merged["row_count"] += res["row_count"]
        merged["missing"].update(res["missing"])

        for col, stats in res["numeric"].items():
            if col not in merged["numeric"]:
                merged["numeric"][col] = stats.copy()
            else:
                m = merged["numeric"][col]
                m["count"] += stats["count"]
                m["sum"] += stats["sum"]
                m["sum_sq"] += stats["sum_sq"]
                m["min"] = min(m["min"], stats["min"])
                m["max"] = max(m["max"], stats["max"])

        for col, counts in res["categorical"].items():
            if col not in merged["categorical"]:
                merged["categorical"][col] = Counter()
            merged["categorical"][col].update(counts)

    return merged


def finalize_summary(merged: dict) -> tuple[pd.DataFrame, dict]:
    numeric_rows = []

    for col, s in merged["numeric"].items():
        count = s["count"]
        mean = s["sum"] / count if count else np.nan
        variance = (s["sum_sq"] / count) - (mean ** 2) if count else np.nan
        std = math.sqrt(max(variance, 0)) if count else np.nan

        numeric_rows.append({
            "column": col,
            "count": count,
            "mean": mean,
            "std": std,
            "min": s["min"],
            "max": s["max"],
            "missing": merged["missing"][col],
        })

    numeric_summary = pd.DataFrame(numeric_rows).sort_values("column")

    categorical_summary = {}
    for col, counts in merged["categorical"].items():
        categorical_summary[col] = pd.DataFrame(
            counts.most_common(),
            columns=["value", "count"]
        )

    return numeric_summary, categorical_summary


def chunk_generator(file_path: str, chunk_size: int):
    for chunk in pd.read_csv(
        file_path,
        chunksize=chunk_size,
        engine="python",
        on_bad_lines="skip"
    ):
        yield chunk


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=N_WORKERS) as executor:
        results = list(executor.map(analyze_chunk, chunk_generator(FILE, CHUNK_SIZE)))

    merged = merge_results(results)
    numeric_summary, categorical_summary = finalize_summary(merged)

    print("\nNumeric summary:")
    print(numeric_summary)

    for col, df_counts in categorical_summary.items():
        print(f"\nTop values for {col}:")
        print(df_counts.head(10))
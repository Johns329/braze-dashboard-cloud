import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd


BRAZE_KIB_PER_ITEM_ESTIMATE = 2.72
# From prior observed export measurement used in the notebook.
CSV_KIB_PER_ROW_OBSERVED = 1.422742337211544


def _latest_csv(input_dir: str) -> str:
    paths = []
    for name in os.listdir(input_dir):
        if name.lower().endswith(".csv"):
            p = os.path.join(input_dir, name)
            if os.path.isfile(p):
                paths.append(p)

    if not paths:
        raise FileNotFoundError(f"No .csv files found in {input_dir}")

    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths[0]


def _count_rows_fast(path: str) -> int:
    """Counts data rows by counting lines; subtracts header."""
    with open(path, "rb") as f:
        return max(0, sum(1 for _ in f) - 1)


def _find_bad_lines(path: str, expected_cols: int, max_find: int = 10):
    bad = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.reader(f)
        _header = next(r, None)
        for i, row in enumerate(r, start=2):
            if len(row) != expected_cols:
                bad.append({"line": i, "fields": len(row)})
                if len(bad) >= max_find:
                    break
    return bad


def _is_empty_obj_series(s: pd.Series) -> pd.Series:
    # Treat NaN + whitespace-only strings as empty.
    s2 = s.fillna("")
    return s2.astype(str).str.strip().eq("")


def build_catalog_composition(
    input_csv: str,
    output_dir: str,
    chunk_size: int = 50_000,
    top_n: int = 15,
):
    os.makedirs(output_dir, exist_ok=True)

    # Header / expected col count
    header_df = pd.read_csv(input_csv, nrows=1, low_memory=False)
    expected_cols = len(header_df.columns)
    rows_by_linecount = _count_rows_fast(input_csv)
    bad_lines = _find_bad_lines(input_csv, expected_cols, max_find=10)

    file_bytes = os.path.getsize(input_csv)
    file_mib = file_bytes / (1024**2)

    empty_counts = defaultdict(int)
    non_empty_counts = defaultdict(int)

    # For string heaviness
    str_total_len = defaultdict(int)
    str_non_empty = defaultdict(int)

    # For weight proxy
    str_bytes = defaultdict(int)
    col_kind = {}

    DEFAULT_BYTES = {
        "bool": 1,
        "int": 8,
        "float": 8,
        "datetime": 8,
        "other": 8,
    }

    good_rows = 0
    cols = None

    # Iterate file in chunks (skip malformed rows).
    for chunk in pd.read_csv(
        input_csv,
        chunksize=chunk_size,
        low_memory=False,
        on_bad_lines="skip",
    ):
        good_rows += len(chunk)
        if cols is None:
            cols = list(chunk.columns)

        for c in chunk.columns:
            s = chunk[c]

            if s.dtype == "object":
                empty_mask = _is_empty_obj_series(s)
                empties = int(empty_mask.sum())
                nonempty = int(len(s) - empties)
                empty_counts[c] += empties
                non_empty_counts[c] += nonempty

                # Accumulate string lengths for non-empty values.
                s2 = s[~empty_mask]
                if len(s2) > 0:
                    lens = s2.astype(str).str.len()
                    total_len = int(lens.sum())
                    n = int(len(lens))
                    str_total_len[c] += total_len
                    str_non_empty[c] += n
                    str_bytes[c] += total_len

                # Infer kind (best-effort heuristic; matches the notebook's intent).
                if c not in col_kind:
                    sample = s.dropna().astype(str).head(200)
                    if len(sample) > 0 and (
                        (sample.str.contains(":").mean() > 0.5)
                        or (sample.str.contains("-").mean() > 0.7)
                    ):
                        col_kind[c] = "datetime"
                    else:
                        col_kind[c] = "string"
            else:
                # Non-object: empty is NaN.
                empties = int(s.isna().sum())
                nonempty = int(len(s) - empties)
                empty_counts[c] += empties
                non_empty_counts[c] += nonempty

                if c not in col_kind:
                    if s.dtype == "bool":
                        col_kind[c] = "bool"
                    elif np.issubdtype(s.dtype, np.integer):
                        col_kind[c] = "int"
                    elif np.issubdtype(s.dtype, np.floating):
                        col_kind[c] = "float"
                    else:
                        col_kind[c] = "other"

    if cols is None:
        raise RuntimeError("No rows found while reading CSV")

    total_cells = good_rows * len(cols)
    non_empty_cells = sum(int(v) for v in non_empty_counts.values())
    overall_filled_pct = (non_empty_cells / total_cells * 100) if total_cells else 0.0

    # Fill rates
    fill_rows = []
    for c in cols:
        ne = int(non_empty_counts.get(c, 0))
        em = int(empty_counts.get(c, 0))
        fr = (ne / good_rows * 100) if good_rows else 0.0
        fill_rows.append(
            {
                "field_name": c,
                "fill_rate_pct": round(fr, 2),
                "non_empty_count": ne,
                "empty_count": em,
            }
        )
    fill_df = pd.DataFrame(fill_rows).sort_values(
        ["fill_rate_pct", "field_name"], ascending=[True, True], kind="mergesort"
    )

    # Heaviest strings by avg length
    heavy_rows = []
    for c in cols:
        n = int(str_non_empty.get(c, 0))
        if n > 0:
            avg_len = float(str_total_len[c]) / n
            heavy_rows.append(
                {
                    "field_name": c,
                    "avg_len": round(avg_len, 1),
                    "non_empty_count": n,
                }
            )
    heavy_df = (
        pd.DataFrame(heavy_rows)
        .sort_values(
            ["avg_len", "field_name"], ascending=[False, True], kind="mergesort"
        )
        .reset_index(drop=True)
    )

    # Weight proxy
    est_bytes = {}
    for c in cols:
        # If we observed string bytes, use those.
        if str_bytes.get(c, 0) > 0 or col_kind.get(c) == "string":
            est_bytes[c] = int(str_bytes.get(c, 0))
        else:
            kind = col_kind.get(c, "other")
            est_bytes[c] = int(non_empty_counts.get(c, 0)) * int(
                DEFAULT_BYTES.get(kind, DEFAULT_BYTES["other"])
            )

    total_est = int(sum(est_bytes.values()))
    ranked = sorted(est_bytes.items(), key=lambda x: x[1], reverse=True)
    top25 = ranked[:25]
    top10 = ranked[:10]
    top10_pct = (sum(b for _, b in top10) / total_est * 100) if total_est else 0.0

    weights_rows = []
    for c, b in top25:
        pct = (b / total_est * 100) if total_est else 0.0
        weights_rows.append(
            {
                "field_name": c,
                "est_mib": round(b / 1024 / 1024, 2),
                "pct_total": round(pct, 2),
                "kind": col_kind.get(c, "unknown"),
                "non_empty_count": int(non_empty_counts.get(c, 0)),
            }
        )
    weights_df = pd.DataFrame(weights_rows)

    # Braze size proxy (estimate)
    csv_kib_per_good_row = (file_mib * 1024) / max(good_rows, 1)
    overhead_mult = BRAZE_KIB_PER_ITEM_ESTIMATE / CSV_KIB_PER_ROW_OBSERVED
    est_braze_mib_A = (good_rows * BRAZE_KIB_PER_ITEM_ESTIMATE) / 1024
    est_braze_mib_B = file_mib * overhead_mult

    def mib_to_mb_decimal(mib: float) -> float:
        return mib * (1024**2) / (1000**2)

    overview = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_file": os.path.basename(input_csv),
        "file_size_bytes": file_bytes,
        "file_size_mib": round(file_mib, 2),
        "rows_linecount": int(rows_by_linecount),
        "good_rows": int(good_rows),
        "columns": int(len(cols)),
        "first_bad_rows": bad_lines,
        "overall_filled_pct": round(float(overall_filled_pct), 2),
        "csv_kib_per_good_row": round(float(csv_kib_per_good_row), 4),
        "braze_kib_per_item_estimate": BRAZE_KIB_PER_ITEM_ESTIMATE,
        "csv_kib_per_row_observed": CSV_KIB_PER_ROW_OBSERVED,
        "braze_overhead_multiplier": round(float(overhead_mult), 3),
        "est_braze_mib_method_a": round(float(est_braze_mib_A), 2),
        "est_braze_mb_method_a": round(float(mib_to_mb_decimal(est_braze_mib_A)), 2),
        "est_braze_mib_method_b": round(float(est_braze_mib_B), 2),
        "est_braze_mb_method_b": round(float(mib_to_mb_decimal(est_braze_mib_B)), 2),
        "weight_proxy_total_mib": round(float(total_est / 1024 / 1024), 2),
        "top10_weight_proxy_pct": round(float(top10_pct), 2),
    }

    # Write outputs
    with open(
        os.path.join(output_dir, "catalog_composition_overview.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(overview, f, indent=2)

    fill_df.to_csv(
        os.path.join(output_dir, "catalog_composition_fill_rates.csv"), index=False
    )
    fill_df.head(top_n).to_csv(
        os.path.join(output_dir, f"catalog_composition_sparsest_{top_n}.csv"),
        index=False,
    )
    fill_df.tail(top_n).sort_values(
        ["fill_rate_pct", "field_name"], ascending=[False, True], kind="mergesort"
    ).to_csv(
        os.path.join(output_dir, f"catalog_composition_most_filled_{top_n}.csv"),
        index=False,
    )

    heavy_df.head(top_n).to_csv(
        os.path.join(output_dir, f"catalog_composition_heaviest_strings_{top_n}.csv"),
        index=False,
    )
    weights_df.to_csv(
        os.path.join(output_dir, "catalog_composition_top_weights_25.csv"), index=False
    )

    return overview


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build small catalog composition artifacts for Streamlit"
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Input catalog CSV path (defaults to newest CSV in data/latest_catalog)",
    )
    parser.add_argument(
        "--input-dir",
        default=os.path.join("data", "latest_catalog"),
        help="Directory to search for newest CSV when --input is not provided",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("data", "tables"),
        help="Where to write summary artifacts",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50_000,
        help="Pandas chunk size",
    )
    args = parser.parse_args()

    input_csv = args.input
    if input_csv is None:
        input_csv = _latest_csv(args.input_dir)

    overview = build_catalog_composition(
        input_csv=input_csv,
        output_dir=args.output_dir,
        chunk_size=args.chunk_size,
    )
    print("Wrote catalog composition artifacts to", args.output_dir)
    print("Input:", input_csv)
    print(
        "Filled %:",
        overview["overall_filled_pct"],
        "Good rows:",
        f"{overview['good_rows']:,}",
        "Columns:",
        overview["columns"],
    )
    print(
        "Braze size est (Method A):",
        f"{overview['est_braze_mib_method_a']:,.1f} MiB",
        f"(~{overview['est_braze_mb_method_a']:,.1f} MB)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

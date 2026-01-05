#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Augment a transformed ReposVul dataset with synthetic samples.

Inputs:
- ReposVul (transformed) CSVs:
    - train.csv (required)
    - val.csv   (optional; if not provided, auto-detect in same folder as train.csv)
    - test.csv  (optional; if not provided, auto-detect in same folder as train.csv)

- Synthetic CSVs:
    - codelama_vulnerable.csv (required)
    - codelama_non_vulnerable.csv (required)

Outputs:
- out_dir/train_aug.csv (always)
- out_dir/val.csv  (only if available from input or auto-detected)
- out_dir/test.csv (only if available from input or auto-detected)

Mapping (per user requirements):
- processed_func <- synthetic 'code'
- target <- synthetic 'target' but forced to 1 for vulnerable, 0 for non-vulnerable
- vul_func_with_fix <- "-"
- cve_id <- "-"
- cwe_id <- from vuln CSV column 'cwe', keep only CWE-XXX, stored as "['CWE-XXX']"
          for non-vuln: "['-']"
- commit_id <- "-"
- file_path <- "-"
- file_language <- "C"
"""

import argparse
import hashlib
import os
import re
from typing import Optional

import pandas as pd


# -----------------------------
# Helpers
# -----------------------------

def clean_code(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\x00", "")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()


_CWE_RE = re.compile(r"(CWE-\d+)", re.IGNORECASE)


def extract_cwe_list(cwe_cell: Optional[str]) -> str:
    """
    Returns a string representation of a Python list, e.g. "['CWE-119']".
    If no CWE id is found, returns "['-']".
    """
    if cwe_cell is None:
        return "['-']"
    m = _CWE_RE.search(str(cwe_cell))
    if not m:
        return "['-']"
    return f"['{m.group(1).upper()}']"


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def ensure_reposvul_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the dataframe contains the ReposVul/LineVul expected columns.
    """
    required_cols = [
        "processed_func", "target", "vul_func_with_fix",
        "cve_id", "cwe_id", "commit_id", "file_path", "file_language",
        "flaw_line_index", "flaw_line"
    ]
    for c in required_cols:
        if c not in df.columns:
            if c == "flaw_line_index":
                df[c] = "[]"  # leere Liste als String
            elif c == "flaw_line":
                df[c] = ""   # leerer String
            else:
                df[c] = "-"

    # Normalize
    df["processed_func"] = df["processed_func"].astype(str).map(clean_code)
    df["target"] = pd.to_numeric(df["target"], errors="coerce").fillna(0).astype(int)
    df["vul_func_with_fix"] = df["vul_func_with_fix"].astype(str).fillna("-")
    df["cve_id"] = df["cve_id"].astype(str).fillna("-")
    df["cwe_id"] = df["cwe_id"].astype(str).fillna("['-']")
    df["commit_id"] = df["commit_id"].astype(str).fillna("-")
    df["file_path"] = df["file_path"].astype(str).fillna("-")
    df["file_language"] = df["file_language"].astype(str).fillna("C")
    df["flaw_line_index"] = df["flaw_line_index"].astype(str).fillna("[]")
    df["flaw_line"] = df["flaw_line"].astype(str).fillna("")

    # Return in fixed order (with flaw_line_index, flaw_line at the end)
    return df[required_cols]


def deduplicate_by_code(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate rows by processed_func hash.    
    """
    tmp = df.copy()
    tmp["_h"] = tmp["processed_func"].map(stable_hash)
    tmp = tmp.drop_duplicates(subset=["_h"]).drop(columns=["_h"])
    return tmp


def remove_overlap_by_code(base_df: pd.DataFrame, candidates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows from candidates_df whose processed_func hash exists in base_df.
    """
    base_h = set(base_df["processed_func"].map(stable_hash).tolist())
    cand = candidates_df.copy()
    cand["_h"] = cand["processed_func"].map(stable_hash)
    cand = cand[~cand["_h"].isin(base_h)].drop(columns=["_h"])
    return cand


def _select_code_series(df: pd.DataFrame) -> pd.Series:
    """Prefer processed_func if present, otherwise fall back to code."""
    if "processed_func" in df.columns:
        return df["processed_func"]
    if "code" in df.columns:
        return df["code"]
    raise ValueError("Synthetic CSV must contain 'processed_func' or 'code'.")


def synth_to_reposvul_rows(vuln_csv: str, nonvuln_csv: str, keep_only_complete: bool) -> pd.DataFrame:
    """
    Convert synthetic CSVs to ReposVul format using processed_func when available.

    """
    v = pd.read_csv(vuln_csv)
    n = pd.read_csv(nonvuln_csv)

    # Optional quality filter
    if keep_only_complete and "is_complete" in v.columns:
        v = v[v["is_complete"] == True]
    if keep_only_complete and "is_complete" in n.columns:
        n = n[n["is_complete"] == True]

    v_code = _select_code_series(v).map(clean_code)
    n_code = _select_code_series(n).map(clean_code)

    v_out = pd.DataFrame({
        "processed_func": v_code,
        "target": 1,  # forced
        "vul_func_with_fix": "-",
        "cve_id": "-",
        "cwe_id": v["cwe"].map(extract_cwe_list) if "cwe" in v.columns else "['-']",
        "commit_id": "-",
        "file_path": "-",
        "file_language": "C",
    })

    n_out = pd.DataFrame({
        "processed_func": n_code,
        "target": 0,  # forced
        "vul_func_with_fix": "-",
        "cve_id": "-",
        "cwe_id": "['-']",
        "commit_id": "-",
        "file_path": "-",
        "file_language": "C",
    })

    out = pd.concat([v_out, n_out], ignore_index=True)

    # Drop empty code
    out = out[out["processed_func"].str.len() > 0].copy()

    return ensure_reposvul_schema(out)


def auto_detect_split(train_csv: str, split_name: str) -> Optional[str]:
    """
    If raw_val/test not provided, try to locate val.csv/test.csv in same directory.
    """
    train_dir = os.path.dirname(os.path.abspath(train_csv))
    cand = os.path.join(train_dir, f"{split_name}.csv")
    return cand if os.path.exists(cand) else None


def label_dist(df: pd.DataFrame) -> dict:
    return df["target"].value_counts(dropna=False).to_dict()


def add_index_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 0-based index column as the first column.
    """
    out = df.copy()
    out.insert(0, "index", range(len(out)))
    return out


# -----------------------------
# Main
# -----------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_train", required=True, help="Path to reposvul train.csv")
    ap.add_argument("--raw_val", required=False, default=None, help="Path to reposvul val.csv (optional)")
    ap.add_argument("--raw_test", required=False, default=None, help="Path to reposvul test.csv (optional)")

    ap.add_argument("--csv_vuln", required=True, help="Path to codelama_vulnerable.csv")
    ap.add_argument("--csv_nonvuln", required=True, help="Path to codelama_non_vulnerable.csv")

    ap.add_argument("--out_dir", required=True, help="Output directory")

    ap.add_argument("--dedup_within_synth", action="store_true",
                    help="Deduplicate synthetic samples by processed_func hash")
    ap.add_argument("--dedup_against_raw_train", action="store_true",
                    help="Remove synthetic samples that overlap with reposvul train by processed_func hash")
    ap.add_argument("--keep_only_complete", action="store_true",
                    help="Keep only synth rows where is_complete == True (if column exists)")
    ap.add_argument("--augment_split", choices=["train_only", "all"], default="train_only",
                    help="Default train_only avoids leakage into val/test")

    args = ap.parse_args()

    # Load reposvul train
    train = ensure_reposvul_schema(pd.read_csv(args.raw_train))

    # Resolve val/test paths (optional)
    val_path = args.raw_val or auto_detect_split(args.raw_train, "val")
    test_path = args.raw_test or auto_detect_split(args.raw_train, "test")

    val = ensure_reposvul_schema(pd.read_csv(val_path)) if val_path else None
    test = ensure_reposvul_schema(pd.read_csv(test_path)) if test_path else None

    # Build synth rows
    synth = synth_to_reposvul_rows(
        vuln_csv=args.csv_vuln,
        nonvuln_csv=args.csv_nonvuln,
        keep_only_complete=args.keep_only_complete,
    )

    if args.dedup_within_synth:
        synth = deduplicate_by_code(synth)

    if args.dedup_against_raw_train:
        synth = remove_overlap_by_code(train, synth)

    # Augment
    if args.augment_split == "train_only":
        train_aug = pd.concat([train, synth], ignore_index=True)
        val_aug = val
        test_aug = test
    else:
        # Not recommended: can leak synthetic distribution into eval
        train_aug = pd.concat([train, synth], ignore_index=True)
        val_aug = pd.concat([val, synth], ignore_index=True) if val is not None else None
        test_aug = pd.concat([test, synth], ignore_index=True) if test is not None else None

    # Final cleanup
    train_aug = ensure_reposvul_schema(train_aug[train_aug["processed_func"].str.len() > 0].copy())
    if val_aug is not None:
        val_aug = ensure_reposvul_schema(val_aug[val_aug["processed_func"].str.len() > 0].copy())
    if test_aug is not None:
        test_aug = ensure_reposvul_schema(test_aug[test_aug["processed_func"].str.len() > 0].copy())

    # Add explicit index column as first column
    train_aug = add_index_column(train_aug)
    if val_aug is not None:
        val_aug = add_index_column(val_aug)
    if test_aug is not None:
        test_aug = add_index_column(test_aug)

    # Write outputs
    os.makedirs(args.out_dir, exist_ok=True)

    out_train = os.path.join(args.out_dir, "train_aug.csv")
    train_aug.to_csv(out_train, index=False)

    print("=== OUTPUTS ===")
    print(f"Train_aug: {out_train} rows={len(train_aug)} label_dist={label_dist(train_aug)}")
    print(f"Synth used rows={len(synth)} label_dist={label_dist(synth)}")

    if val_aug is not None:
        out_val = os.path.join(args.out_dir, "val.csv")
        val_aug.to_csv(out_val, index=False)
        print(f"Val:      {out_val} rows={len(val_aug)} label_dist={label_dist(val_aug)}")
    else:
        print("Val:      (not provided and not auto-detected) -> not written")

    if test_aug is not None:
        out_test = os.path.join(args.out_dir, "test.csv")
        test_aug.to_csv(out_test, index=False)
        print(f"Test:     {out_test} rows={len(test_aug)} label_dist={label_dist(test_aug)}")
    else:
        print("Test:     (not provided and not auto-detected) -> not written")


if __name__ == "__main__":
    main()


"""
--deduplicate_by_code: Deduplicate synthetic samples by processed_func hash.
We deduplicate synthetically generated samples by function body to prevent training bias caused by repeated code fragments produced by large language models.

--dedup_within_synth: Remove duplicate synthetic samples within the synthetic dataset itself.
When generating synthetic data, large language models may produce identical or near-identical code snippets multiple times. This option ensures that each synthetic sample is unique within the synthetic dataset.

--dedup_against_raw_train: Remove synthetic samples that overlap with reposvul train by processed_func hash.
To avoid implicit data leakage and artificial performance gains, synthetic samples that overlap with the original training set are removed.

--keep_only_complete: Keep only synthetic rows where is_complete == True (if column exists).
We restrict synthetic augmentation to complete functions to avoid introducing label noise and syntactic artifacts.

--augment_split: Choose whether to augment only the training split or all splits (train, val, test).
By default, only the training split is augmented to prevent leakage of synthetic data characteristics into validation and test sets, which could skew evaluation metrics.
Synthetic data is used exclusively for training, while validation and testing are performed on real-world vulnerabilities to ensure an unbiased evaluation.

"""
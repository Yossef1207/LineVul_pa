#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import json
import os
import random
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

def as_list(x: Any) -> List[Any]:
    """
    write a docstring for the function
    Converts the input x into a list.
    """
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def clean_code(s: Optional[str]) -> str:
    """
    Cleans code string by removing null characters and normalizing line endings.
    """
    if not s:
        return ""
    s = str(s).replace("\x00", "")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()

def to_int_label(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, (int, float)):
        v = int(x)
        return v if v in (0, 1) else None
    if isinstance(x, str):
        t = x.strip().lower()
        if t in ("0", "1"):
            return int(t)
        if t in ("false", "true"):
            return 1 if t == "true" else 0
    return None

def extract_code_and_label(detail: Dict[str, Any]) -> Tuple[str, Optional[int], str]:
    """
    Extracts before code, label, and after code from a detail dictionary.
    The extraction follows these rules:
    - Before code is taken from `function_before` if available, otherwise from `code_before` or `code`.
    - Label is taken from `function_before.target` if available, otherwise from `details.target
    - After code is taken from `function_after` if available, otherwise from `patch`.
    Returns a tuple of (before_code, label, after_code).
    """

    # --- label: prefer function_before.target, else details.target, else function_after.target
    label = None

    fb = detail.get("function_before")
    fa = detail.get("function_after")

    # function_before can be dict / list / string / missing
    def get_fb_code_and_label(x: Any) -> Tuple[str, Optional[int]]:
        if isinstance(x, dict):
            code = clean_code(x.get("function") or x.get("code_before") or x.get("code") or "")
            lab = to_int_label(x.get("target"))
            return code, lab
        if isinstance(x, str):
            # sometimes stored directly as string
            return clean_code(x), None
        return "", None

    def get_fa_code(x: Any) -> str:
        if isinstance(x, dict):
            return clean_code(x.get("function") or x.get("code") or "")
        if isinstance(x, str):
            return clean_code(x)
        return ""

    # before code candidates
    before_code = ""
    fb_items = as_list(fb)
    if fb_items:
        # take first by default (or you can iterate all; kept simple)
        before_code, label = get_fb_code_and_label(fb_items[0])

    # fallback code if function_before missing / empty
    if not before_code:
        before_code = clean_code(detail.get("code_before") or detail.get("code") or "")

    # fallback label from details.target
    if label is None:
        label = to_int_label(detail.get("target"))

    # after code candidates
    after_code = ""
    fa_items = as_list(fa)
    if fa_items:
        after_code = get_fa_code(fa_items[0])

    if not after_code:
        # patch often exists per README
        after_code = clean_code(detail.get("patch") or "")

    if not after_code:
        after_code = before_code  # safe fallback so CSV isn't empty

    return before_code, label, after_code

def read_jsonl(path: str) -> Iterable[Dict[str, Any]]:
    """
    Reads a JSONL file and yields each line as a JSON object.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def iter_rows(jsonl_path: str, filter_lang: str, stats: Counter, debug_n: int = 0) -> Iterable[Dict[str, Any]]:
    """
    Iterates over rows in a JSONL file, applying filtering and extraction logic.
    Yields dictionaries suitable for CSV output.
    """
    dbg_left = debug_n

    for obj in read_jsonl(jsonl_path):
        details = obj.get("details")
        if details is None:
            stats["skip_no_details"] += 1
            if dbg_left > 0:
                print("[DEBUG] no 'details' keys:", list(obj.keys()))
                dbg_left -= 1
            continue

        for d in as_list(details):
            if not isinstance(d, dict):
                stats["skip_detail_not_dict"] += 1
                continue

            file_lang = (d.get("file_language") or obj.get("cve_language") or "").strip()
            # if filter_lang:
            #     if file_lang.lower() != filter_lang.strip().lower():
            #         stats["skip_lang_mismatch"] += 1
            #         continue

            before_code, label, after_code = extract_code_and_label(d)

            if not before_code:
                stats["skip_no_code"] += 1
                if dbg_left > 0:
                    print("[DEBUG] missing code; detail keys:", list(d.keys()))
                    dbg_left -= 1
                continue

            if label is None:
                stats["skip_no_label"] += 1
                if dbg_left > 0:
                    print("[DEBUG] missing label; sample detail.target/function_before:", d.get("target"), d.get("function_before"))
                    dbg_left -= 1
                continue

            stats["kept"] += 1

            yield {
                # LineVul expects these columns. :contentReference[oaicite:3]{index=3}
                "processed_func": before_code,
                "target": int(label),
                "vul_func_with_fix": after_code,

                # optional metadata for tracing
                "cve_id": obj.get("cve_id") or "",
                "cwe_id": obj.get("cwe_id") or "",
                "commit_id": obj.get("commit_id") or "",
                "file_path": d.get("file_path") or "",
                "file_language": file_lang,
            }

def write_csv(rows: Iterable[Dict[str, Any]], out_csv: str, fieldnames: List[str]) -> int:
    """
    Writes rows to a CSV file with specified fieldnames.
    Returns the number of rows written.
    """
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    n = 0
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow(r)
            n += 1
    return n

def stratified_split(rows: List[Dict[str, Any]], seed: int, ratios=(0.8, 0.1, 0.1)):
    """
    Splits the dataset into train/val/test sets while preserving class distribution.
    Returns three lists: train, val, test.  
    """
    random.seed(seed)
    pos = [r for r in rows if r["target"] == 1]
    neg = [r for r in rows if r["target"] == 0]
    random.shuffle(pos); random.shuffle(neg)

    def split_bucket(b):
        n = len(b)
        n_tr = int(n * ratios[0]); n_va = int(n * ratios[1])
        return b[:n_tr], b[n_tr:n_tr+n_va], b[n_tr+n_va:]

    p_tr, p_va, p_te = split_bucket(pos)
    n_tr, n_va, n_te = split_bucket(neg)

    train = p_tr + n_tr
    val   = p_va + n_va
    test  = p_te + n_te
    random.shuffle(train); random.shuffle(val); random.shuffle(test)
    return train, val, test

def main():
    """
    Docstring for main
    Main function to parse arguments and transform dataset.
    1. Parses command-line arguments for input/output paths and options.    
    2. Defines fieldnames for CSV output.
    3. Defines a helper function `transform_one` to process a single JSONL file and write to CSV.
    4. Depending on provided arguments, either processes separate train/val/test JSONL files
         or a single all-encompassing JSONL file.
    5. If using a single JSONL file, performs a stratified split into train/val/test sets.
    6. Outputs the resulting CSV files to the specified output directory.
    7. Prints statistics about the number of samples processed and skipped.
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_jsonl", type=str, default=None)
    ap.add_argument("--val_jsonl", type=str, default=None)
    ap.add_argument("--test_jsonl", type=str, default=None)
    ap.add_argument("--all_jsonl", type=str, default=None)
    ap.add_argument("--out_dir", type=str, required=True)
    ap.add_argument("--seed", type=int, default=123456)
    ap.add_argument("--filter_lang", type=str, default="", help='Exact match on file_language, e.g. "C" or "C++"')
    ap.add_argument("--debug_n", type=int, default=0, help="Print debug info for first N skipped samples")
    args = ap.parse_args()

    fieldnames = [
        "processed_func", "target", "vul_func_with_fix",
        "cve_id", "cwe_id", "commit_id", "file_path", "file_language"
    ]

    def transform_one(in_path: str, out_path: str) -> Tuple[int, Counter]:
        stats = Counter()
        rows = iter_rows(in_path, args.filter_lang, stats, debug_n=args.debug_n)
        n = write_csv(rows, out_path, fieldnames)
        return n, stats

    out_train = os.path.join(args.out_dir, "train.csv")
    out_val   = os.path.join(args.out_dir, "val.csv")
    out_test  = os.path.join(args.out_dir, "test.csv")

    if args.train_jsonl and args.val_jsonl and args.test_jsonl:
        n1, s1 = transform_one(args.train_jsonl, out_train)
        n2, s2 = transform_one(args.val_jsonl,   out_val)
        n3, s3 = transform_one(args.test_jsonl,  out_test)
        print("Train:", n1, dict(s1))
        print("Val:  ", n2, dict(s2))
        print("Test: ", n3, dict(s3))
        return

    if not args.all_jsonl:
        raise SystemExit("Provide either (train/val/test JSONL) or --all_jsonl")

    stats = Counter()
    all_rows = list(iter_rows(args.all_jsonl, args.filter_lang, stats, debug_n=args.debug_n))
    print("All:", len(all_rows), dict(stats))

    train, val, test = stratified_split(all_rows, seed=args.seed)
    write_csv(train, out_train, fieldnames)
    write_csv(val,   out_val,   fieldnames)
    write_csv(test,  out_test,  fieldnames)

    print(f"Wrote train={len(train)} val={len(val)} test={len(test)} into {args.out_dir}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import csv
import os
import re
from pathlib import Path
from typing import Dict, Optional


METRIC_KEYS = [
    "test_accuracy",
    "test_f1",
    "test_precision",
    "test_recall",
    "test_threshold",
]


def parse_filename(path: Path) -> Dict[str, str]:
    """Infer dataset (primevul/reposvul) and train_variant from log filename.

    Expected patterns like:
      test_with_primevul_only.log
      test_with_primevul_codellama.log
      test_with_primevul_gpt-4o.log
      test_with_primevul_vul_codellama.log
      test_with_primevul_vul_gpt-4o.log
      ... and the same for reposvul.
    """
    name = path.name
    base = name
    if base.startswith("test_with_"):
        base = base[len("test_with_"):]
    if base.endswith(".log"):
        base = base[:-4]

    # base e.g. "primevul_only", "primevul_vul_codellama"
    if "_" in base:
        dataset, rest = base.split("_", 1)
        train_variant = rest
    else:
        dataset, train_variant = base, "unknown"

    return {"log_file": name, "dataset": dataset, "train_variant": train_variant}


def parse_log_file(path: Path, tail_lines: int = 80) -> Optional[Dict[str, str]]:
    """Parse a single log file and extract metrics + TP indices from the last N lines."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None

    if not lines:
        return None

    tail = "".join(lines[-tail_lines:])

    result: Dict[str, str] = {}

    # Extract metrics like: "test_accuracy = 0.9274"
    for key in METRIC_KEYS:
        m = re.search(rf"{key}\s*=\s*([0-9.]+)", tail)
        if m:
            result[key] = m.group(1)

    # Extract True Positive indices line (keep as string list)
    m_tp = re.search(
        r"True Positive indices \(dataset order\):\s*(\[[^\]]*\])",
        tail,
    )
    if m_tp:
        result["true_positive_indices"] = m_tp.group(1)
    else:
        result["true_positive_indices"] = "[]"

    # If we didn't find at least accuracy and f1, treat as not a completed test log
    if "test_accuracy" not in result and "test_f1" not in result:
        return None

    return result


def collect_results(log_dir: Path) -> Dict[str, Dict[str, str]]:
    """Collect results from all test_with_*.log files in a directory."""
    results: Dict[str, Dict[str, str]] = {}
    for path in sorted(log_dir.glob("test_with_*.log")):
        parsed_metrics = parse_log_file(path)
        if not parsed_metrics:
            continue
        meta = parse_filename(path)
        row: Dict[str, str] = {}
        row.update(meta)
        for key in METRIC_KEYS:
            row[key] = parsed_metrics.get(key, "")
        row["true_positive_indices"] = parsed_metrics.get("true_positive_indices", "[]")
        results[path.name] = row
    return results


def write_csv(results: Dict[str, Dict[str, str]], output_path: Path) -> None:
    fieldnames = [
        "log_file",
        "dataset",
        "train_variant",
        *METRIC_KEYS,
        "true_positive_indices",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for _, row in sorted(results.items()):
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Collect LineVul test metrics from log files and write a summary CSV. "
            "It expects logs like 'test_with_primevul_only.log' in the given directory."
        )
    )
    parser.add_argument(
        "log_dir",
        nargs="?",
        default="./best_testing_logs",
        help="Directory containing test_with_*.log files (default: ./best_testing_logs)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="test_summary_results.csv",
        help=(
            "Pfad zur Ausgabedatei (CSV). Wenn relativ, wird sie im Log-Verzeichnis "
            "abgelegt. Standard: test_summary_results.csv"
        ),
    )

    args = parser.parse_args()

    log_dir = Path(args.log_dir).expanduser().resolve()
    if not log_dir.is_dir():
        raise SystemExit(f"Log-Verzeichnis existiert nicht: {log_dir}")

    # Output-Pfad ggf. relativ zum Log-Verzeichnis interpretieren
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = log_dir / output_path

    results = collect_results(log_dir)
    if not results:
        raise SystemExit(f"Keine auswertbaren Logs in {log_dir} gefunden.")

    write_csv(results, output_path)
    print(f"Geschriebene Zusammenfassung: {output_path}")


if __name__ == "__main__":
    main()


"""
cd LineVul_pa/linevul

# Standard: liest ./best_testing_logs und schreibt test_summary_results.csv dort hinein
python collect_test_results.py

# Oder mit explizitem Pfad und Ausgabedatei
python collect_test_results.py ./testing_logs -o my_results.csv
"""
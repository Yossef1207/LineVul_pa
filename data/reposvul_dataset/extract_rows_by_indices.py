#!/usr/bin/env python3
import argparse
import ast
import csv
import os
import sys
from typing import List


def parse_indices(indices_arg: str) -> List[int]:
    """Parse the indices argument which can be like "1,2,3" or "[1, 2, 3]"."""
    indices_arg = indices_arg.strip()
    # Try to parse as Python literal list first
    try:
        value = ast.literal_eval(indices_arg)
        if isinstance(value, (list, tuple)):
            return [int(x) for x in value]
        # fall through to comma-split if it's not a list/tuple
    except (SyntaxError, ValueError):
        pass

    # Fallback: comma-separated string
    if not indices_arg:
        return []
    return [int(part.strip()) for part in indices_arg.split(',') if part.strip()]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract rows from a CSV test file given zero-based dataset indices "
            "(as used in the logs) and write them to a TXT file."
        )
    )
    parser.add_argument(
        "csv_path",
        help="Pfad zur test.csv (z.B. LineVul_pa/data/reposvul_dataset/test.csv)",
    )
    parser.add_argument(
        "indices",
        help=(
            "Liste der Indizes, entweder als Python-Liste (z.B. '[2, 67, 71]') "
            "oder als Komma-getrennte Liste (z.B. '2,67,71'). Indizes sind 0-basiert "
            "wie in den Logs (dataset order)."
        ),
    )

    args = parser.parse_args()
    indices = sorted(set(parse_indices(args.indices)))

    if not indices:
        print("Keine gültigen Indizes angegeben.")
        return

    # CSV-Modul für sehr große Felder konfigurieren (z.B. Quellcode-Spalten)
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        # Fallback auf einen großen, aber sichereren Wert
        csv.field_size_limit(10**8)

    # Ziel-Dateiname im gleichen Ordner wie die CSV anlegen
    base_dir = os.path.dirname(os.path.abspath(args.csv_path))
    base_name = os.path.splitext(os.path.basename(args.csv_path))[0]
    out_path = os.path.join(base_dir, f"{base_name}_selected_indices.txt")

    # Wir gehen davon aus, dass die Indizes sich auf die Datenzeilen beziehen
    # (Zeile 0 = erste Datenzeile nach dem Header).
    with open(args.csv_path, newline="", encoding="utf-8") as f_in, open(
        out_path, "w", encoding="utf-8"
    ) as f_out:
        reader = csv.reader(f_in)
        header = next(reader, None)

        # Header optional oben in die TXT-Datei schreiben
        if header is not None:
            f_out.write(",".join(header) + "\n")

        for row_idx, row in enumerate(reader):
            if row_idx in indices:
                f_out.write(",".join(row) + "\n")

    print(f"Geschriebene Datei: {out_path}")


if __name__ == "__main__":
    main()

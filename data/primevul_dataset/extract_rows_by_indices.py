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
            "oder als Komma-getrennte Liste (z.B. '2,67,71'), oder 'all' für alle "
            "Zeilen. Indizes sind 0-basiert wie in den Logs (dataset order)."
        ),
    )
    parser.add_argument(
        "--columns",
        "-c",
        help=(
            "Optionale Komma-getrennte Liste von Spaltennamen aus dem Header, "
            "die in die Ausgabe übernommen werden sollen. Standard: alle Spalten."
        ),
    )
    parser.add_argument(
        "--filter-column",
        "-fc",
        help=(
            "Optional: Name einer Spalte, nach der gefiltert werden soll (z.B. 'cwe_id')."
        ),
    )
    parser.add_argument(
        "--filter-value",
        "-fv",
        help=(
            "Optional: Filterwert, der in der angegebenen Spalte vorkommen muss. "
            "Es wird eine einfache Teilstring-Suche gemacht, z.B. 'CWE-362' in "
            "cwe_id-Spalte, die JSON-Listen wie ['CWE-362'] enthält."
        ),
    )

    args = parser.parse_args()
    raw_indices = args.indices.strip()
    if raw_indices.lower() == "all":
        indices = None  # keine Einschränkung nach Zeilenindex
    else:
        indices = sorted(set(parse_indices(raw_indices)))

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
        reader = csv.DictReader(f_in)

        if reader.fieldnames is None:
            print("CSV-Datei hat keinen Header.", file=sys.stderr)
            sys.exit(1)

        # Spaltenauswahl vorbereiten
        if args.columns:
            selected_columns = [
                col.strip() for col in args.columns.split(",") if col.strip()
            ]
        else:
            selected_columns = list(reader.fieldnames)

        # Prüfen, ob alle gewünschten Spalten existieren
        missing = [c for c in selected_columns if c not in reader.fieldnames]
        if missing:
            print(
                "Folgende Spalten wurden angefordert, existieren aber nicht im Header: "
                + ", ".join(missing),
                file=sys.stderr,
            )
            sys.exit(1)

        # Header schreiben (nur ausgewählte Spalten)
        f_out.write(",".join(selected_columns) + "\n")

        for row_idx, row in enumerate(reader):
            # Falls Indizes angegeben wurden, nur diese Zeilen berücksichtigen
            if indices is not None and row_idx not in indices:
                continue

            # Optionaler Spalten-Filter
            if args.filter_column and args.filter_value is not None:
                cell = row.get(args.filter_column, "")
                if cell is None:
                    cell = ""
                else:
                    cell = str(cell)

                # Einfache Teilstring-Suche, z.B. "CWE-362" in "['CWE-362']"
                if args.filter_value not in cell:
                    continue

            values = [row.get(col, "") or "" for col in selected_columns]
            f_out.write(",".join(values) + "\n")

    print(f"Geschriebene Datei: {out_path}")


if __name__ == "__main__":
    main()

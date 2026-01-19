#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
from typing import Dict


def looks_like_cpp(func: str) -> bool:
    """Heuristisch entscheiden, ob eine Funktion eher C++ als C ist.

    Wir filtern alles raus, was sehr typische C++-Konstrukte enthält.
    Die Heuristik ist bewusst konservativ: lieber etwas zu viel verwerfen
    als C++-Code fälschlich als C zu markieren.
    """

    cpp_markers = [
        "::",
        "template<",
        "std::",
        "using namespace",
        "new ",
        "delete ",
        "noexcept",
        "nullptr",
        "friend ",
        "virtual ",
        "public:",
        "private:",
        "protected:",
        "constexpr",
        "decltype",
        "typename",
        "explicit",
        "mutable",
        "static_cast<",
        "dynamic_cast<",
        "reinterpret_cast<",
        "const_cast<",
    ]

    lower = func.lower()
    for marker in cpp_markers:
        if marker in lower:
            return True
    return False


def is_c_function(sample: Dict) -> bool:
    func = sample.get("func", "")
    if not func or not isinstance(func, str):
        return False

    # Wenn es wie C++ aussieht, verwerfen
    if looks_like_cpp(func):
        return False

    # Optional: ganz grobe Plausibilitätsprüfung auf C-Funktion
    # (Rückgabetyp, Name, Parameterliste, Blockklammern)
    if "(" not in func or ")" not in func or "{" not in func or "}" not in func:
        return False

    return True


def extract_c_functions(jsonl_path: str, csv_path: str) -> None:
    total = 0
    kept = 0
    row_index = 0

    with open(jsonl_path, "r", encoding="utf-8") as f_in, \
            open(csv_path, "w", encoding="utf-8", newline="") as f_out:

        writer = csv.writer(f_out)
        # Spalten entsprechend der gewünschten Zielstruktur
        writer.writerow([
            "index",            # laufender Index der Zeile
            "processed_func",   # Funktionscode aus "func"
            "target",           # Label aus "target"
            "vul_func_with_fix",  # hier konstant "-"
            "cve_id",           # aus "cve"
            "cwe_id",           # aus "cwe" (als String repräsentiert)
            "commit_id",        # aus "commit_id"
            "file_path",        # aus "file_name"
            "file_language",    # hier konstant "c"
            "flaw_line_index",  # leere Liste
            "flaw_line",        # leerer String
        ])

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                sample = json.loads(line)
            except json.JSONDecodeError:
                # Zeile überspringen, falls defekt
                continue

            if not is_c_function(sample):
                continue

            processed_func = sample.get("func", "")
            target = sample.get("target")
            vul_func_with_fix = "-"
            cve_id = sample.get("cve", "")

            cwe_value = sample.get("cwe")
            if cwe_value is None:
                cwe_id = ""
            else:
                # Als JSON-String repräsentieren, um Listenstruktur zu erhalten
                cwe_id = json.dumps(cwe_value, ensure_ascii=False)

            commit_id = sample.get("commit_id", "")
            file_path = sample.get("file_name", "")
            file_language = "c"

            # flaw_line_index: hier immer leere Liste
            flaw_line_index = json.dumps([], ensure_ascii=False)
            # flaw_line: hier immer leerer String
            flaw_line = ""

            writer.writerow([
                row_index,
                processed_func,
                target,
                vul_func_with_fix,
                cve_id,
                cwe_id,
                commit_id,
                file_path,
                file_language,
                flaw_line_index,
                flaw_line,
            ])
            row_index += 1
            kept += 1

    print(f"Fertig. Insgesamt Zeilen gelesen: {total}, C-Funktionen geschrieben: {kept}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extrahiere C-Funktionen mit ihren Labels aus primevul JSONL "
            "und speichere sie in einer CSV-Datei."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        default="primevul_valid.jsonl",
        help="Pfad zur Eingabe-JSONL-Datei (Standard: primevul_valid.jsonl)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="val.csv",
        help="Pfad zur Ausgabe-CSV-Datei (Standard: val.csv)",
    )

    args = parser.parse_args()

    jsonl_path = os.path.abspath(args.input)
    csv_path = os.path.abspath(args.output)

    if not os.path.isfile(jsonl_path):
        print(f"Eingabedatei nicht gefunden: {jsonl_path}", file=sys.stderr)
        sys.exit(1)

    extract_c_functions(jsonl_path, csv_path)


if __name__ == "__main__":
    main()

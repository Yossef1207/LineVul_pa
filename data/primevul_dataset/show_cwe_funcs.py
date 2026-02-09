import csv
import sys
from pathlib import Path

# Allow very large code fields
csv.field_size_limit(10**9)


def default_vuln_csv() -> Path:
    """Return default vuln CSV (codellama-34b_vuln.csv) relative to repo root.

    This lets you call the script simply as:
        python show_cwe_funcs.py CWE-787 10
    from any working directory.
    """

    here = Path(__file__).resolve()
    # __file__ is in .../LineVul_pa/data/primevul_dataset/
    linevul_root = here.parents[2]  # .../LineVul_pa
    return linevul_root / "data" / "llm_datasets" / "codellama-34b_vuln.csv"


def show_first_funcs(
    csv_path: str,
    cwe_query: str,
    max_hits: int = 5,
    contains: str | None = None,
) -> None:
    """Print the first `max_hits` processed_func entries matching the given CWE.

    Primär wird in der Spalte `cwe` gesucht (LLM-Datasets).
    Falls diese nicht existiert, wird auf `cwe_id` zurückgefallen.

    Optional kann zusätzlich auf einen Substring in `processed_func` gefiltert
    werden (z.B. "malloc").
    """
    path = Path(csv_path)
    if not path.is_file():
        print(f"CSV file not found: {path}")
        return

    hits = 0

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # Bevorzugt in `cwe` suchen, nur wenn nicht vorhanden auf `cwe_id` fallen
        if "cwe" in fieldnames:
            cwe_col = "cwe"
        elif "cwe_id" in fieldnames:
            cwe_col = "cwe_id"
        else:
            print("No CWE column (cwe / cwe_id) found in CSV header:", fieldnames)
            return

        for row in reader:
            cwe_val = (row.get(cwe_col) or "").strip()
            if not cwe_val:
                continue

            processed = row.get("processed_func") or ""

            # Match if the text contains the CWE identifier (e.g. "CWE-787")
            # und optional einen Substring im Code (z.B. "malloc")
            if cwe_query in cwe_val and (contains is None or contains in processed):
                hits += 1
                print(f"\n=== Treffer {hits} (CWE-Feld: {cwe_val}) ===")
                print(processed)

                if hits >= max_hits:
                    break

    if hits == 0:
        print(f"Keine Einträge mit '{cwe_query}' gefunden in {csv_path}.")


if __name__ == "__main__":
    # Unterstützt zwei Modi:
    # 1) Nur CWE + optional max_hits [+ optional contains] -> default codellama-34b_vuln.csv
    #    python show_cwe_funcs.py CWE-787 10 malloc
    # 2) CSV-Pfad + CWE + optional max_hits [+ optional contains]
    #    python show_cwe_funcs.py path/to/file.csv CWE-787 10 malloc

    if len(sys.argv) < 2:
        print("Benutzung:")
        print("  python show_cwe_funcs.py <CWE-Nummer> [max_hits]")
        print("  python show_cwe_funcs.py <csv_path> <CWE-Nummer> [max_hits]")
        sys.exit(1)

    args = sys.argv[1:]

    contains_substring: str | None = None

    if args[0].lower().endswith(".csv"):
        # Modus 2: expliziter CSV-Pfad
        if len(args) < 2:
            print("Fehlendes CWE-Argument.")
            sys.exit(1)
        csv_path = args[0]
        cwe_query = args[1]
        if len(args) > 2:
            # drittes Argument: max_hits; viertes (falls vorhanden): contains-Filter
            try:
                max_hits = int(args[2])
                if len(args) > 3:
                    contains_substring = args[3]
            except ValueError:
                # wenn keine Zahl, dann drittes Argument direkt als contains-Filter
                max_hits = 5
                contains_substring = args[2]
    else:
        # Modus 1: nur CWE angegeben, nimm Default-LLM-Dataset
        cwe_query = args[0]
        if len(args) > 1:
            # zweites Argument: max_hits oder contains-Filter
            try:
                max_hits = int(args[1])
                if len(args) > 2:
                    contains_substring = args[2]
            except ValueError:
                max_hits = 5
                contains_substring = args[1]
        else:
            max_hits = 5
        csv_path = str(default_vuln_csv())

    show_first_funcs(csv_path, cwe_query, max_hits, contains_substring)

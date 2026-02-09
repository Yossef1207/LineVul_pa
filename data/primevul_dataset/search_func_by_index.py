import json
from pathlib import Path
import sys
import pandas as pd

def search_func_in_jsonl(jsonl_path, function_code):
    """
    Sucht nach einer spezifischen Funktion in der JSONL-Datei
    und gibt alle Einträge aus, die diese Funktion haben.
    
    Args:
        jsonl_path: Pfad zur JSONL-Datei
        function_code: Der Funktionscode zum Suchen
    """
    path = Path(jsonl_path)
    results = []
    
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                print(f"Fehler beim Parsen der Zeile: {e}")
                continue
            
            # Prüfe ob die Funktion in diesem Eintrag vorhanden ist
            if obj.get('func') == function_code:
                results.append(obj)
    
    return results

def get_processed_func_from_csv(csv_path, index):
    """
    Sucht einen Index in der CSV-Datei und gibt die processed_func zurück.
    
    Args:
        csv_path: Pfad zur test.csv
        index: Der Index zum Suchen
    
    Returns:
        Der Wert aus der processed_func Spalte oder None
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Suche nach der Zeile mit dem gegebenen Index
        if 'index' in df.columns:
            row = df[df['index'] == index]
        else:
            # Falls die erste Spalte der Index ist
            row = df.iloc[[index]]
        
        if row.empty:
            return None
        
        # Versuche processed_func zu finden
        if 'processed_func' in row.columns:
            return row['processed_func'].values[0]
        else:
            return None
    except Exception as e:
        print(f"Fehler beim Lesen der CSV: {e}")
        return None

if __name__ == "__main__":
    # Eingabeparameter lesen
    if len(sys.argv) < 2:
        print("Verwendung: python search_func_by_index.py <INDEX>")
        print("Beispiel: python search_func_by_index.py 217")
        sys.exit(1)
    
    try:
        index = int(sys.argv[1])
    except ValueError:
        print(f"Fehler: Index muss eine Zahl sein. Eingabe: {sys.argv[1]}")
        sys.exit(1)
    
    csv_file = "/work/cps/czt0517/LineVul_pa/data/primevul_dataset/test.csv"
    jsonl_file = "/work/cps/czt0517/LineVul_pa/data/primevul_dataset/primevul_test.jsonl"
    
    print(f"Suche nach Index: {index}\n")
    
    # Hole die processed_func aus der CSV
    processed_func = get_processed_func_from_csv(csv_file, index)
    
    if processed_func is None:
        print(f"Index {index} nicht gefunden in {csv_file}")
        sys.exit(1)
    
    print(f"Gefundene Funktion aus CSV:")
    print(f"{processed_func}\n")
    print("=" * 80)
    print(f"Suche nach Funktion in primevul_test.jsonl...\n")
    
    results = search_func_in_jsonl(jsonl_file, processed_func)
    
    if results:
        print(f"Gefunden: {len(results)} Einträge mit dieser Funktion\n")
        for i, entry in enumerate(results, 1):
            print(f"--- Eintrag {i} ---")
            print(json.dumps(entry, ensure_ascii=False, indent=2))
            print()
    else:
        print(f"Keine Einträge mit dieser Funktion gefunden.")

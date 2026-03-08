import csv
import sys
from pathlib import Path

# Feldgrößenlimit anheben für sehr lange processed_func-Einträge
csv.field_size_limit(sys.maxsize)

paths = [
    'primevul_dataset/test.csv',
    'primevul_dataset/train.csv',
    'reposvul_dataset/test.csv',
    'reposvul_dataset/train.csv',
]

for p in paths:
    path = Path(p)
    print(f'--- {path} ---')
    if not path.is_file():
        print('Datei nicht gefunden')
        continue
    total = 0
    over_512 = 0
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'processed_func' not in reader.fieldnames:
            print('Spalte processed_func nicht gefunden; vorhandene Spalten:', reader.fieldnames)
            continue
        for row in reader:
            total += 1
            text = row.get('processed_func') or ''
            length = len(text.split())  # whitespace-getrennte Tokens
            if length > 512:
                over_512 += 1
    if total == 0:
        print('Keine Zeilen gefunden')
    else:
        perc = over_512 / total * 100
        print(f'Funktionen gesamt: {total}')
        print(f'>512 Tokens: {over_512}')
        print(f'Prozentual: {perc:.2f}%')
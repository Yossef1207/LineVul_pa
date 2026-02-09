## zeige mir die strucktur von jsonl
```
cd /fibus/fs2/14/czt0517/Desktop/pa-yossef/LineVul_pa/data/primevul && python - << 'PY'
import json
from pathlib import Path

path = Path('primevul_train.jsonl')
keys = set()

with path.open('r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        keys.update(obj.keys())

print('\n'.join(sorted(keys)))
PY
```


## csv vollständig? 

cd /fibus/fs2/14/czt0517/Desktop/pa-yossef/LineVul_pa/data/primevul && python - << 'PY'
import csv, sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)
path = Path('val.csv')

missing_target = 0
missing_func = 0
bad_rows = 0
rows = 0

with path.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows += 1
        try:
            target = row.get('target')
            func = row.get('processed_func') or row.get('func')
        except Exception:
            bad_rows += 1
            continue

        if target is None or target == '':
            missing_target += 1
        if func is None or func.strip() == '':
            missing_func += 1

print(f'rows={rows}')
print(f'missing_target={missing_target}')
print(f'missing_func={missing_func}')
print(f'bad_rows={bad_rows}')
PY




python 03_augment_with_llm.py --reposvul_train ../primevul/train.csv --csv_vuln codellama-34b_vuln.csv --csv_nonvuln codellama-34b_non-vuln.csv --out_dir ../primevul_plus_codellama





cd /fibus/fs2/14/czt0517/Desktop/pa-yossef/LineVul_pa/data/llm_datasets && curl --header "PRIVATE-TOKEN: $TOKEN" "https://collaborating.tuhh.de/api/v4/projects/e22%2Finstitute-members%2Fcurrent-members%2Fphd%2Ftorge%2Fllm-based-vulnerability-synthesis/repository/files/data%2Fenhanced%2Fcomparison%2Fcodellama-34b%2Fnon-vuln%2Fmerged_results_w_complexity_and_compil.csv/raw?ref=main" -o codellama-34b_non-vuln.csv



python - <<'PY'
import pandas as pd

csv_file = "/work/cps/czt0517/LineVul_pa/data/primevul_dataset/val.csv"

df = pd.read_csv(csv_file)

total = len(df)
target_0 = len(df[df['target'] == 0])
target_1 = len(df[df['target'] == 1])

print(f"Gesamte Einträge in val.csv: {total}")
print(f"Einträge mit target = 0: {target_0}")
print(f"Einträge mit target = 1: {target_1}")
print(f"\nProzentual:")
print(f"target = 0: {target_0/total*100:.1f}%")
print(f"target = 1: {target_1/total*100:.1f}%")
PY
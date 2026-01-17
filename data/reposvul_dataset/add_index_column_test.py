import os
import pandas as pd

# Dieses Skript fügt eine Index-Spalte (0-basiert) als erste Spalte in test.csv ein.
# Es legt vorher ein Backup test_no_index.csv an.

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "test.csv")
backup_path = os.path.join(script_dir, "test_no_index.csv")

print(f"Lese {csv_path} ...")
df = pd.read_csv(csv_path)

# Backup anlegen, falls noch nicht vorhanden
if not os.path.exists(backup_path):
    print(f"Erstelle Backup {backup_path} ...")
    df.to_csv(backup_path, index=False)

# Index-Spalte einfügen (0-basiert)
df.insert(0, "index", range(len(df)))

print(f"Schreibe mit Index-Spalte nach {csv_path} ...")
df.to_csv(csv_path, index=False)
print("Fertig.")

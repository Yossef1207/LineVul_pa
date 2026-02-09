import pandas as pd

path = "../reposvul_dataset/train.csv"
df = pd.read_csv(path, low_memory=False)
print("Anzahl Einträge:", len(df))
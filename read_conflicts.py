import glob, pandas as pd
p = sorted(glob.glob("exports/conflicts_*.xlsx"))[-1]
print("Open:", p)
x = pd.ExcelFile(p)
print("Sheets:", x.sheet_names)
for s in x.sheet_names:
    df = pd.read_excel(p, sheet_name=s)
    print(f"\n=== {s} (rows={len(df)}) ===")
    print(df.head(10).to_string(index=False))

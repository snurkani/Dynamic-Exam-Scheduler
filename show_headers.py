import pandas as pd

for path in ["Ders Listesi.xlsx", "ogrenci_listesi.xlsx"]:
    try:
        df = pd.read_excel(path, nrows=0)  # sadece sütun adlarını al
        print(f"\n== {path} ==")
        for i, c in enumerate(df.columns, 1):
            print(f"{i}. {c}")
    except Exception as e:
        print(f"\n== {path} ==\nHata: {e}")

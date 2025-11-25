import re, pandas as pd
df = pd.read_excel("samples/courses_from_uploaded.xlsx")
def prefix(code:str)->str:
    s = str(code or "").strip().upper()
    m = re.match(r"^[A-ZÇĞİÖŞÜ]+", s)
    return m.group(0) if m else ""
df["__pref"] = df["code"].map(prefix)
print("Önekler ve adetler (en çoktan aza):")
print(df["__pref"].value_counts().head(30).to_string())
print("\nÖrnek kayıtlar (ilk 10):")
print(df[["code","name"]].head(10).to_string(index=False))

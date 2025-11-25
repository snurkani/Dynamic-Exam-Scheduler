import os, pandas as pd

COURSE_ALIASES = {
    "code": {"code","ders_kodu","ders kodu","kod"},
    "name": {"name","ders_adı","ders adi","ders adı","ders"},
    "instructor": {"instructor","öğretim elemanı","ogretim elemani","hoca","öğretim uyesi","öğretim üyesi"},
    "class_year": {"class_year","sınıf","sinif","yıl","yil","class"},
    "course_type": {"course_type","tür","tur","tip","zorunlu/seçmeli"}
}
STU_ALIASES = {
    "number": {"number","ogrenci_no","öğrenci no","öğrenci numarası","ogrenci numarasi","ogr no","öğrenci no."},
    "name": {"name","ad soyad","öğrenci adı","ogrenci adi","isim"}
}

def normalize_columns(df, aliases):
    low = {c:str(c).strip().lower() for c in df.columns}
    rev = {}
    for k, vals in aliases.items():
        for v in vals:
            rev[v] = k
    newcols = []
    for c in df.columns:
        lc = str(c).strip().lower()
        newcols.append(rev.get(lc, lc))
    df = df.copy()
    df.columns = newcols
    return df

def pick_cols(df, need):
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"Eksik kolonlar: {missing}")
    return df[need]

def main():
    os.makedirs("samples", exist_ok=True)

    # Dersler
    cpath = "Ders Listesi.xlsx"
    if os.path.exists(cpath):
        dfc = pd.read_excel(cpath)
        dfc = normalize_columns(dfc, COURSE_ALIASES)
        # class_year sayıya, course_type normalize
        if "class_year" in dfc.columns:
            dfc["class_year"] = pd.to_numeric(dfc["class_year"], errors="coerce").fillna(1).astype(int)
        if "course_type" in dfc.columns:
            dfc["course_type"] = (dfc["course_type"].astype(str).str.strip()
                                  .str.replace("seçmeli","seçmeli", regex=False)
                                  .str.replace("zorunlu","Zorunlu", case=False, regex=False)
                                  .str.replace("seçmeli","Seçmeli", case=False, regex=False))
        dfc = pick_cols(dfc, ["code","name","instructor","class_year","course_type"])
        outc = "samples/courses_from_uploaded.xlsx"
        dfc.to_excel(outc, index=False)
        print("OK ->", outc)
    else:
        print("Bulunamadı:", cpath)

    # Öğrenciler
    spath = "ogrenci_listesi.xlsx"
    if os.path.exists(spath):
        dfs = pd.read_excel(spath)
        dfs = normalize_columns(dfs, STU_ALIASES)
        dfs = pick_cols(dfs, ["number","name"])
        outs = "samples/students_from_uploaded.xlsx"
        dfs.to_excel(outs, index=False)
        print("OK ->", outs)
    else:
        print("Bulunamadı:", spath)

if __name__ == "__main__":
    main()

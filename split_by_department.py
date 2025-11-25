import os, re
import pandas as pd

BASE = "samples"
COURSES = os.path.join(BASE, "courses_from_uploaded.xlsx")
STUDENTS = os.path.join(BASE, "students_from_uploaded.xlsx")
ENRS = os.path.join(BASE, "enrollments_from_uploaded.xlsx")

# Kod prefix → bölüm adı (gerekirse düzenleyin)
MAP = {
    "Bilgisayar Müh.": ["CSE","BLM"],
    "Yazılım Müh.":    ["YAZ","SWE","SE"],
    "Elektrik Müh.":   ["ELK","EEE"],
    "Elektronik Müh.": ["ELN","ECE"],
    "İnşaat Müh.":     ["INS","CE"],
}

def dep_of(code:str)->str|None:
    up = (code or "").upper().strip()
    for dep, prefs in MAP.items():
        if any(up.startswith(p) for p in prefs):
            return dep
    return None

def main():
    dfc = pd.read_excel(COURSES)      # code, name, instructor, class_year, course_type
    dfs = pd.read_excel(STUDENTS)     # number, name
    dfe = pd.read_excel(ENRS)         # student_number, course_code

    # Ders → bölüm sözlüğü (dersten bölümü bulmak için)
    code2dep = {str(r.code).strip().upper(): dep_of(str(r.code)) for _,r in dfc.iterrows()}

    for dep in MAP.keys():
        outdir = os.path.join(BASE, f"dept_{dep.replace(' ','_')}")
        os.makedirs(outdir, exist_ok=True)

        # 1) Bölüm dersleri
        dfc_dep = dfc[[code2dep.get(str(r.code).strip().upper())==dep for _,r in dfc.iterrows()]]
        dfc_dep.to_excel(os.path.join(outdir, "courses.xlsx"), index=False)

        # 2) Bölüm kayıtları (enrollment) → önce bu bölüm derslerine ait olan satırlar
        codes_dep = set(c.strip().upper() for c in dfc_dep["code"])
        dfe_dep = dfe[[str(r.course_code).strip().upper() in codes_dep for _,r in dfe.iterrows()]]

        # 3) Bölüm öğrencileri → bu bölüm kayıtlarında geçen tüm numaralar
        nums = set(str(n).strip() for n in dfe_dep["student_number"])
        dfs_dep = dfs[[str(r.number).strip() in nums for _,r in dfs.iterrows()]]

        # Kaydet
        dfe_dep.to_excel(os.path.join(outdir, "enrollments.xlsx"), index=False)
        dfs_dep.to_excel(os.path.join(outdir, "students.xlsx"), index=False)

        print(dep, "->",
              len(dfc_dep), "ders,", len(dfs_dep), "öğrenci,", len(dfe_dep), "kayıt")

if __name__ == "__main__":
    main()

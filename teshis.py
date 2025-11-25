# --- teshis.py: Öğrenci Arama Teşhis Aracı ---
import sqlite3, os, glob, re, sys

# >>>> BURAYI DÜZENLE (istenirse) <<<<
TEST_NO = "210059017"      # Aramak istediğin öğrenci no
DEP_KEY = "bilgisayar"     # Bölüm adından bir parça (küçük harf)

# DB dosyasını bul
db = 'app.db' if os.path.exists('app.db') else (glob.glob('**/*.db', recursive=True)[0])
con = sqlite3.connect(db); cur = con.cursor()

print("DB_PATH:", os.path.abspath(db))

# Bölümler
deps = cur.execute("SELECT id,name FROM departments ORDER BY id;").fetchall()
print("Departments:", deps)
dep_id = next((i for i,n in deps if DEP_KEY and DEP_KEY.lower() in (n or "").lower()), None)
print("Selected dep_id by name key:", dep_id)

# Sayımlar
n_students      = cur.execute("SELECT COUNT(*) FROM students;").fetchone()[0]
n_students_null = cur.execute("SELECT COUNT(*) FROM students WHERE department_id IS NULL OR department_id='';").fetchone()[0]
n_enroll        = cur.execute("SELECT COUNT(*) FROM enrollments;").fetchone()[0]
print(f"Counts -> students:{n_students}  null_dep:{n_students_null}  enrollments:{n_enroll}")

raw  = TEST_NO.strip()
norm = re.sub(r"\D","", raw).strip()

def one(sql, params): return cur.execute(sql, params).fetchone()

# A) Bölüm zorunlu + TRIM
stu_A = one("""SELECT id,name,department_id FROM students
               WHERE department_id=? AND TRIM(number)=?
               LIMIT 1""", (dep_id, raw)) if dep_id is not None else None

# B) Bölüm zorunlu + normalize karşılaştırma
stu_B = one("""SELECT id,name,department_id FROM students
               WHERE department_id=? AND REPLACE(TRIM(number),' ','')=REPLACE(TRIM(?),' ','')
               LIMIT 1""", (dep_id, norm)) if dep_id is not None else None

# C) Bölüm esnek (NULL/'' de kabul) + normalize karşılaştırma
stu_C = one("""SELECT id,name,department_id FROM students
               WHERE (? IS NULL OR department_id=? OR department_id IS NULL OR department_id='')
                 AND REPLACE(TRIM(number),' ','')=REPLACE(TRIM(?),' ','')
               LIMIT 1""", (dep_id, dep_id, norm))

print("\nProbe results:")
print("A) strict dept + TRIM(number)=raw    ->", stu_A)
print("B) strict dept + normalized compare  ->", stu_B)
print("C) flexible dept + normalized compare->", stu_C)

print("\nDiagnosis & Fix:")
if n_students == 0:
    print("- Students tablosu boş: import/commit yapılmamış.")
    print("  Çözüm: import koduna conn.commit() ekle ve tekrar içe aktar.")
elif stu_C is None:
    print("- Bu numarayla hiç kayıt yok. Excel/DB uyuşmuyor.")
    print("  Çözüm: ogrenciler_clean.xlsx ile yeniden import et.")
else:
    if dep_id is not None and stu_B is None and stu_C is not None:
        print("- Kayıt var ama department_id boş; bölüm filtresine takılıyor.")
        print("  Hızlı: UPDATE students SET department_id = <dep_id> WHERE department_id IS NULL OR department_id='';")
        print("  Kalıcı: import'ta department_id ile INSERT + commit.")
    elif stu_A is None and stu_B is not None:
        print("- Numara format/boşluk sorunu; TRIM yetmiyor.")
        print("  Çözüm: arama SQL'inde REPLACE(TRIM(number),' ','') karşılaştırması kullan.")
    else:
        print("- Bölüm filtresi/normalize birlikte uygulanmalı (yukarıdaki iki öneri).")

con.close()

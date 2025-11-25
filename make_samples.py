import os, pandas as pd
os.makedirs("samples", exist_ok=True)

courses = pd.DataFrame([
    {"code":"CSE101","name":"Programlama I"},
    {"code":"CSE102","name":"Programlama II"},
    {"code":"CSE201","name":"Veri Yapilari"},
])
courses.to_excel("samples/courses.xlsx", index=False)

students = pd.DataFrame([
    {"number":"1001","name":"Ayse Yilmaz"},
    {"number":"1002","name":"Mehmet Demir"},
    {"number":"1003","name":"Zeynep Kaya"},
])
students.to_excel("samples/students.xlsx", index=False)

print("olusturuldu: samples/courses.xlsx, samples/students.xlsx")

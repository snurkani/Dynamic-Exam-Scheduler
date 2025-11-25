import os, pandas as pd
os.makedirs("samples", exist_ok=True)
df = pd.DataFrame([
    {"code":"CSE101","name":"Programlama I","instructor":"Dr. A","class_year":1,"course_type":"Zorunlu"},
    {"code":"CSE201","name":"Veri Yapilari","instructor":"Dr. B","class_year":2,"course_type":"Zorunlu"},
    {"code":"CSE350","name":"Goruntu Isleme","instructor":"Dr. C","class_year":3,"course_type":"Seçmeli"},
])
df.to_excel("samples/courses_v2.xlsx", index=False)
print("samples/courses_v2.xlsx hazir")

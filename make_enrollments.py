import os, pandas as pd
os.makedirs("samples", exist_ok=True)
df = pd.DataFrame([
    {"student_number":"1001", "course_code":"CSE101"},
    {"student_number":"1002", "course_code":"CSE101"},
    {"student_number":"1003", "course_code":"CSE201"},
    {"student_number":"1001", "course_code":"CSE350"},
])
df.to_excel("samples/enrollments.xlsx", index=False)
print("samples/enrollments.xlsx hazir")

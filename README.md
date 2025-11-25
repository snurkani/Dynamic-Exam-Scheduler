# Dynamic Exam Scheduler Automation System

## 🚀 Project Overview
This project is a desktop application developed to solve the complex scheduling problems in universities. It automatically generates optimized exam timetables by considering constraints such as classroom capacities, student overlaps, and professor availability.

The system parses student and course data from Excel files (`.xlsx`) and processes them to create conflict-free schedules.

## 🛠️ Technologies Used
* **Language:** Python
* **Data Handling:** Pandas, Excel Parsing
* **Database:** SQLite / SQL
* **Algorithm:** Custom conflict detection & capacity optimization logic

## ✨ Key Features
* **Conflict Prevention:** Ensures no student has conflicting exams.
* **Capacity Management:** Assigns classrooms based on student counts.
* **Automated Parsing:** Reads `Ders Listesi.xlsx` and `ogrenci_listesi.xlsx` automatically.
* **Reporting:** Exports final schedules to Excel/PDF.

## 📂 How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt

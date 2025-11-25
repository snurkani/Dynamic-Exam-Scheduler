PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  department_id INTEGER,
  FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS classrooms (
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  capacity INTEGER NOT NULL,
  rows INTEGER NOT NULL,
  cols INTEGER NOT NULL,
  seat_group_size INTEGER NOT NULL,
  UNIQUE(department_id, code),
  FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  instructor TEXT,
  class_year INTEGER,
  course_type TEXT,
  UNIQUE(department_id, code),
  FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS students (
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  number TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE(department_id, number),
  FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exam_slots (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  starts_at TEXT NOT NULL,
  ends_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exam_assignments (
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  classroom_id INTEGER NOT NULL,
  slot_id INTEGER NOT NULL,
  FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE,
  FOREIGN KEY(course_id)     REFERENCES courses(id) ON DELETE CASCADE,
  FOREIGN KEY(classroom_id)  REFERENCES classrooms(id) ON DELETE CASCADE,
  FOREIGN KEY(slot_id)       REFERENCES exam_slots(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS enrollments (
  id INTEGER PRIMARY KEY,
  department_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  UNIQUE(student_id, course_id),
  FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE,
  FOREIGN KEY(student_id)    REFERENCES students(id)    ON DELETE CASCADE,
  FOREIGN KEY(course_id)     REFERENCES courses(id)     ON DELETE CASCADE
);

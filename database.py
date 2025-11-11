import sqlite3
import os

class AttendanceDatabase:
    def __init__(self, db_name='attendance.db'):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create students table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_number TEXT UNIQUE NOT NULL,
                face_encoding BLOB
            )
        ''')

        # Create attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT,
                time TEXT,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_student(self, name, roll_number, face_encoding=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO students (name, roll_number, face_encoding)
                VALUES (?, ?, ?)
            ''', (name, roll_number, face_encoding))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Roll number already exists
        finally:
            conn.close()

    def get_all_students(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, roll_number FROM students')
        students = cursor.fetchall()

        conn.close()
        return students

    def get_student_by_roll(self, roll_number):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, roll_number, face_encoding FROM students WHERE roll_number = ?', (roll_number,))
        student = cursor.fetchone()

        conn.close()
        return student

    def update_face_encoding(self, roll_number, face_encoding):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE students
            SET face_encoding = ?
            WHERE roll_number = ?
        ''', (face_encoding, roll_number))

        conn.commit()
        conn.close()

    def mark_attendance(self, student_id, date, time):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Check if attendance already marked for today
        cursor.execute('''
            SELECT id FROM attendance
            WHERE student_id = ? AND date = ?
        ''', (student_id, date))

        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO attendance (student_id, date, time)
                VALUES (?, ?, ?)
            ''', (student_id, date, time))
            conn.commit()
            marked = True
        else:
            marked = False

        conn.close()
        return marked

    def get_attendance_report(self, date=None):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if date:
            cursor.execute('''
                SELECT s.name, s.roll_number, a.date, a.time
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
                ORDER BY s.name
            ''', (date,))
        else:
            cursor.execute('''
                SELECT s.name, s.roll_number, COUNT(a.id) as total_days
                FROM students s
                LEFT JOIN attendance a ON s.id = a.student_id
                GROUP BY s.id
                ORDER BY s.name
            ''')

        report = cursor.fetchall()
        conn.close()
        return report

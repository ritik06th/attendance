import cv2
import numpy as np
import sqlite3
import pickle
from datetime import datetime
import os

class SimpleFaceRecognition:
    def __init__(self, db_name='attendance.db'):
        self.db_name = db_name
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_number TEXT UNIQUE NOT NULL
            )
        ''')

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

    def capture_face(self, name, roll_number):
        """Capture face images for training"""
        cap = cv2.VideoCapture(0)
        faces = []
        labels = []
        count = 0

        print(f"Capturing faces for {name} ({roll_number}). Press 'c' to capture, 'q' to quit.")

        while count < 20:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            detected_faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in detected_faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))

                if count < 20:
                    faces.append(face_roi)
                    labels.append(count)
                    count += 1
                    print(f"Captured {count}/20 faces")

                if count >= 20:
                    break

            cv2.imshow('Capture Face', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if len(faces) >= 10:
            # Add student to database
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            try:
                cursor.execute('INSERT INTO students (name, roll_number) VALUES (?, ?)', (name, roll_number))
                student_id = cursor.lastrowid
                conn.commit()

                # Train recognizer with this student's faces
                self.recognizer.train(faces, np.array(labels))

                # Save the trained model
                model_file = f'model_{student_id}.yml'
                self.recognizer.save(model_file)

                print(f"Successfully added {name} ({roll_number}) to the database.")
                return True
            except sqlite3.IntegrityError:
                print("Roll number already exists!")
                return False
            finally:
                conn.close()
        else:
            print("Not enough face images captured. Please try again.")
            return False

    def load_all_models(self):
        """Load all trained models"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, roll_number FROM students')
        students = cursor.fetchall()
        conn.close()

        self.student_models = {}
        for student_id, name, roll in students:
            model_file = f'model_{student_id}.yml'
            if os.path.exists(model_file):
                recognizer = cv2.face.LBPHFaceRecognizer_create()
                recognizer.read(model_file)
                self.student_models[student_id] = {
                    'recognizer': recognizer,
                    'name': name,
                    'roll': roll
                }

        return len(self.student_models)

    def recognize_and_mark_attendance(self):
        """Real-time face recognition and attendance marking"""
        if not hasattr(self, 'student_models') or not self.student_models:
            print("No trained models found. Please train some faces first.")
            return

        cap = cv2.VideoCapture(0)
        recognized_today = set()

        print("Starting attendance recognition. Press 'q' to quit.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))

                # Try to recognize with each model
                best_match = None
                best_confidence = 100

                for student_id, model_data in self.student_models.items():
                    recognizer = model_data['recognizer']
                    label, confidence = recognizer.predict(face_roi)

                    if confidence < best_confidence and confidence < 80:  # Confidence threshold
                        best_confidence = confidence
                        best_match = model_data

                if best_match:
                    name = best_match['name']
                    roll = best_match['roll']
                    student_id = list(self.student_models.keys())[list(self.student_models.values()).index(best_match)]

                    # Mark attendance if not already marked today
                    if roll not in recognized_today:
                        now = datetime.now()
                        date = now.strftime("%Y-%m-%d")
                        time = now.strftime("%H:%M:%S")

                        conn = sqlite3.connect(self.db_name)
                        cursor = conn.cursor()

                        # Check if attendance already marked
                        cursor.execute('SELECT id FROM attendance WHERE student_id = ? AND date = ?', (student_id, date))
                        if not cursor.fetchone():
                            cursor.execute('INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)', (student_id, date, time))
                            conn.commit()
                            recognized_today.add(roll)
                            print(f"Attendance marked for {name} ({roll}) at {time}")

                        conn.close()

                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{name} ({roll})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            cv2.imshow('Attendance System', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Attendance recognition stopped.")

    def get_attendance_report(self, date=None):
        """Get attendance report"""
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

# Example usage
if __name__ == "__main__":
    fr = SimpleFaceRecognition()

    # To add a student
    # fr.capture_face("John Doe", "001")

    # To start recognition
    # fr.load_all_models()
    # fr.recognize_and_mark_attendance()

    # To get report
    # report = fr.get_attendance_report()
    # for name, roll, days in report:
    #     print(f"{name} ({roll}): {days} days")

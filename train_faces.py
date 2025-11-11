import cv2
import face_recognition
import pickle
import os
from database import AttendanceDatabase

def capture_face(name, roll_number):
    """
    Capture face images for a student and save encodings
    """
    db = AttendanceDatabase()

    # Check if student already exists
    if db.get_student_by_roll(roll_number):
        print(f"Student with roll number {roll_number} already exists!")
        return False

    cap = cv2.VideoCapture(0)
    face_encodings = []
    count = 0

    print(f"Capturing faces for {name} ({roll_number}). Press 'c' to capture, 'q' to quit.")

    while count < 10:  # Capture 10 face images
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings_frame = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings_frame):
            # Draw rectangle around face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Store encoding
            face_encodings.append(face_encoding)
            count += 1
            print(f"Captured {count}/10 faces")

            if count >= 10:
                break

        cv2.imshow('Capture Face', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(face_encodings) >= 5:  # Require at least 5 faces
        # Average the encodings
        avg_encoding = sum(face_encodings) / len(face_encodings)

        # Convert to bytes for storage
        encoding_bytes = pickle.dumps(avg_encoding)

        # Add student to database
        student_id = db.add_student(name, roll_number, encoding_bytes)

        if student_id:
            print(f"Successfully added {name} ({roll_number}) to the database.")
            return True
        else:
            print("Failed to add student to database.")
            return False
    else:
        print("Not enough face images captured. Please try again.")
        return False

def load_known_faces():
    """
    Load all known face encodings from database
    """
    db = AttendanceDatabase()
    students = db.get_all_students()

    known_encodings = []
    known_names = []
    known_rolls = []

    for student in students:
        student_id, name, roll_number = student
        student_data = db.get_student_by_roll(roll_number)

        if student_data and student_data[3]:  # face_encoding exists
            encoding = pickle.loads(student_data[3])
            known_encodings.append(encoding)
            known_names.append(name)
            known_rolls.append(roll_number)

    return known_encodings, known_names, known_rolls

if __name__ == "__main__":
    # Example usage
    name = input("Enter student name: ")
    roll = input("Enter roll number: ")
    capture_face(name, roll)

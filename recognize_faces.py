import cv2
import face_recognition
import pickle
from datetime import datetime
from train_faces import load_known_faces
from database import AttendanceDatabase

def recognize_and_mark_attendance():
    """
    Real-time face recognition and attendance marking
    """
    # Load known faces
    known_encodings, known_names, known_rolls = load_known_faces()

    if not known_encodings:
        print("No trained faces found. Please train some faces first.")
        return

    db = AttendanceDatabase()
    cap = cv2.VideoCapture(0)

    # Set video resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    recognized_today = set()  # Track who has been recognized today

    print("Starting attendance recognition. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Compare with known faces
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"
            roll = ""

            # Find the best match
            if True in matches:
                best_match_index = matches.index(True)
                name = known_names[best_match_index]
                roll = known_rolls[best_match_index]

                # Mark attendance if not already marked today
                if roll not in recognized_today:
                    now = datetime.now()
                    date = now.strftime("%Y-%m-%d")
                    time = now.strftime("%H:%M:%S")

                    student_data = db.get_student_by_roll(roll)
                    if student_data:
                        student_id = student_data[0]
                        if db.mark_attendance(student_id, date, time):
                            recognized_today.add(roll)
                            print(f"Attendance marked for {name} ({roll}) at {time}")
                        else:
                            print(f"Attendance already marked for {name} ({roll}) today")

            # Draw rectangle and name
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, f"{name} ({roll})", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imshow('Attendance System', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Attendance recognition stopped.")

def get_attendance_report(date=None):
    """
    Get attendance report for a specific date or overall
    """
    db = AttendanceDatabase()
    report = db.get_attendance_report(date)

    if date:
        print(f"Attendance Report for {date}:")
        print("Name\t\tRoll Number\tTime")
        print("-" * 40)
        for name, roll, date_att, time in report:
            status = time if time else "Absent"
            print(f"{name}\t\t{roll}\t\t{status}")
    else:
        print("Overall Attendance Report:")
        print("Name\t\tRoll Number\tTotal Days Present")
        print("-" * 50)
        for name, roll, total_days in report:
            print(f"{name}\t\t{roll}\t\t{total_days}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "report":
        date = sys.argv[2] if len(sys.argv) > 2 else None
        get_attendance_report(date)
    else:
        recognize_and_mark_attendance()

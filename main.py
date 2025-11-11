import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from database import AttendanceDatabase
from train_faces import capture_face
from recognize_faces import recognize_and_mark_attendance, get_attendance_report
import threading

class AttendanceSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Attendance System")
        self.root.geometry("600x400")

        self.db = AttendanceDatabase()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Students tab
        self.students_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.students_frame, text="Students")

        # Attendance tab
        self.attendance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.attendance_frame, text="Attendance")

        # Reports tab
        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports")

        self.setup_students_tab()
        self.setup_attendance_tab()
        self.setup_reports_tab()

    def setup_students_tab(self):
        # Add student section
        add_frame = ttk.LabelFrame(self.students_frame, text="Add New Student", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(add_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_entry = ttk.Entry(add_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=(10,0), pady=2)

        ttk.Label(add_frame, text="Roll Number:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.roll_entry = ttk.Entry(add_frame, width=30)
        self.roll_entry.grid(row=1, column=1, padx=(10,0), pady=2)

        ttk.Button(add_frame, text="Add Student", command=self.add_student).grid(row=2, column=0, columnspan=2, pady=10)

        # Students list section
        list_frame = ttk.LabelFrame(self.students_frame, text="Registered Students", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview for students
        columns = ("ID", "Name", "Roll Number")
        self.students_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.students_tree.heading("ID", text="ID")
        self.students_tree.heading("Name", text="Name")
        self.students_tree.heading("Roll Number", text="Roll Number")
        self.students_tree.column("ID", width=50)
        self.students_tree.column("Name", width=150)
        self.students_tree.column("Roll Number", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scrollbar.set)

        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(list_frame, text="Refresh", command=self.load_students).pack(pady=5)

        self.load_students()

    def setup_attendance_tab(self):
        ttk.Label(self.attendance_frame, text="Real-time Face Recognition Attendance", font=("Arial", 14)).pack(pady=20)

        ttk.Button(self.attendance_frame, text="Start Attendance Recognition",
                  command=self.start_recognition, style="Accent.TButton").pack(pady=10)

        self.status_label = ttk.Label(self.attendance_frame, text="Status: Ready", foreground="blue")
        self.status_label.pack(pady=10)

    def setup_reports_tab(self):
        # Date selection
        date_frame = ttk.Frame(self.reports_frame)
        date_frame.pack(pady=10)

        ttk.Label(date_frame, text="Date (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.date_entry = ttk.Entry(date_frame, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=(10,0))

        ttk.Button(date_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=(10,0))

        # Report display
        report_frame = ttk.LabelFrame(self.reports_frame, text="Attendance Report", padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.report_text = tk.Text(report_frame, height=15, width=60)
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scrollbar.set)

        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def add_student(self):
        name = self.name_entry.get().strip()
        roll = self.roll_entry.get().strip()

        if not name or not roll:
            messagebox.showerror("Error", "Please enter both name and roll number.")
            return

        # Capture face
        if capture_face(name, roll):
            messagebox.showinfo("Success", f"Student {name} ({roll}) added successfully!")
            self.name_entry.delete(0, tk.END)
            self.roll_entry.delete(0, tk.END)
            self.load_students()
        else:
            messagebox.showerror("Error", "Failed to add student. Please try again.")

    def load_students(self):
        # Clear existing items
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)

        # Load students from database
        students = self.db.get_all_students()
        for student in students:
            self.students_tree.insert("", tk.END, values=student)

    def start_recognition(self):
        self.status_label.config(text="Status: Running recognition...", foreground="green")
        # Run recognition in a separate thread to avoid freezing GUI
        recognition_thread = threading.Thread(target=self.run_recognition)
        recognition_thread.daemon = True
        recognition_thread.start()

    def run_recognition(self):
        try:
            recognize_and_mark_attendance()
        finally:
            self.status_label.config(text="Status: Recognition stopped", foreground="blue")

    def generate_report(self):
        date = self.date_entry.get().strip()
        if not date:
            # Generate overall report
            report = self.db.get_attendance_report()
            self.display_report(report, overall=True)
        else:
            # Generate daily report
            report = self.db.get_attendance_report(date)
            self.display_report(report, date=date)

    def display_report(self, report, date=None, overall=False):
        self.report_text.delete(1.0, tk.END)

        if overall:
            self.report_text.insert(tk.END, "Overall Attendance Report\n")
            self.report_text.insert(tk.END, "=" * 50 + "\n")
            self.report_text.insert(tk.END, f"{'Name':<20} {'Roll Number':<15} {'Total Days':<10}\n")
            self.report_text.insert(tk.END, "-" * 50 + "\n")

            for name, roll, total_days in report:
                self.report_text.insert(tk.END, f"{name:<20} {roll:<15} {total_days:<10}\n")
        else:
            self.report_text.insert(tk.END, f"Attendance Report for {date}\n")
            self.report_text.insert(tk.END, "=" * 50 + "\n")
            self.report_text.insert(tk.END, f"{'Name':<20} {'Roll Number':<15} {'Status':<10}\n")
            self.report_text.insert(tk.END, "-" * 50 + "\n")

            for name, roll, date_att, time in report:
                status = time if time else "Absent"
                self.report_text.insert(tk.END, f"{name:<20} {roll:<15} {status:<10}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceSystemGUI(root)
    root.mainloop()

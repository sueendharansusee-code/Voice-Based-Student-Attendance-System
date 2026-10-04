"""
Seed Data Script for Voice-Based Student Attendance System
Populates SQLite database with sample students and attendance records.
"""

from database import init_db, register_student, mark_attendance, get_students
from datetime import datetime, timedelta

def seed_database(db_path=None):
    print("Initializing database...")
    init_db(db_path=db_path)

    sample_students = [
        {"student_id": "STU101", "name": "Alice Smith", "department": "Computer Science"},
        {"student_id": "STU102", "name": "Bob Johnson", "department": "Computer Science"},
        {"student_id": "STU103", "name": "Charlie Brown", "department": "Electrical Engineering"},
        {"student_id": "STU104", "name": "Diana Prince", "department": "Mechanical Engineering"},
        {"student_id": "STU105", "name": "Evan Wright", "department": "Civil Engineering"},
        {"student_id": "STU106", "name": "Fiona Gallagher", "department": "Biotechnology"},
        {"student_id": "STU107", "name": "George Clark", "department": "Computer Science"},
        {"student_id": "STU108", "name": "Hannah Abbott", "department": "Electrical Engineering"},
        {"student_id": "STU109", "name": "Ian Malcolm", "department": "Mechanical Engineering"},
        {"student_id": "STU110", "name": "Julia Roberts", "department": "Biotechnology"},
    ]

    print("Seeding student records...")
    for student in sample_students:
        res = register_student(
            student_id=student["student_id"],
            name=student["name"],
            department=student["department"],
            db_path=db_path
        )
        if res["success"]:
            print(f" Registered: {student['name']} ({student['student_id']})")
        else:
            print(f" Skipped: {res['message']}")

    # Seed historical attendance records for today and past 2 days
    today = datetime.now()
    dates_to_seed = [
        (today - timedelta(days=2)).strftime('%Y-%m-%d'),
        (today - timedelta(days=1)).strftime('%Y-%m-%d'),
        today.strftime('%Y-%m-%d'),
    ]

    print("Seeding attendance logs...")
    # Mark subset of students Present for each day
    students = get_students(db_path=db_path)
    for date_str in dates_to_seed:
        for idx, student in enumerate(students):
            # Alternate present/absent for testing stats
            if (idx + int(date_str[-1])) % 3 != 0 or date_str == today.strftime('%Y-%m-%d') and idx < 7:
                method = "Voice" if idx % 2 == 0 else "Manual"
                time_str = f"09:{10 + idx:02d}:00"
                res = mark_attendance(
                    student_id=student['student_id'],
                    status='Present',
                    method=method,
                    custom_date=date_str,
                    custom_time=time_str,
                    db_path=db_path
                )
                if res.get("success"):
                    print(f" Marked Present [{date_str}]: {student['name']} via {method}")

    print("\nDatabase seeding completed successfully!")

if __name__ == "__main__":
    seed_database()

"""
Automated Test Suite for Voice-Based Student Attendance System
Run with: pytest test_app.py OR python -m unittest test_app.py
"""

import os
import unittest
import tempfile
import json
from app import app
from database import (
    init_db,
    register_student,
    get_students,
    find_student_by_speech,
    mark_attendance,
    update_manual_attendance,
    get_dashboard_stats,
    generate_attendance_csv
)

class TestVoiceAttendanceSystem(unittest.TestCase):

    def setUp(self):
        # Create a temporary SQLite database file for isolated testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        init_db(db_path=self.db_path)
        
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_student_registration(self):
        res = register_student("STU999", "Test Student", "Computer Science", db_path=self.db_path)
        self.assertTrue(res['success'])
        self.assertIn("registered successfully", res['message'])

        # Duplicate ID test
        dup_res = register_student("STU999", "Another Name", "EEE", db_path=self.db_path)
        self.assertFalse(dup_res['success'])
        self.assertIn("already exists", dup_res['message'])

    def test_speech_matching_algorithm(self):
        register_student("STU101", "Alice Smith", "Computer Science", db_path=self.db_path)
        register_student("STU102", "Bob Marley", "Electrical", db_path=self.db_path)

        # 1. Exact name match
        matched = find_student_by_speech("Alice Smith", db_path=self.db_path)
        self.assertIsNotNone(matched)
        self.assertEqual(matched['student_id'], "STU101")

        # 2. Conversational spoken phrase match
        matched_conv = find_student_by_speech("my name is Alice Smith present", db_path=self.db_path)
        self.assertIsNotNone(matched_conv)
        self.assertEqual(matched_conv['student_id'], "STU101")

        # 3. Student ID match
        matched_id = find_student_by_speech("STU102", db_path=self.db_path)
        self.assertIsNotNone(matched_id)
        self.assertEqual(matched_id['name'], "Bob Marley")

        # 4. Spoken digits match
        matched_digits = find_student_by_speech("student 102", db_path=self.db_path)
        self.assertIsNotNone(matched_digits)
        self.assertEqual(matched_digits['student_id'], "STU102")

        # 5. Non-existent student
        unmatched = find_student_by_speech("Unknown User", db_path=self.db_path)
        self.assertIsNone(unmatched)

    def test_duplicate_attendance_prevention(self):
        register_student("STU101", "Alice Smith", "Computer Science", db_path=self.db_path)

        # First mark: Should succeed
        res1 = mark_attendance("STU101", status="Present", method="Voice", db_path=self.db_path)
        self.assertTrue(res1['success'])
        self.assertFalse(res1['already_marked'])

        # Second mark on same day: Should trigger duplicate prevention rule
        res2 = mark_attendance("STU101", status="Present", method="Voice", db_path=self.db_path)
        self.assertFalse(res2['success'])
        self.assertTrue(res2['already_marked'])
        self.assertIn("already marked", res2['message'])

    def test_manual_attendance_toggle(self):
        register_student("STU101", "Alice Smith", "Computer Science", db_path=self.db_path)

        # Mark present manually
        res1 = update_manual_attendance("STU101", status="Present", db_path=self.db_path)
        self.assertTrue(res1['success'])
        self.assertEqual(res1['status'], "Present")

        # Toggle to absent
        res2 = update_manual_attendance("STU101", status="Absent", db_path=self.db_path)
        self.assertTrue(res2['success'])
        self.assertEqual(res2['status'], "Absent")

    def test_dashboard_stats(self):
        register_student("STU101", "Alice Smith", "Computer Science", db_path=self.db_path)
        register_student("STU102", "Bob Johnson", "Computer Science", db_path=self.db_path)

        mark_attendance("STU101", status="Present", method="Voice", db_path=self.db_path)

        stats = get_dashboard_stats(db_path=self.db_path)
        self.assertEqual(stats['total_students'], 2)
        self.assertEqual(stats['present_today'], 1)
        self.assertEqual(stats['absent_today'], 1)
        self.assertEqual(stats['attendance_rate'], 50.0)

    def test_csv_export(self):
        register_student("STU101", "Alice Smith", "Computer Science", db_path=self.db_path)
        mark_attendance("STU101", status="Present", method="Voice", db_path=self.db_path)

        csv_content = generate_attendance_csv(db_path=self.db_path)
        self.assertIn("ID,Student ID,Student Name,Department,Date,Time,Status,Method", csv_content)
        self.assertIn("Alice Smith", csv_content)
        self.assertIn("STU101", csv_content)


if __name__ == '__main__':
    unittest.main()

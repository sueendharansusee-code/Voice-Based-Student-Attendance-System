# Voice-Based Student Attendance System 🎙️📊

A full-stack, speech-recognition-powered web application for recording student attendance in educational institutions. Students state their registered **Name** or **Student ID** verbally into a microphone, and the system matches the speech input against database records to automatically log attendance with real-time duplicate prevention.

> **Note**: This system uses voice command speech-to-text recognition (matching spoken names/IDs against database records), NOT biometric voiceprint identification.

---

## ✨ Key Features

1. **Student Registration**:
   - Register students with Student ID, Full Name, and Department.
2. **Voice Attendance Terminal**:
   - Interactive hands-free speech recognition terminal using browser Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`).
   - Visual audio wave animation and mic pulse indicators.
3. **Smart Speech-to-Text Matching Engine**:
   - Flexible matching algorithm supporting exact name, student ID, digits extraction, and conversational phrases (e.g. *"My name is Alice Smith present"* or *"Student 101"*).
4. **Duplicate Attendance Prevention**:
   - Built-in SQLite uniqueness rules prevent duplicate attendance for the same student on the same calendar day.
5. **Real-time College Dashboard**:
   - Live metrics: Total Students, Present Today, Absent Today, Attendance Percentage.
   - Department breakdown progress bars.
   - Live stream of today's attendance entries.
6. **Search & Filter Directory**:
   - Search student records by Name, ID, or Department.
7. **Attendance History & Logs**:
   - Filter history logs by date range, department, and search keywords.
8. **CSV Export**:
   - One-click export of attendance logs to downloadable CSV format.
9. **Manual Backup Mode**:
   - Interactive toggle checklist to mark Present/Absent manually if microphone is unavailable.
10. **Browser Permission & Error Handling**:
    - Friendly UI notifications for microphone access, unrecognized speech, and browser compatibility.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Modern Glassmorphism & Dashboard Layout), JavaScript (ES6+).
- **Backend**: Python 3.9+ with Flask Web Server.
- **Speech Engine**: Web Speech API (`SpeechRecognition`).
- **Database**: SQLite3 (`attendance.db`).
- **Testing**: Pytest / Unittest.

---

## 📁 Directory Structure

```text
voice_student_attendance/
├── app.py                  # Main Flask application server & REST API endpoints
├── database.py             # SQLite helper & intelligent speech matching engine
├── seed_data.py            # Sample data seeder script
├── test_app.py             # Pytest automated test suite
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation & instructions
├── database/
│   ├── schema.sql          # SQLite relational schema definition
│   └── attendance.db       # Generated SQLite database file
├── static/
│   ├── css/
│   │   └── style.css       # College dashboard CSS styling & voice visualizer
│   └── js/
│       ├── voice.js        # Web Speech API controller & audio animations
│       └── app.js          # Dashboard UI logic, AJAX calls, search & filters
└── templates/
    ├── base.html           # Common layout template with sidebar navigation
    ├── dashboard.html      # Main dashboard with stat cards & quick voice widget
    ├── voice_attendance.html # Fullscreen kiosk terminal for voice attendance
    ├── students.html       # Student registration & directory table
    ├── history.html        # Attendance history logs & CSV export
    └── manual_attendance.html # Backup manual attendance toggle page
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.8 or higher installed on your system.
- Modern Web Browser (Google Chrome, Microsoft Edge, or Apple Safari recommended for Web Speech API support).

### 2. Install Dependencies
Open a terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### 3. Seed Sample Data
Initialize the database with sample student records and attendance logs:
```bash
python seed_data.py
```

### 4. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the included test suite to verify backend endpoints, speech matching, and duplicate prevention rules:

```bash
python test_app.py
```
*or using pytest:*
```bash
pytest test_app.py
```

---

## 🎙️ Speech Recognition Workflow

1. Navigate to **Voice Attendance Kiosk** (`/voice-attendance`).
2. Click the **Microphone** button and grant microphone access when prompted by your browser.
3. Speak your registered name (e.g. *"Alice Smith"*) or Student ID (e.g. *"STU101"* or *"101"*).
4. The system:
   - Converts voice input into text.
   - Cleans conversational filler words (*"my name is"*, *"present"*).
   - Matches transcript against SQLite student records.
   - Records attendance with current date and timestamp.
   - Displays a success card or a duplicate warning if already marked today.

---

## 📊 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/stats` | `GET` | Returns aggregated dashboard statistics |
| `GET /api/students` | `GET` | Search students (`?query=...&department=...`) |
| `POST /api/students/register` | `POST` | Register a new student profile |
| `POST /api/attendance/voice-mark` | `POST` | Mark attendance via speech transcript |
| `GET /api/attendance/today` | `GET` | Fetch today's attendance logs |
| `POST /api/attendance/manual-mark` | `POST` | Manually mark Present/Absent for a student |
| `GET /api/attendance/history` | `GET` | Filter attendance logs |
| `GET /api/attendance/export-csv` | `GET` | Export attendance records as CSV |

---

## 📄 License
MIT License. Free for educational and commercial project use.

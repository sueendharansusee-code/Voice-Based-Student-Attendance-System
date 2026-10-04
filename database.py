import os
import sqlite3
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'attendance.db')

def get_db_connection(db_path=None):
    """Establishes and returns a SQLite database connection."""
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    """Initializes the database using database/schema.sql."""
    target_path = db_path or DB_PATH
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    
    conn = get_db_connection(target_path)
    cursor = conn.cursor()
    
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
    else:
        # Fallback inline schema creation
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
            method TEXT NOT NULL CHECK(method IN ('Voice', 'Manual')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            UNIQUE(student_id, date)
        );
        """)
    conn.commit()
    conn.close()

def register_student(student_id, name, department, db_path=None):
    """Registers a new student in the database."""
    student_id = student_id.strip()
    name = name.strip()
    department = department.strip()

    if not student_id or not name or not department:
        return {"success": False, "message": "All fields (Student ID, Name, Department) are required."}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (student_id, name, department) VALUES (?, ?, ?)",
            (student_id, name, department)
        )
        conn.commit()
        student_row_id = cursor.lastrowid
        conn.close()
        return {
            "success": True,
            "message": f"Student '{name}' ({student_id}) registered successfully.",
            "student": {"id": student_row_id, "student_id": student_id, "name": name, "department": department}
        }
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": f"Student ID '{student_id}' already exists."}
    except Exception as e:
        conn.close()
        return {"success": False, "message": str(e)}

def get_students(query=None, department=None, db_path=None):
    """Retrieves students with optional search query and department filter."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    sql = "SELECT id, student_id, name, department, created_at FROM students WHERE 1=1"
    params = []

    if department and department.strip() and department != "All":
        sql += " AND department = ?"
        params.append(department.strip())

    if query and query.strip():
        q = f"%{query.strip()}%"
        sql += " AND (student_id LIKE ? OR name LIKE ? OR department LIKE ?)"
        params.extend([q, q, q])

    sql += " ORDER BY name ASC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def normalize_text(text):
    """Cleans text for matching: lowercase, strip punctuation, strip filler words."""
    if not text:
        return ""
    text = text.lower()
    # Remove common conversational voice phrases
    fillers = [
        "my name is", "i am", "this is", "present", "here",
        "student id", "student number", "roll number", "id is", "mark me",
        "attendance", "please"
    ]
    for filler in fillers:
        text = text.replace(filler, " ")
    
    # Clean punctuation except alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def find_student_by_speech(transcript, db_path=None):
    """
    Intelligent speech-to-student matching algorithm.
    Matches recognized speech against student_id and name.
    """
    if not transcript or not transcript.strip():
        return None

    cleaned_speech = normalize_text(transcript)
    if not cleaned_speech:
        return None

    students = get_students(db_path=db_path)
    if not students:
        return None

    # Priority 1: Exact match on student_id (ignoring spaces/hyphens)
    speech_compact = re.sub(r'[^a-z0-9]', '', cleaned_speech)
    for s in students:
        sid_compact = re.sub(r'[^a-z0-9]', '', s['student_id'].lower())
        if speech_compact == sid_compact:
            return s

    # Priority 2: Exact match on full name
    for s in students:
        sname_clean = normalize_text(s['name'])
        if cleaned_speech == sname_clean:
            return s

    # Priority 3: Substring / Token match (e.g. spoken name contains student full name or vice versa)
    for s in students:
        sname_clean = normalize_text(s['name'])
        if len(sname_clean) > 2 and (sname_clean in cleaned_speech or cleaned_speech in sname_clean):
            return s

    # Priority 4: All tokens in student's name present in spoken phrase
    for s in students:
        name_tokens = set(normalize_text(s['name']).split())
        speech_tokens = set(cleaned_speech.split())
        if name_tokens and name_tokens.issubset(speech_tokens):
            return s

    # Priority 5: Number extraction match (e.g. spoken "101" matches student_id "STU101" or "101")
    digits_in_speech = re.findall(r'\d+', cleaned_speech)
    if digits_in_speech:
        speech_num = "".join(digits_in_speech)
        for s in students:
            sid_digits = "".join(re.findall(r'\d+', s['student_id']))
            if sid_digits and sid_digits == speech_num:
                return s

    return None

def mark_attendance(student_id, status='Present', method='Voice', custom_date=None, custom_time=None, db_path=None):
    """
    Marks attendance for a student.
    Prevents duplicate attendance for the same student on the same date.
    """
    today_date = custom_date or datetime.now().strftime('%Y-%m-%d')
    current_time = custom_time or datetime.now().strftime('%H:%M:%S')

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Verify student exists
    cursor.execute("SELECT student_id, name, department FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return {"success": False, "message": f"Student with ID '{student_id}' does not exist."}

    student_dict = dict(student)

    # Check for existing attendance on today_date
    cursor.execute(
        "SELECT id, time, status, method FROM attendance WHERE student_id = ? AND date = ?",
        (student_id, today_date)
    )
    existing = cursor.fetchone()

    if existing:
        existing_dict = dict(existing)
        conn.close()
        formatted_time = existing_dict['time']
        return {
            "success": False,
            "already_marked": True,
            "student": student_dict,
            "attendance": existing_dict,
            "message": f"Attendance already marked for {student_dict['name']} ({student_dict['student_id']}) today at {formatted_time}."
        }

    try:
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time, status, method) VALUES (?, ?, ?, ?, ?)",
            (student_id, today_date, current_time, status, method)
        )
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()

        return {
            "success": True,
            "already_marked": False,
            "student": student_dict,
            "attendance": {
                "id": record_id,
                "student_id": student_id,
                "date": today_date,
                "time": current_time,
                "status": status,
                "method": method
            },
            "message": f"Attendance marked Present for {student_dict['name']} ({student_dict['student_id']})!"
        }
    except sqlite3.IntegrityError:
        conn.close()
        return {
            "success": False,
            "already_marked": True,
            "student": student_dict,
            "message": f"Attendance already recorded for {student_dict['name']} on {today_date}."
        }
    except Exception as e:
        conn.close()
        return {"success": False, "message": str(e)}

def update_manual_attendance(student_id, status, target_date=None, db_path=None):
    """Allows manual toggling/entry of attendance status for a student."""
    date_val = target_date or datetime.now().strftime('%Y-%m-%d')
    time_val = datetime.now().strftime('%H:%M:%S')
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT student_id, name FROM students WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return {"success": False, "message": f"Student ID '{student_id}' not found."}

    student_dict = dict(student)

    if status == 'Absent':
        # Remove present record if toggled to Absent
        cursor.execute("DELETE FROM attendance WHERE student_id = ? AND date = ?", (student_id, date_val))
        conn.commit()
        conn.close()
        return {
            "success": True,
            "status": "Absent",
            "student": student_dict,
            "message": f"{student_dict['name']} marked Absent for {date_val}."
        }
    else:
        # Upsert Present status
        cursor.execute(
            """
            INSERT INTO attendance (student_id, date, time, status, method)
            VALUES (?, ?, ?, 'Present', 'Manual')
            ON CONFLICT(student_id, date) DO UPDATE SET status='Present', method='Manual', time=?
            """,
            (student_id, date_val, time_val, time_val)
        )
        conn.commit()
        conn.close()
        return {
            "success": True,
            "status": "Present",
            "student": student_dict,
            "message": f"{student_dict['name']} marked Present manually for {date_val}."
        }

def get_today_attendance(date_val=None, db_path=None):
    """Retrieves all attendance records for today along with student info."""
    target_date = date_val or datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    sql = """
        SELECT a.id, a.student_id, s.name, s.department, a.date, a.time, a.status, a.method
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.date = ?
        ORDER BY a.time DESC
    """
    cursor.execute(sql, (target_date,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_dashboard_stats(date_val=None, db_path=None):
    """Calculates high-level statistics for the dashboard."""
    target_date = date_val or datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Total registered students
    cursor.execute("SELECT COUNT(*) as count FROM students")
    total_students = cursor.fetchone()['count']

    # Present students today
    cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM attendance WHERE date = ? AND status = 'Present'", (target_date,))
    present_today = cursor.fetchone()['count']

    absent_today = max(0, total_students - present_today)
    attendance_rate = round((present_today / total_students * 100), 1) if total_students > 0 else 0.0

    # Department breakdown
    cursor.execute("""
        SELECT s.department, COUNT(DISTINCT s.student_id) as total,
               COUNT(DISTINCT a.student_id) as present
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND a.date = ? AND a.status = 'Present'
        GROUP BY s.department
        ORDER BY s.department ASC
    """, (target_date,))
    dept_rows = cursor.fetchall()

    dept_stats = []
    for r in dept_rows:
        tot = r['total']
        pres = r['present']
        pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
        dept_stats.append({
            "department": r['department'],
            "total": tot,
            "present": pres,
            "absent": max(0, tot - pres),
            "percentage": pct
        })

    conn.close()

    return {
        "date": target_date,
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_rate": attendance_rate,
        "department_stats": dept_stats
    }

def get_attendance_history(start_date=None, end_date=None, target_date=None, department=None, search=None, db_path=None):
    """Retrieves full attendance logs with multi-field filtering."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    sql = """
        SELECT a.id, a.student_id, s.name, s.department, a.date, a.time, a.status, a.method
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE 1=1
    """
    params = []

    if target_date and target_date.strip():
        sql += " AND a.date = ?"
        params.append(target_date.strip())
    else:
        if start_date and start_date.strip():
            sql += " AND a.date >= ?"
            params.append(start_date.strip())
        if end_date and end_date.strip():
            sql += " AND a.date <= ?"
            params.append(end_date.strip())

    if department and department.strip() and department != "All":
        sql += " AND s.department = ?"
        params.append(department.strip())

    if search and search.strip():
        q = f"%{search.strip()}%"
        sql += " AND (a.student_id LIKE ? OR s.name LIKE ?)"
        params.extend([q, q])

    sql += " ORDER BY a.date DESC, a.time DESC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def generate_attendance_csv(start_date=None, end_date=None, target_date=None, department=None, db_path=None):
    """Generates CSV text content for downloading attendance records."""
    records = get_attendance_history(
        start_date=start_date,
        end_date=end_date,
        target_date=target_date,
        department=department,
        db_path=db_path
    )
    
    headers = ["ID", "Student ID", "Student Name", "Department", "Date", "Time", "Status", "Method"]
    lines = [",".join(headers)]
    
    for r in records:
        row = [
            str(r['id']),
            f'"{r["student_id"]}"',
            f'"{r["name"]}"',
            f'"{r["department"]}"',
            r['date'],
            r['time'],
            r['status'],
            r['method']
        ]
        lines.append(",".join(row))
        
    return "\n".join(lines)

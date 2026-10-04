import os
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for
from database import (
    init_db,
    register_student,
    get_students,
    find_student_by_speech,
    mark_attendance,
    update_manual_attendance,
    get_today_attendance,
    get_dashboard_stats,
    get_attendance_history,
    generate_attendance_csv
)

app = Flask(__name__)
app.secret_key = "voice_attendance_secret_key_antigravity"

# Initialize SQLite database schema upon startup
init_db()

# --- PAGE ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/voice-attendance')
def voice_attendance():
    return render_template('voice_attendance.html', active_page='voice_attendance')

@app.route('/students')
def students():
    return render_template('students.html', active_page='students')

@app.route('/history')
def history():
    return render_template('history.html', active_page='history')

@app.route('/manual-attendance')
def manual_attendance():
    return render_template('manual_attendance.html', active_page='manual_attendance')


# --- REST API ENDPOINTS ---

@app.route('/api/stats', methods=['GET'])
def api_stats():
    date_param = request.args.get('date')
    stats = get_dashboard_stats(date_val=date_param)
    return jsonify(stats)

@app.route('/api/students', methods=['GET'])
def api_get_students():
    query = request.args.get('query', '')
    department = request.args.get('department', '')
    student_list = get_students(query=query, department=department)
    return jsonify({"success": True, "students": student_list, "count": len(student_list)})

@app.route('/api/students/register', methods=['POST'])
def api_register_student():
    data = request.get_json() or {}
    student_id = data.get('student_id', '')
    name = data.get('name', '')
    department = data.get('department', '')

    result = register_student(student_id, name, department)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@app.route('/api/attendance/voice-mark', methods=['POST'])
def api_voice_mark_attendance():
    """
    Process speech recognition transcript, match student, and record attendance.
    Prevents duplicate attendance for same student on same day.
    """
    data = request.get_json() or {}
    transcript = data.get('transcript', '')

    if not transcript or not transcript.strip():
        return jsonify({
            "success": False,
            "message": "No speech transcript provided. Please try speaking again."
        }), 400

    # Speech-to-student matching algorithm
    matched_student = find_student_by_speech(transcript)

    if not matched_student:
        return jsonify({
            "success": False,
            "matched": False,
            "transcript": transcript,
            "message": f"No registered student found matching spoken phrase '{transcript}'."
        }), 404

    # Mark attendance for matched student
    result = mark_attendance(
        student_id=matched_student['student_id'],
        status='Present',
        method='Voice'
    )

    result['matched'] = True
    result['transcript'] = transcript
    result['student'] = matched_student

    if result.get('already_marked'):
        return jsonify(result), 409  # Conflict status code for duplicate
    elif result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/api/attendance/today', methods=['GET'])
def api_today_attendance():
    date_param = request.args.get('date')
    records = get_today_attendance(date_val=date_param)
    return jsonify({"success": True, "attendance": records, "count": len(records)})

@app.route('/api/attendance/manual-mark', methods=['POST'])
def api_manual_mark_attendance():
    data = request.get_json() or {}
    student_id = data.get('student_id', '')
    status = data.get('status', 'Present')
    target_date = data.get('date')

    if not student_id:
        return jsonify({"success": False, "message": "Student ID is required."}), 400

    result = update_manual_attendance(student_id=student_id, status=status, target_date=target_date)
    return jsonify(result)

@app.route('/api/attendance/history', methods=['GET'])
def api_attendance_history():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    target_date = request.args.get('date')
    department = request.args.get('department')
    search = request.args.get('search')

    records = get_attendance_history(
        start_date=start_date,
        end_date=end_date,
        target_date=target_date,
        department=department,
        search=search
    )
    return jsonify({"success": True, "records": records, "count": len(records)})

@app.route('/api/attendance/export-csv', methods=['GET'])
def api_export_csv():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    target_date = request.args.get('date')
    department = request.args.get('department')

    csv_data = generate_attendance_csv(
        start_date=start_date,
        end_date=end_date,
        target_date=target_date,
        department=department
    )
    filename = f"attendance_export_{target_date or 'history'}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


if __name__ == '__main__':
    print("Starting Voice-Based Student Attendance System...")
    print("Server running at: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

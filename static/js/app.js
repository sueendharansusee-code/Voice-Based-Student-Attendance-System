/**
 * Voice Attendance System - Main Application Logic & UI Handlers
 */

// Global Toast Notification Helper
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'warning') icon = '⚠️';
    if (type === 'error') icon = '❌';

    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.1rem;">${icon}</span>
            <span style="font-size: 0.9rem; font-weight: 500;">${message}</span>
        </div>
        <button onclick="this.parentElement.remove()" style="background:none; border:none; color:#64748b; font-size:1.1rem; cursor:pointer;">&times;</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 4500);
}

// Format Time helper (HH:MM:SS -> 12hr AM/PM)
function formatTime12Hr(timeStr) {
    if (!timeStr) return '';
    const parts = timeStr.split(':');
    if (parts.length < 2) return timeStr;
    let hours = parseInt(parts[0], 10);
    const minutes = parts[1];
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${hours}:${minutes} ${ampm}`;
}


// --- DASHBOARD FUNCTIONS ---

async function loadDashboardStats() {
    const totalEl = document.getElementById('stat-total-students');
    const presentEl = document.getElementById('stat-present-today');
    const absentEl = document.getElementById('stat-absent-today');
    const rateEl = document.getElementById('stat-attendance-rate');

    if (!totalEl) return;

    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        totalEl.innerText = data.total_students;
        presentEl.innerText = data.present_today;
        absentEl.innerText = data.absent_today;
        rateEl.innerText = `${data.attendance_rate}%`;

        renderDepartmentBreakdown(data.department_stats || []);
    } catch (err) {
        console.error("Error loading dashboard stats:", err);
    }
}

function renderDepartmentBreakdown(deptStats) {
    const container = document.getElementById('dept-breakdown-list');
    if (!container) return;

    if (deptStats.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No department data available.</p>`;
        return;
    }

    let html = '';
    deptStats.forEach(d => {
        html += `
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.3rem;">
                    <span>${d.department}</span>
                    <span>${d.present} / ${d.total} (${d.percentage}%)</span>
                </div>
                <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: var(--primary); width: ${d.percentage}%; height: 100%; border-radius: 4px; transition: width 0.5s;"></div>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

async function loadTodayAttendanceTable() {
    const tbody = document.getElementById('today-attendance-tbody');
    if (!tbody) return;

    try {
        const response = await fetch('/api/attendance/today');
        const data = await response.json();

        if (!data.attendance || data.attendance.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 2rem;">No attendance recorded today yet. Use Voice Attendance Kiosk above to get started!</td></tr>`;
            return;
        }

        let html = '';
        data.attendance.forEach((r, idx) => {
            const badgeClass = r.method === 'Voice' ? 'badge-voice' : 'badge-manual';
            html += `
                <tr>
                    <td><strong>#${idx + 1}</strong></td>
                    <td><code>${r.student_id}</code></td>
                    <td><strong>${r.name}</strong></td>
                    <td>${r.department}</td>
                    <td>${formatTime12Hr(r.time)}</td>
                    <td>
                        <span class="badge badge-present">Present</span>
                        <span class="badge ${badgeClass}">${r.method}</span>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error("Error loading today's attendance table:", err);
    }
}

// Global hook so voice controller can trigger instant refresh
window.refreshTodayAttendance = function() {
    loadDashboardStats();
    loadTodayAttendanceTable();
};


// --- STUDENT DIRECTORY & REGISTRATION ---

async function loadStudentDirectory() {
    const tbody = document.getElementById('student-directory-tbody');
    if (!tbody) return;

    const query = document.getElementById('student-search-input')?.value || '';
    const dept = document.getElementById('student-dept-filter')?.value || '';

    try {
        const response = await fetch(`/api/students?query=${encodeURIComponent(query)}&department=${encodeURIComponent(dept)}`);
        const data = await response.json();

        if (!data.students || data.students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 2rem;">No students found. Add a new student using the registration form.</td></tr>`;
            return;
        }

        let html = '';
        data.students.forEach((s, idx) => {
            html += `
                <tr>
                    <td>${idx + 1}</td>
                    <td><code>${s.student_id}</code></td>
                    <td><strong>${s.name}</strong></td>
                    <td><span class="badge badge-voice">${s.department}</span></td>
                    <td>${s.created_at ? s.created_at.split(' ')[0] : 'N/A'}</td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error("Error loading students:", err);
    }
}

function bindStudentRegisterForm() {
    const form = document.getElementById('student-register-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const studentId = document.getElementById('reg-student-id').value.trim();
        const name = document.getElementById('reg-student-name').value.trim();
        const department = document.getElementById('reg-student-dept').value.trim();

        if (!studentId || !name || !department) {
            showToast("Please fill in all registration fields.", "warning");
            return;
        }

        try {
            const response = await fetch('/api/students/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: studentId, name: name, department: department })
            });

            const data = await response.json();

            if (data.success) {
                showToast(data.message, "success");
                form.reset();
                loadStudentDirectory();
                loadDashboardStats();
            } else {
                showToast(data.message || "Registration failed.", "error");
            }
        } catch (err) {
            console.error("Error registering student:", err);
            showToast("Error connecting to server.", "error");
        }
    });
}


// --- ATTENDANCE HISTORY & CSV EXPORT ---

async function loadAttendanceHistory() {
    const tbody = document.getElementById('history-table-tbody');
    if (!tbody) return;

    const startDate = document.getElementById('hist-start-date')?.value || '';
    const endDate = document.getElementById('hist-end-date')?.value || '';
    const dept = document.getElementById('hist-dept-filter')?.value || '';
    const search = document.getElementById('hist-search-input')?.value || '';

    const url = `/api/attendance/history?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&department=${encodeURIComponent(dept)}&search=${encodeURIComponent(search)}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (!data.records || data.records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-muted); padding: 2rem;">No attendance history logs match your search filters.</td></tr>`;
            return;
        }

        let html = '';
        data.records.forEach((r, idx) => {
            const badgeMethod = r.method === 'Voice' ? 'badge-voice' : 'badge-manual';
            const badgeStatus = r.status === 'Present' ? 'badge-present' : 'badge-absent';
            html += `
                <tr>
                    <td>${idx + 1}</td>
                    <td><code>${r.student_id}</code></td>
                    <td><strong>${r.name}</strong></td>
                    <td>${r.department}</td>
                    <td>${r.date}</td>
                    <td>${formatTime12Hr(r.time)}</td>
                    <td>
                        <span class="badge ${badgeStatus}">${r.status}</span>
                        <span class="badge ${badgeMethod}">${r.method}</span>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error("Error loading attendance history:", err);
    }
}

function bindExportCSV() {
    const exportBtn = document.getElementById('btn-export-csv');
    if (!exportBtn) return;

    exportBtn.addEventListener('click', () => {
        const startDate = document.getElementById('hist-start-date')?.value || '';
        const endDate = document.getElementById('hist-end-date')?.value || '';
        const dept = document.getElementById('hist-dept-filter')?.value || '';

        const url = `/api/attendance/export-csv?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}&department=${encodeURIComponent(dept)}`;
        window.location.href = url;
    });
}


// --- MANUAL ATTENDANCE TOGGLE ---

async function loadManualAttendanceList() {
    const tbody = document.getElementById('manual-attendance-tbody');
    if (!tbody) return;

    const dateVal = document.getElementById('manual-date-picker')?.value || new Date().toISOString().split('T')[0];

    try {
        const [studRes, attRes] = await Promise.all([
            fetch('/api/students'),
            fetch(`/api/attendance/today?date=${dateVal}`)
        ]);

        const studData = await studRes.json();
        const attData = await attRes.json();

        const presentSet = new Set(attData.attendance.map(a => a.student_id));

        if (!studData.students || studData.students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color: var(--text-muted); padding: 2rem;">No registered students. Please register students first.</td></tr>`;
            return;
        }

        let html = '';
        studData.students.forEach((s, idx) => {
            const isPresent = presentSet.has(s.student_id);
            html += `
                <tr>
                    <td>${idx + 1}</td>
                    <td><code>${s.student_id}</code></td>
                    <td><strong>${s.name}</strong></td>
                    <td>${s.department}</td>
                    <td>
                        <button class="${isPresent ? 'btn-success' : 'btn-secondary'}" 
                                onclick="toggleManualAttendance('${s.student_id}', '${isPresent ? 'Absent' : 'Present'}')">
                            ${isPresent ? '✓ Present (Click to Mark Absent)' : '✗ Absent (Click to Mark Present)'}
                        </button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error("Error loading manual attendance:", err);
    }
}

async function toggleManualAttendance(studentId, newStatus) {
    const dateVal = document.getElementById('manual-date-picker')?.value || new Date().toISOString().split('T')[0];

    try {
        const response = await fetch('/api/attendance/manual-mark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId, status: newStatus, date: dateVal })
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, "success");
            loadManualAttendanceList();
            loadDashboardStats();
        } else {
            showToast(data.message || "Failed to update attendance", "error");
        }
    } catch (err) {
        console.error("Error toggling manual attendance:", err);
    }
}


// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadTodayAttendanceTable();
    loadStudentDirectory();
    bindStudentRegisterForm();
    loadAttendanceHistory();
    bindExportCSV();
    loadManualAttendanceList();

    // Bind Search/Filter Events
    const studentSearchInput = document.getElementById('student-search-input');
    const studentDeptFilter = document.getElementById('student-dept-filter');
    if (studentSearchInput) studentSearchInput.addEventListener('input', loadStudentDirectory);
    if (studentDeptFilter) studentDeptFilter.addEventListener('change', loadStudentDirectory);

    const histSearchInput = document.getElementById('hist-search-input');
    const histDeptFilter = document.getElementById('hist-dept-filter');
    const histStartDate = document.getElementById('hist-start-date');
    const histEndDate = document.getElementById('hist-end-date');

    if (histSearchInput) histSearchInput.addEventListener('input', loadAttendanceHistory);
    if (histDeptFilter) histDeptFilter.addEventListener('change', loadAttendanceHistory);
    if (histStartDate) histStartDate.addEventListener('change', loadAttendanceHistory);
    if (histEndDate) histEndDate.addEventListener('change', loadAttendanceHistory);

    const manualDatePicker = document.getElementById('manual-date-picker');
    if (manualDatePicker) {
        manualDatePicker.value = new Date().toISOString().split('T')[0];
        manualDatePicker.addEventListener('change', loadManualAttendanceList);
    }
});

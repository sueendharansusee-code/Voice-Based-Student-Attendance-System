/**
 * Voice Speech Recognition Module
 * Integrates Web Speech API with Flask Backend Attendance Engine
 */

class VoiceAttendanceController {
    constructor() {
        this.recognition = null;
        this.isListening = false;

        // DOM elements
        this.micBtnWrapper = document.getElementById('mic-button-wrapper');
        this.micBtn = document.getElementById('mic-btn');
        this.statusText = document.getElementById('speech-status-text');
        this.transcriptDisplay = document.getElementById('speech-transcript-display');
        this.audioWaves = document.getElementById('audio-waves');
        this.resultCard = document.getElementById('match-result-card');
        this.manualFallbackForm = document.getElementById('manual-fallback-form');
        this.manualInput = document.getElementById('manual-speech-input');

        this.initSpeechEngine();
        this.bindEvents();
    }

    initSpeechEngine() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn("Web Speech API is not supported in this browser.");
            if (this.statusText) {
                this.statusText.innerHTML = `<span style="color: #ef4444;">⚠️ Web Speech API is not supported in this browser. Please use Chrome, Edge, or Safari, or enter student ID/Name manually below.</span>`;
            }
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            this.isListening = true;
            this.setListeningState(true);
            this.updateStatus("🎙️ Listening... Speak student name or ID clearly.");
            this.transcriptDisplay.innerText = "...";
            this.hideResultCard();
        };

        this.recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const currentText = finalTranscript || interimTranscript;
            if (currentText) {
                this.transcriptDisplay.innerText = `"${currentText}"`;
            }

            if (finalTranscript) {
                console.log("Final Speech Recognized:", finalTranscript);
                this.processSpeechTranscript(finalTranscript);
            }
        };

        this.recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            this.setListeningState(false);

            let errorMessage = "Speech recognition error occurred.";
            if (event.error === 'not-allowed' || event.error === 'permission-denied') {
                errorMessage = "Microphone access denied. Please allow microphone permissions in browser settings.";
            } else if (event.error === 'no-speech') {
                errorMessage = "No speech detected. Please tap microphone and try again.";
            } else if (event.error === 'network') {
                errorMessage = "Network connection error during speech recognition.";
            }

            this.updateStatus(`❌ ${errorMessage}`);
            showToast(errorMessage, "error");
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this.setListeningState(false);
        };
    }

    bindEvents() {
        if (this.micBtn) {
            this.micBtn.addEventListener('click', () => {
                this.toggleListening();
            });
        }

        if (this.manualFallbackForm) {
            this.manualFallbackForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const value = this.manualInput.value.trim();
                if (value) {
                    this.processSpeechTranscript(value);
                    this.manualInput.value = '';
                }
            });
        }
    }

    toggleListening() {
        if (!this.recognition) {
            showToast("Web Speech API not supported in your browser. Use manual entry below.", "warning");
            return;
        }

        if (this.isListening) {
            this.recognition.stop();
            this.setListeningState(false);
        } else {
            try {
                this.recognition.start();
            } catch (err) {
                console.error("Error starting recognition:", err);
                this.recognition.stop();
                setTimeout(() => this.recognition.start(), 200);
            }
        }
    }

    setListeningState(active) {
        if (this.micBtnWrapper) {
            if (active) {
                this.micBtnWrapper.classList.add('listening');
                if (this.audioWaves) this.audioWaves.classList.add('active');
            } else {
                this.micBtnWrapper.classList.remove('listening');
                if (this.audioWaves) this.audioWaves.classList.remove('active');
            }
        }
    }

    updateStatus(message) {
        if (this.statusText) {
            this.statusText.innerText = message;
        }
    }

    async processSpeechTranscript(transcriptText) {
        this.updateStatus("🔄 Matching transcript with student records...");

        try {
            const response = await fetch('/api/attendance/voice-mark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transcript: transcriptText })
            });

            const data = await response.json();

            if (response.status === 200 && data.success) {
                // Success: Attendance Marked
                this.showResultCard({
                    type: 'success',
                    title: '✅ Attendance Recorded!',
                    message: data.message,
                    student: data.student,
                    time: data.attendance.time,
                    method: data.attendance.method
                });
                showToast(`Attendance marked for ${data.student.name}`, "success");
                this.updateStatus("✨ Success! Say next student name or ID.");

                // Trigger today's attendance table refresh if listener exists
                if (window.refreshTodayAttendance) {
                    window.refreshTodayAttendance();
                }

            } else if (response.status === 409 || data.already_marked) {
                // Duplicate Attendance Warning
                this.showResultCard({
                    type: 'duplicate',
                    title: '⚠️ Duplicate Attendance Detected',
                    message: data.message,
                    student: data.student,
                    time: data.attendance ? data.attendance.time : ''
                });
                showToast(data.message, "warning");
                this.updateStatus("⚠️ Attendance was already marked for this student today.");

            } else if (response.status === 404 || !data.matched) {
                // No Matching Student Found
                this.showResultCard({
                    type: 'error',
                    title: '❌ Student Not Found',
                    message: `No student record found matching '${transcriptText}'. Ensure student is registered with this exact Name or ID.`,
                });
                showToast(`No student matched '${transcriptText}'`, "error");
                this.updateStatus("❌ No match found. Please try again or register student.");

            } else {
                // Other Error
                this.showResultCard({
                    type: 'error',
                    title: '❌ Error',
                    message: data.message || "Failed to process attendance."
                });
                showToast(data.message || "Error processing attendance", "error");
                this.updateStatus("❌ Error recording attendance.");
            }

        } catch (error) {
            console.error("Network Error:", error);
            this.showResultCard({
                type: 'error',
                title: '❌ Network Error',
                message: "Unable to connect to Flask server. Please check your network connection."
            });
            showToast("Server connection error.", "error");
            this.updateStatus("❌ Connection error.");
        }
    }

    showResultCard(info) {
        if (!this.resultCard) return;

        this.resultCard.className = `match-result-card ${info.type}`;
        
        let detailsHtml = '';
        if (info.student) {
            detailsHtml = `
                <div style="margin-top: 0.75rem; display: flex; gap: 1.5rem; flex-wrap: wrap;">
                    <div><strong>Student ID:</strong> ${info.student.student_id}</div>
                    <div><strong>Name:</strong> ${info.student.name}</div>
                    <div><strong>Department:</strong> ${info.student.department}</div>
                    ${info.time ? `<div><strong>Time Recorded:</strong> ${info.time}</div>` : ''}
                </div>
            `;
        }

        this.resultCard.innerHTML = `
            <h4 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem;">${info.title}</h4>
            <p style="font-size: 0.95rem;">${info.message}</p>
            ${detailsHtml}
        `;
        this.resultCard.style.display = 'block';
    }

    hideResultCard() {
        if (this.resultCard) {
            this.resultCard.style.display = 'none';
        }
    }
}

// Global initialization when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.voiceController = new VoiceAttendanceController();
});

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import requests
import threading

SUPABASE_URL = "https://gxdijcyjambxhigzxfgf.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd4ZGlqY3lqYW1ieGhpZ3p4ZmdmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjI4NjIyMywiZXhwIjoyMDg3ODYyMjIzfQ.jiSGc7GjFPuoku-sw7Zr9fE-WjjbWKSQ6jCkkwQNMoE"
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

RESEND_API_KEY = "re_2Cuw6HLd_DNg81QMcsJXbX3xmVaWTd13Z"
ACADEMY_EMAIL  = "srisrimehernayana@gmail.com"
EMAIL_FROM     = "Elite Dance Academy <onboarding@resend.dev>"

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})


# ----------------------------------------------------
# EMAIL HELPER
# ----------------------------------------------------

def _send_email(to, subject, body):
    """Send one email via Resend API."""
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from":    EMAIL_FROM,
                "to":      [to],
                "subject": subject,
                "text":    body
            }
        )
        print(f"✅ Email → {to} | status: {response.status_code} | {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Email failed → {to}: {e}")
        return False


def send_enrollment_emails(student_email, student_name, dance_style, phone, experience):
    """Send 2 emails in background threads — one to student, one to academy."""

    # ── Email 1: Welcome email to STUDENT ──
    student_subject = "🎉 Welcome to Elite Dance Academy!"
    student_body = f"""Hi {student_name},

Thank you for enrolling in the {dance_style} class at Elite Dance Academy!

We're excited to have you join our dance family 💃

Our team will contact you soon with class schedules and next steps.

Keep Dancing!
Elite Dance Academy
"""
    threading.Thread(
        target=_send_email,
        args=(student_email, student_subject, student_body),
        daemon=True
    ).start()

    # ── Email 2: Notification to ACADEMY OWNER ──
    academy_subject = f"📋 New Enrollment — {student_name} ({dance_style})"
    academy_body = f"""New student enrolled!

Name         : {student_name}
Email        : {student_email}
Phone        : {phone}
Dance Style  : {dance_style}
Experience   : {experience}

Please follow up with the student.

Elite Dance Academy
"""
    threading.Thread(
        target=_send_email,
        args=(ACADEMY_EMAIL, academy_subject, academy_body),
        daemon=True
    ).start()


def send_mentor_request_emails(user_name, user_email, message):
    """Send 2 emails — confirmation to user, alert to academy."""

    # ── Email 1: Confirmation to USER ──
    user_subject = "✅ We received your request — Elite Dance Academy"
    user_body = f"""Hi {user_name},

Thank you for reaching out to Elite Dance Academy!

We've received your message and one of our mentors will get back to you within 24 hours.

Your message:
"{message}"

See you on the dance floor! 🕺
Elite Dance Academy
"""
    threading.Thread(
        target=_send_email,
        args=(user_email, user_subject, user_body),
        daemon=True
    ).start()

    # ── Email 2: Alert to ACADEMY OWNER ──
    academy_subject = f"📩 New Mentor Request from {user_name}"
    academy_body = f"""New mentor request received via the website.

Name    : {user_name}
Email   : {user_email}
Message : {message}

Please contact this person soon.
Elite Dance Academy
"""
    threading.Thread(
        target=_send_email,
        args=(ACADEMY_EMAIL, academy_subject, academy_body),
        daemon=True
    ).start()


# ----------------------------------------------------
# ROUTES
# ----------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/test-supabase")
def test_supabase():
    try:
        data = supabase.table("enrollments").select("*").limit(1).execute()
        return jsonify({"connected": True, "data": data.data})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})


@app.route("/enroll", methods=["POST"])
def enroll():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required."}), 401

    token = auth_header.split(" ")[1]
    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user
        if user is None:
            return jsonify({"error": "Invalid session."}), 403
    except Exception as e:
        print("[AUTH ERROR]", e)
        return jsonify({"error": "Invalid or expired token"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided."}), 400

    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    try:
        response = supabase.table("enrollments").insert({
            "name":             data.get("name"),
            "email":            data.get("email"),
            "phone":            data.get("phone"),
            "age":              data.get("age"),
            "dance_style":      data.get("dance_style"),
            "experience_level": data.get("experience_level"),
            "user_id":          user.id
        }).execute()

        # Send to BOTH student and academy
        send_enrollment_emails(
            student_email = data.get("email"),
            student_name  = data.get("name"),
            dance_style   = data.get("dance_style"),
            phone         = data.get("phone"),
            experience    = data.get("experience_level")
        )

        return jsonify({"message": "Enrollment successful!", "data": response.data}), 201

    except Exception as e:
        print("[DB ERROR]", e)
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route("/contact", methods=["POST"])
def contact():
    data    = request.get_json()
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400

    # Send to BOTH user and academy
    send_mentor_request_emails(name, email, message)

    return jsonify({"message": "Request received! We'll contact you within 24 hours. 🎉"}), 200


# ----------------------------------------------------
# RUN SERVER
# ----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

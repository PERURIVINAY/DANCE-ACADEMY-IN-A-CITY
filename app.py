from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
import resend


# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = "https://gxdijcyjambxhigzxfgf.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd4ZGlqY3lqYW1ieGhpZ3p4ZmdmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjI4NjIyMywiZXhwIjoyMDg3ODYyMjIzfQ.jiSGc7GjFPuoku-sw7Zr9fE-WjjbWKSQ6jCkkwQNMoE"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------------
# EMAIL CONFIG
# -----------------------------
EMAIL_SENDER   = "vinayperuri934@gmail.com"
EMAIL_PASSWORD = "dgsf detg pszu vmef"


# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app, resources={r"/*": {"origins": "*"}})


# ----------------------------------------------------
# EMAIL HELPERS
# ----------------------------------------------------


# ikkada change cheyyandi
resend.api_key = os.environ.get("re_4YCNtaZw_EooMdt5cGjzokW9jWYBGNMpe")

def _send_email(to_address, subject, body):
    try:
        resend.Emails.send({
            "from": "Elite Dance <onboarding@resend.dev>",
            "to": to_address,
            "subject": subject,
            "text": body
        })
        print(f"✅ Email sent to {to_address}")
    except Exception as e:
        print(f"❌ Email failed: {e}")
def send_thank_you_email(user_email, user_name, dance_style):
    """Sent to student after enrollment — runs in background thread."""
    subject = "🎉 Welcome to Elite Dance Academy!"
    body = f"""
Hi {user_name},

Thank you for enrolling in the {dance_style} class at Elite Dance Academy!

We're excited to have you join our dance family 💃

Our team will contact you soon with class schedules and next steps.

Keep Dancing!

Elite Dance Academy
"""
    threading.Thread(
        target=_send_email,
        args=(user_email, subject, body),
        daemon=True
    ).start()


def send_mentor_request_email(user_email, user_name, message):
    """
    Two emails sent in background threads:
      1. Confirmation to the person who filled the form.
      2. Internal notification to the academy inbox.
    """
    # --- Confirmation to user ---
    user_subject = "✅ We received your request — Elite Dance Academy"
    user_body = f"""
Hi {user_name},

Thank you for reaching out to Elite Dance Academy!

We've received your message and one of our mentors will get back to you within 24 hours.

Your message:
\"{message}\"

See you on the dance floor! 🕺

Elite Dance Academy
"""
    threading.Thread(
        target=_send_email,
        args=(user_email, user_subject, user_body),
        daemon=True
    ).start()

    # --- Internal alert to academy ---
    admin_subject = f"📩 New Mentor Request from {user_name}"
    admin_body = f"""
New mentor request received via the website.

Name    : {user_name}
Email   : {user_email}
Message : {message}

Log in to Supabase to view all requests:
https://app.supabase.com
"""
    threading.Thread(
        target=_send_email,
        args=(EMAIL_SENDER, admin_subject, admin_body),
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


# ----------------------------------------------------
# ENROLL ROUTE
# ----------------------------------------------------
@app.route("/enroll", methods=["POST"])
def enroll():

    # 1️⃣ Check Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required. Please sign in."}), 401

    token = auth_header.split(" ")[1]

    # 2️⃣ Verify Supabase user
    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user
        if user is None:
            return jsonify({"error": "Invalid session. Please login again."}), 403
    except Exception as e:
        print("[AUTH ERROR]", e)
        return jsonify({"error": "Invalid or expired token"}), 403

    # 3️⃣ Parse JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "No enrollment data provided."}), 400

    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # 4️⃣ Insert into database
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

        # 5️⃣ Send confirmation email (non-blocking)
        send_thank_you_email(data.get("email"), data.get("name"), data.get("dance_style"))

        return jsonify({"message": "Enrollment successful!", "data": response.data}), 201

    except Exception as e:
        print("[DB ERROR]", e)
        return jsonify({"error": f"Database error: {str(e)}"}), 500


# ----------------------------------------------------
# MENTOR REQUEST ROUTE
# ----------------------------------------------------
@app.route("/mentor-request", methods=["POST"])
def mentor_request():

    # 1️⃣ Parse JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided."}), 400

    # 2️⃣ Validate required fields
    required_fields = ["name", "email"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    message = data.get("message", "").strip()

    # 3️⃣ Basic email format check
    if "@" not in email or "." not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    # 4️⃣ Save to Supabase
    try:
        response = supabase.table("mentor_requests").insert({
            "name":    name,
            "email":   email,
            "message": message
        }).execute()

        # 5️⃣ Send emails (non-blocking)
        send_mentor_request_email(email, name, message)

        return jsonify({
            "message": "Request received! We'll contact you within 24 hours. 🎉"
        }), 201

    except Exception as e:
        print("[MENTOR REQUEST DB ERROR]", e)
        return jsonify({"error": f"Could not save request: {str(e)}"}), 500


# ----------------------------------------------------
# RUN SERVER  ← FIX: reads PORT from environment (required by Render)
# ----------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

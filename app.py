from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# -----------------------------
# SUPABASE CONFIG (FROM ENV)
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------------
# EMAIL CONFIG (FROM ENV)
# -----------------------------
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

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

def send_thank_you_email(user_email, user_name, dance_style):
    subject = "🎉 Welcome to Elite Dance Academy!"

    body = f"""
Hi {user_name},

Thank you for enrolling in the {dance_style} class at Elite Dance Academy!

We're excited to have you join our dance family 💃

Our team will contact you soon with class schedules and next steps.

Keep Dancing!

Elite Dance Academy
"""

    _send_email(user_email, subject, body)


def send_mentor_request_email(user_email, user_name, message):

    # Email to user
    user_subject = "✅ We received your request — Elite Dance Academy"

    user_body = f"""
Hi {user_name},

Thank you for reaching out to Elite Dance Academy!

We've received your message and one of our mentors will get back to you within 24 hours.

Your message:
"{message}"

See you on the dance floor! 🕺

Elite Dance Academy
"""

    _send_email(user_email, user_subject, user_body)

    # Email to academy
    admin_subject = f"📩 New Mentor Request from {user_name}"

    admin_body = f"""
New mentor request received via the website.

Name    : {user_name}
Email   : {user_email}
Message : {message}

Check Supabase dashboard for details.
"""

    _send_email(EMAIL_SENDER, admin_subject, admin_body)


def _send_email(to_address, subject, body):

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_address
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_address, msg.as_string())
        server.quit()

        print(f"Email sent to {to_address}")

    except Exception as e:
        print("Email failed:", e)


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

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401

    token = auth_header.split(" ")[1]

    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user

        if user is None:
            return jsonify({"error": "Invalid session"}), 403

    except Exception as e:
        return jsonify({"error": "Invalid token"}), 403

    data = request.get_json()

    required_fields = ["name", "email", "phone", "dance_style", "experience_level"]

    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:

        response = supabase.table("enrollments").insert({
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "age": data.get("age"),
            "dance_style": data.get("dance_style"),
            "experience_level": data.get("experience_level"),
            "user_id": user.id
        }).execute()

        send_thank_you_email(
            data.get("email"),
            data.get("name"),
            data.get("dance_style")
        )

        return jsonify({
            "message": "Enrollment successful!"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------
# MENTOR REQUEST
# ----------------------------------------------------

@app.route("/mentor-request", methods=["POST"])
def mentor_request():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email:
        return jsonify({"error": "Missing required fields"}), 400

    try:

        supabase.table("mentor_requests").insert({
            "name": name,
            "email": email,
            "message": message
        }).execute()

        send_mentor_request_email(email, name, message)

        return jsonify({
            "message": "Request received! We'll contact you soon."
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------
# RUN SERVER
# ----------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )

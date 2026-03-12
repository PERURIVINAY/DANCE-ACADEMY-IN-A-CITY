from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = "https://gxdijcyjambxhigzxfgf.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd4ZGlqY3lqYW1ieGhpZ3p4ZmdmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjI4NjIyMywiZXhwIjoyMDg3ODYyMjIzfQ.jiSGc7GjFPuoku-sw7Zr9fE-WjjbWKSQ6jCkkwQNMoE"

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# -----------------------------
# EMAIL CONFIG
# -----------------------------
EMAIL_SENDER = "vinayperuri934@gmail.com"
EMAIL_PASSWORD = "dgsf detg pszu vmef"

# ----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app, resources={r"/*": {"origins": "*"}})

# ----------------------------------------------------
# EMAIL FUNCTION
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

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = user_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, user_email, msg.as_string())
        server.quit()

        print(f"✅ Email sent to {user_email}")

    except Exception as e:
        print("❌ Email sending failed:", e)


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

        return jsonify({
            "connected": True,
            "data": data.data
        })

    except Exception as e:
        return jsonify({
            "connected": False,
            "error": str(e)
        })


# ----------------------------------------------------
# ENROLL ROUTE
# ----------------------------------------------------
@app.route("/enroll", methods=["POST"])
def enroll():

    # -----------------------------
    # 1️⃣ Check Authorization
    # -----------------------------
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({
            "error": "Authentication required. Please sign in."
        }), 401

    token = auth_header.split(" ")[1]

    # -----------------------------
    # 2️⃣ Verify Supabase user
    # -----------------------------
    try:
        auth_response = supabase.auth.get_user(token)
        user = auth_response.user

        if user is None:
            return jsonify({
                "error": "Invalid session. Please login again."
            }), 403

    except Exception as e:
        print("[AUTH ERROR]", e)

        return jsonify({
            "error": "Invalid or expired token"
        }), 403


    # -----------------------------
    # 3️⃣ Parse JSON
    # -----------------------------
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No enrollment data provided."
        }), 400


    required_fields = [
        "name",
        "email",
        "phone",
        "dance_style",
        "experience_level"
    ]

    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return jsonify({
            "error": f"Missing fields: {', '.join(missing)}"
        }), 400


    # -----------------------------
    # 4️⃣ Insert into database
    # -----------------------------
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


        # -----------------------------
        # 5️⃣ SEND EMAIL AUTOMATICALLY
        # -----------------------------
        send_thank_you_email(
            data.get("email"),
            data.get("name"),
            data.get("dance_style")
        )


        return jsonify({
            "message": "Enrollment successful!",
            "data": response.data
        }), 201


    except Exception as e:

        print("[DB ERROR]", e)

        return jsonify({
            "error": f"Database error: {str(e)}"
        }), 500


# ----------------------------------------------------
# RUN SERVER
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

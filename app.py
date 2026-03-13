from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client
import os
import traceback
import requests

# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# -----------------------------
# BREVO EMAIL CONFIG
# -----------------------------
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

# Safe Supabase init
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase connected")
except Exception as e:
    supabase = None
    print("Supabase init failed:", e)


# -----------------------------
# EMAIL FUNCTION (Brevo)
# -----------------------------
def send_email(to_email, subject, html_body):
    try:
        if not BREVO_API_KEY:
            print("BREVO_API_KEY not set")
            return False

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json={
                "sender": {
                    "name": "Elite Dance Academy",
                    "email": BREVO_SENDER_EMAIL
                },
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_body
            },
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print("Brevo response:", response.status_code, response.text)
        return response.status_code == 201

    except Exception as e:
        print("Email error:", e)
        return False


# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# SUPABASE TEST ROUTE
# -----------------------------
@app.route("/test-supabase")
def test_supabase():
    try:
        if not supabase:
            return jsonify({"connected": False, "error": "Supabase not initialized"}), 500
        data = supabase.table("enrollments").select("*").limit(1).execute()
        return jsonify({"connected": True, "data": data.data})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 500


# -----------------------------
# EMAIL TEST ROUTE
# -----------------------------
@app.route("/test-email")
def test_email():
    success = send_email(
        BREVO_SENDER_EMAIL,
        "Test Email from Elite Dance Academy",
        "<h2>Email works!</h2><p>Brevo is configured correctly.</p>"
    )
    if success:
        return jsonify({"message": "Test email sent successfully"})
    return jsonify({"error": "Failed. Check BREVO_API_KEY and BREVO_SENDER_EMAIL in Railway."}), 500


# -----------------------------
# ENROLL ROUTE
# -----------------------------
@app.route("/enroll", methods=["POST"])
def enroll():
    try:
        if not supabase:
            return jsonify({"error": "Database not connected."}), 500

        # Verify Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized. Please sign in."}), 401

        token = auth_header.split(" ")[1]

        try:
            user_response = supabase.auth.get_user(token)
            if not user_response or not user_response.user:
                return jsonify({"error": "Invalid or expired session. Please sign in again."}), 401
        except Exception as auth_err:
            print("Auth error:", auth_err)
            return jsonify({"error": "Session verification failed. Please sign in again."}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        name        = (data.get("name") or "").strip()
        email       = (data.get("email") or "").strip()
        phone       = (data.get("phone") or "").strip()
        age         = data.get("age")
        dance_style = (data.get("dance_style") or "").strip()
        experience  = (data.get("experience_level") or "").strip()

        if not name or not email or not phone:
            return jsonify({"error": "Name, email, and phone are required."}), 400

        # Save to Supabase
        response = supabase.table("enrollments").insert({
            "name": name,
            "email": email,
            "phone": phone,
            "age": age,
            "dance_style": dance_style,
            "experience_level": experience
        }).execute()

        # Send confirmation email to student
        try:
            send_email(
                email,
                "Welcome to Elite Dance Academy 💃",
                f"""
                <div style="font-family:Arial;padding:30px;background:#f4f6f8">
                <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:10px">
                <h2 style="color:#e63946;text-align:center">💃 Welcome to Elite Dance Academy</h2>
                <p>Hello <b>{name}</b>,</p>
                <p>Thank you for enrolling in <b>{dance_style}</b>.</p>
                <p>We are excited to welcome you to our dance family!</p>
                <div style="background:#f1faee;padding:15px;border-radius:8px;margin:20px 0">
                <b>Enrollment Details</b><br>
                Name: {name}<br>
                Dance Style: {dance_style}
                </div>
                <p>Our team will contact you soon with class schedule details.</p>
                <p>Keep dancing, keep shining! ✨</p>
                <hr>
                <p style="text-align:center;color:#777">Elite Dance Academy<br>Inspiring Passion Through Dance</p>
                </div>
                </div>
                """
            )
        except Exception as mail_err:
            print("Email failed (non-fatal):", mail_err)

        return jsonify({"message": "Enrollment successful", "data": response.data}), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# CONTACT ROUTE
# -----------------------------
@app.route("/mentor-request", methods=["POST"])
def contact():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        name    = (data.get("name") or "").strip()
        email   = (data.get("email") or "").strip()
        message = (data.get("message") or "").strip()

        if not name or not email or not message:
            return jsonify({"error": "All fields are required."}), 400

        # Save to Supabase
        if supabase:
            supabase.table("mentor_requests").insert({
                "name":    name,
                "email":   email,
                "message": message
            }).execute()

        # Send confirmation to student
        try:
            send_email(
                email,
                "We received your message | Elite Dance Academy",
                f"""
                <h2>Thank You for Contacting Elite Dance Academy</h2>
                <p>Hello <b>{name}</b>,</p>
                <p>Thank you for reaching out to us.</p>
                <p>Our mentor will review your request and contact you shortly.</p>
                <p>We are excited to help you start your dance journey! 💃</p>
                <br>
                <p>Best Regards,<br>Elite Dance Academy Team</p>
                """
            )
        except Exception as mail_err:
            print("Email failed (non-fatal):", mail_err)

        return jsonify({"message": "Request received! We'll contact you within 24 hours. 🎉"}), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port

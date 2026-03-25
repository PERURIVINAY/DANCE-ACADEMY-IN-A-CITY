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
BREVO_API_KEY     = os.environ.get("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
ADMIN_EMAIL       = os.environ.get("ADMIN_EMAIL", BREVO_SENDER_EMAIL)  # fallback to sender

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
    print("✅ Supabase connected")
except Exception as e:
    supabase = None
    print("❌ Supabase init failed:", e)


# -----------------------------
# EMAIL FUNCTION (Brevo)
# -----------------------------
def send_email(to_email, subject, html_body):
    try:
        if not BREVO_API_KEY:
            print("❌ BREVO_API_KEY not set")
            return False
        if not BREVO_SENDER_EMAIL:
            print("❌ BREVO_SENDER_EMAIL not set")
            return False

        payload = {
            "sender": {
                "name": "Elite Dance Academy",
                "email": BREVO_SENDER_EMAIL
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body
        }

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=15
        )

        print(f"📧 Brevo → {to_email} | Status: {response.status_code} | Response: {response.text}")
        return response.status_code in (200, 201)

    except requests.exceptions.Timeout:
        print("❌ Email timeout")
        return False
    except Exception as e:
        print("❌ Email error:", e)
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
    if not BREVO_API_KEY:
        return jsonify({"error": "BREVO_API_KEY not set in Railway environment variables"}), 500
    if not BREVO_SENDER_EMAIL:
        return jsonify({"error": "BREVO_SENDER_EMAIL not set in Railway environment variables"}), 500

    success = send_email(
        BREVO_SENDER_EMAIL,
        "✅ Test Email from Elite Dance Academy",
        "<h2>Email works!</h2><p>Brevo is configured correctly.</p>"
    )
    if success:
        return jsonify({"message": f"Test email sent to {BREVO_SENDER_EMAIL}"})
    return jsonify({"error": "Email failed. Check BREVO_API_KEY and BREVO_SENDER_EMAIL in Railway."}), 500


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
            "name":             name,
            "email":            email,
            "phone":            phone,
            "age":              age,
            "dance_style":      dance_style,
            "experience_level": experience
        }).execute()

        print(f"✅ Enrollment saved for {name} ({email})")

        # --- Confirmation email to student ---
        student_html = f"""
        <div style="font-family:Arial,sans-serif;padding:30px;background:#f4f6f8;">
          <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:10px;border-top:5px solid #e63946;">
            <h2 style="color:#e63946;text-align:center;">💃 Welcome to Elite Dance Academy</h2>
            <p>Hello <b>{name}</b>,</p>
            <p>Thank you for enrolling in <b>{dance_style}</b>! We are thrilled to welcome you to our dance family.</p>
            <div style="background:#f1faee;padding:15px;border-radius:8px;margin:20px 0;border-left:4px solid #e63946;">
              <b>Your Enrollment Details</b><br><br>
              👤 Name: {name}<br>
              💃 Dance Style: {dance_style}<br>
              📊 Experience: {experience}<br>
              📞 Phone: {phone}
            </div>
            <p>Our team will contact you shortly with class schedule and timing details.</p>
            <p>Keep dancing, keep shining! ✨</p>
            <hr style="margin:20px 0;">
            <p style="text-align:center;color:#777;font-size:13px;">
              Elite Dance Academy<br>
              Bhanugudi Junction, Kakinada<br>
              📞 +91 90000 12345 | ✉️ admissions@elitedance.com
            </p>
          </div>
        </div>
        """
        email_sent = send_email(email, "🎉 Welcome to Elite Dance Academy!", student_html)
        if not email_sent:
            print(f"⚠️ Confirmation email failed for {email} (enrollment still saved)")

        # --- Notification email to admin ---
        if ADMIN_EMAIL:
            admin_html = f"""
            <div style="font-family:Arial,sans-serif;padding:20px;">
              <h3>🆕 New Enrollment Received</h3>
              <table style="border-collapse:collapse;width:100%;">
                <tr><td style="padding:8px;border:1px solid #ddd;"><b>Name</b></td><td style="padding:8px;border:1px solid #ddd;">{name}</td></tr>
                <tr><td style="padding:8px;border:1px solid #ddd;"><b>Email</b></td><td style="padding:8px;border:1px solid #ddd;">{email}</td></tr>
                <tr><td style="padding:8px;border:1px solid #ddd;"><b>Phone</b></td><td style="padding:8px;border:1px solid #ddd;">{phone}</td></tr>
                <tr><td style="padding:8px;border:1px solid #ddd;"><b>Age</b></td><td style="padding:8px;border:1px solid #ddd;">{age or 'N/A'}</td></tr>
                <tr><td style="padding:8px;border:1px solid #ddd;"><b>Dance Style</b></td><td style="padding:8px;border:1px solid #ddd;">{dance_style}</td></tr>
                <tr><td style="padding:8px;border:1px solid #ddd;"><b>Experience</b></td><td style="padding:8px;border:1px solid #ddd;">{experience}</td></tr>
              </table>
            </div>
            """
            send_email(ADMIN_EMAIL, f"🆕 New Enrollment: {name} – {dance_style}", admin_html)

        return jsonify({"message": "Enrollment successful!", "data": response.data}), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# MENTOR REQUEST ROUTE
# -----------------------------
@app.route("/mentor-request", methods=["POST"])
def mentor_request():
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
            try:
                supabase.table("mentor_requests").insert({
                    "name":    name,
                    "email":   email,
                    "message": message
                }).execute()
                print(f"✅ Mentor request saved for {name} ({email})")
            except Exception as db_err:
                # Log but don't fail — emails still go out
                print(f"⚠️ DB insert failed (mentor_requests): {db_err}")
                print("👉 Make sure the 'mentor_requests' table exists in Supabase.")

        # --- Confirmation email to user ---
        user_html = f"""
        <div style="font-family:Arial,sans-serif;padding:30px;background:#f4f6f8;">
          <div style="max-width:600px;margin:auto;background:white;padding:30px;border-radius:10px;border-top:5px solid #00b4d8;">
            <h2 style="color:#e63946;text-align:center;">🎓 Elite Dance Academy</h2>
            <p>Hello <b>{name}</b>,</p>
            <p>Thank you for reaching out to us! We've received your message and a mentor will review it and contact you within <b>24 hours</b>.</p>
            <div style="background:#f1faee;padding:15px;border-radius:8px;margin:20px 0;border-left:4px solid #00b4d8;">
              <b>Your Message</b><br><br>
              {message}
            </div>
            <p>We are excited to help you start your dance journey! 💃</p>
            <hr style="margin:20px 0;">
            <p style="text-align:center;color:#777;font-size:13px;">
              Elite Dance Academy<br>
              Bhanugudi Junction, Kakinada<br>
              📞 +91 90000 12345 | ✉️ admissions@elitedance.com
            </p>
          </div>
        </div>
        """
        email_sent = send_email(email, "✅ We received your message | Elite Dance Academy", user_html)
        if not email_sent:
            print(f"⚠️ Confirmation email failed for {email}")

        # --- Notification to admin ---
        if ADMIN_EMAIL:
            admin_html = f"""
            <div style="font-family:Arial,sans-serif;padding:20px;">
              <h3>📩 New Mentor Request</h3>
              <p><b>Name:</b> {name}</p>
              <p><b>Email:</b> {email}</p>
              <p><b>Message:</b></p>
              <blockquote style="border-left:4px solid #e63946;padding-left:12px;color:#555;">{message}</blockquote>
            </div>
            """
            send_email(ADMIN_EMAIL, f"📩 Mentor Request from {name}", admin_html)

        return jsonify({"message": "Request received! We'll contact you within 24 hours. 🎉"}), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

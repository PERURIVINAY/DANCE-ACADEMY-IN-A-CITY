# 🎭 Elite Dance Academy

---

## 📖 Project Description

Elite Dance Academy is a full-stack web application for a professional dance studio that allows students to explore dance styles, sign in securely, and enroll in classes. The platform offers a smooth, modern experience for both learners and administrators, bridging the gap between traditional dance heritage and modern performance culture.

---

## 🚨 Problem Statement

Dance academies typically rely on manual enrollment processes — phone calls, paper forms, or walk-ins — making it difficult to manage registrations efficiently and provide students with instant access to course information. There is a need for a centralized digital platform where students can discover available classes, sign in securely, and reserve their spot with ease, while the academy can manage enrollments professionally.

---

## ✨ Features

- 🔐 **Google OAuth2 Authentication** — Secure sign-in using Google accounts
- 🎓 **Class Enrollment System** — Students can browse and enroll in dance classes (Beginner / Intermediate / Advanced)
- 💃 **9 Dance Styles** — Bharatanatyam, Hip Hop, Contemporary, Salsa, Kathak, Ballet, and more
- ⭐ **Student Testimonials** — Real reviews displayed in an animated carousel
- 📩 **Trial Class Request** — Users can request a free trial session via a contact form
- 📧 **Email Notifications** — Powered by Brevo API for transactional emails
- 📱 **Responsive Design** — Works seamlessly across desktop and mobile devices
- 🏆 **Academy Stats** — Displays live stats like students trained, ratings, and awards

---

## 🛠️ Technologies Used

| Category | Technology |
|---|---|
| **Backend** | Python, Flask |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Authentication** | Google OAuth2 |
| **Database** | Supabase (PostgreSQL) |
| **Email Service** | Brevo API (Transactional Emails) |
| **Deployment** | Railway |

---

## 📁 Project Structure

```
elite-dance-academy/
│
├── static/
│   ├── hero-dance.jpg
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
└── README.md
```

---

## ⚙️ Installation / Setup

### Prerequisites

- Python 3.8+
- A Google Cloud project with OAuth2 credentials
- A Supabase account and project
- A Brevo account with API key

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/elite-dance-academy.git
   cd elite-dance-academy
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate        # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```env
   FLASK_SECRET_KEY=your_secret_key
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   BREVO_API_KEY=your_brevo_api_key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:5000
   ```

---

## 🚀 Usage

1. Visit the homepage to explore dance styles and academy information.
2. Click **Sign In** and authenticate using your Google account.
3. Browse available dance classes under the **Classes** section.
4. Select a class and choose your level (Beginner / Intermediate / Advanced).
5. Click **Confirm Spot** to complete your enrollment.
6. Use the **Contact** section to request a free trial class.
7. A confirmation email will be sent via Brevo upon successful enrollment.

---

## 🖼️ Sample Output

```
🏠 Homepage
  → Hero banner with academy tagline
  → "9 world-class styles, 1 destination"

🔐 Sign In Modal
  → Google OAuth2 popup for authentication

💃 Classes Section
  → Cards for each dance style with description and mastery path

✅ Enrollment Confirmation
  → "Confirm Spot" button with level selection (Beginner / Intermediate / Advanced)

📧 Email Notification
  → Automated confirmation email sent via Brevo API
```

> **Live Demo:** [https://web-production-93d2c.up.railway.app](https://web-production-93d2c.up.railway.app)

---

## 🔮 Future Improvements

- 📅 **Class Scheduling** — Add a live timetable with date/time slots for each class
- 💳 **Online Payment Integration** — Enable fee payment via Razorpay or Stripe
- 📊 **Admin Dashboard** — A backend panel for managing students, classes, and enrollments
- 🔔 **Push Notifications** — Remind students of upcoming classes
- 🌐 **Multi-language Support** — Add regional language options (Telugu, Hindi)
- 📷 **Gallery Section** — Showcase performance photos and event highlights
- 📱 **Mobile App** — Build a companion app for iOS and Android

---

## 👥 Authors

This project was collaboratively built by:

| Name | Role |
|---|---|
| **Mallipudi Sri Sri Meher Nayana** | Full Stack Developer |
| **Peruri Vinay** | Full Stack Developer |
| **Shaik Ismail** | Frontend Developer & Tester |

---

---

© 2025 Elite Dance Academy. All Rights Reserved.

> Feel free to suggest improvements or contribute enhancements.

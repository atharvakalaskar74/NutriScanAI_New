# NutriScan AI

### AI-Powered Food Recognition & Personal Nutrition Assistant

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%20%7C%20MariaDB-4479A1?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Multimodal%20AI-4285F4?style=flat&logo=google&logoColor=white)](https://aistudio.google.com/)

**NutriScan AI** is an intelligent, full-stack personal nutrition and diet tracking platform. Built with Python Flask, MySQL, and Google Gemini Multimodal Vision AI, it enables users to scan meal plates using their camera or upload food photos, automatically distinguishes food from non-food items, identifies multiple dishes in a single frame, estimates portion weights, dynamically recalculates macro distributions, and offers personalized AI dietary coaching.

---

## 🌟 Key Features

1. **Multimodal Food Scanner (Google Gemini)**
   - Live browser camera capture via WebRTC (`getUserMedia()`) or image file upload.
   - Recognizes complex meals and dishes (Indian thalis, biryanis, salads, international cuisines) beyond static database lists.
   - Detects multiple food items on a single plate (e.g., Rice + Dal + Roti + Sabzi).
2. **Food vs. Non-Food Guard**
   - Automatically detects and rejects non-food images (selfies, human faces, electronics, pets, vehicles) with clear user feedback.
   - Strictly prevents inaccurate caloric estimations for non-food items.
3. **Interactive Portion & Weight Recalculation**
   - Estimated serving weights (e.g. 300g Biryani) can be adjusted by the user in real time.
   - Instant recalculation of Calories, Protein, Carbs, Fat, Fiber, and Sugar without page reloads.
4. **Smart Database Caching & Cost Optimization**
   - Client and server-side image compression with Pillow (max 1024px) saves upload bandwidth and lowers AI latency.
   - Automatically caches newly identified foods and their standard 100g nutritional profile into the local MySQL database, reducing redundant Gemini API calls.
5. **Personal Nutrition Calculator (Mifflin-St Jeor Formula)**
   - Computes Basal Metabolic Rate (BMR) and Total Daily Energy Expenditure (TDEE).
   - Generates personalized targets based on fitness goals: *Maintain*, *Lose Weight*, *Gain Weight*, or *Build Muscle*.
6. **Transparent 0–100 Daily Wellness Score**
   - Evaluates daily caloric adherence, protein achievement, macro balance, and meal logging consistency.
7. **Context-Aware Gemini AI Assistant**
   - Chatbot with real-time awareness of your profile and today's remaining calories and macros.
   - Offers actionable dietary advice, post-workout suggestions, and healthy recipe alternatives.
8. **Meal History & Daily Tracking**
   - Complete meal logs with date filtering (Today, Yesterday, Custom Date).
   - Categorized by meal type (Breakfast, Lunch, Dinner, Snack).

---

## 🏗️ Architecture & Technology Stack

```
NutriScan AI/
│
├── app.py                      # Flask Application Factory & Server Entrypoint
├── requirements.txt            # Locked Python Dependencies
├── .env.example                # Template for Environment Variables
├── .env                        # Local Environment Configuration (git-ignored)
├── .gitignore                  # Git Ignore Rules
├── Procfile                    # Production Gunicorn Process Definition
├── runtime.txt                 # Target Python Version for Cloud Hosting
├── README.md                   # Complete Documentation
│
├── config/
│   ├── __init__.py
│   └── config.py               # Centralized Configuration Loader
│
├── database/
│   ├── __init__.py
│   ├── db.py                   # PyMySQL Connection Pool & Auto-Initializer
│   └── schema.sql              # Normalized MySQL Schema with 30 Seed Foods
│
├── models/
│   ├── __init__.py
│   ├── user.py                 # User Model & Password Hashing
│   ├── nutrition_goal.py       # Macro Targets Model
│   ├── food.py                 # Food & 100g Nutrition Cache Model
│   ├── meal.py                 # Meals & Meal Items Model
│   ├── ai_analysis.py          # AI Scan Audit Logger
│   └── chat_history.py         # AI Assistant Conversation Model
│
├── services/
│   ├── __init__.py
│   ├── gemini_service.py       # Google GenAI Multimodal & Chatbot Service
│   ├── food_analysis_service.py# Image Compression & Scan Pipeline
│   ├── nutrition_service.py    # Nutrition Scaling & Recalculation
│   ├── calculation_service.py  # Scientific BMR, TDEE, & Wellness Score Formulas
│   └── validation_service.py   # Input & File Security Validation
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py          # Authentication & Session Handlers
│   ├── dashboard_routes.py     # Dashboard & Analytics Endpoints
│   ├── scanner_routes.py       # Camera & AI Image Scanner Endpoints
│   ├── nutrition_routes.py     # Dynamic Macro Recalculation API
│   ├── meal_routes.py          # Meal Saving & Historical Logs
│   ├── goals_routes.py         # Goal Calculator & Profile Settings
│   └── chatbot_routes.py       # Gemini Assistant Chat API
│
├── templates/
│   ├── base.html               # Semantic Master Layout & Navigation
│   ├── index.html              # Modern Hero Landing Page
│   ├── login.html              # Glassmorphic Sign In Card
│   ├── register.html           # Profile & Physical Metric Registration
│   ├── dashboard.html          # Real-time Nutrition Dashboard
│   ├── scanner.html            # WebRTC Camera & Food Scanner
│   ├── meal_history.html       # Date-Filtered Meal History Log
│   ├── goals.html              # BMR/TDEE Goals Calculator
│   ├── profile.html            # User Profile Settings
│   └── chatbot.html            # Contextual AI Assistant Chat View
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern Theme with CSS Variables & Micro-animations
│   └── js/
│       ├── main.js             # Navigation & Global Utilities
│       ├── scanner.js          # WebRTC Camera, Scan Processing, & Weight Listeners
│       └── chatbot.js          # Interactive Gemini Chatbot Stream
│
├── tests/
│   ├── __init__.py
│   └── test_basic.py           # Unit & Smoke Test Suite (9 Tests)
│
└── uploads/                    # Local Storage for Compressed Food Images
    └── .gitkeep
```

---

## ⚙️ Local Development Setup (Windows / XAMPP)

### Prerequisites
- **Python**: Version 3.12 (or 3.11+) installed on Windows.
- **XAMPP**: Apache & MySQL distribution installed (e.g. at `C:\xampp` or `D:\XAMPP`).
- **Web Browser**: Chrome, Edge, or Firefox (with camera permissions allowed).

### Step-by-Step Instructions

#### 1. Open Terminal & Navigate to Project
```powershell
cd d:\NutriScanAI_New
```

#### 2. Create and Activate Virtual Environment
```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
```

#### 3. Install Python Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Start XAMPP MySQL
1. Launch **XAMPP Control Panel**.
2. Click **Start** next to **MySQL** (Default port: `3306`).

#### 5. Configure Environment Variables
Copy `.env.example` to `.env` (or verify existing `.env`):
```ini
# Flask Configuration
SECRET_KEY=nutriscan_ai_secret_key_development_2026_dev_secure
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

# Database Configuration (Local XAMPP MySQL)
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=nutriscan_ai_db
DATABASE_USER=root
DATABASE_PASSWORD=

# Google Gemini AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# Upload Configuration
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
```

> **Note:** The database `nutriscan_ai_db` and all 8 tables with 30 seeded staple foods are created automatically when the app boots up via `init_db()`. You do not need to create them manually.

#### 6. Run the Application
```powershell
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🔑 Obtaining Your Free Google Gemini API Key

NutriScan AI is powered by Google's free-tier Gemini API (`gemini-2.5-flash`):
1. Visit **Google AI Studio**: [https://aistudio.google.com/](https://aistudio.google.com/)
2. Sign in with your Google account.
3. Click **"Get API key"** and then **"Create API key in new project"**.
4. Copy the generated key.
5. Paste it into your `.env` file:
   ```ini
   GEMINI_API_KEY=AIzaSy...your-actual-key...
   ```
6. Restart the Flask server.

> **Offline / Demo Mode:** Even without an API key, all authentication, dashboard tracking, BMR/TDEE calculations, manual food recalculations, database caching, and meal history work completely!

---

## 🧪 Running Automated Tests

Run the complete unit and integration test suite:
```powershell
.\venv\Scripts\python.exe -m unittest tests/test_basic.py
```
**Test Coverage Includes:**
- Password hashing & verification (`werkzeug.security`)
- Mifflin-St Jeor BMR formula (Male and Female verification)
- TDEE multipliers across sedentary, moderate, and active tiers
- Macronutrient partitioning (Protein, Carbs, Fat) by fitness goal
- Gram-based nutritional scaling
- Daily Wellness Score (0–100 bounds and adherence scoring)
- Input & security file validation (allowing JPG/PNG/WEBP, blocking EXE/scripts)
- Flask route smoke tests and unauthenticated redirect checks
- Gemini JSON response parser (handling plain JSON, markdown code fences, and conversational wrappers)

---

## 🚀 Zero-Cost Cloud Deployment Guide (₹0 / $0 — No Credit Card Required)

NutriScan AI is engineered for zero-cost deployment using currently available free-tier services.

### Current Free-Tier Architecture:
- **Cloud Web Hosting**: [Render.com](https://render.com) (Free Web Service — 512 MB RAM, free `*.onrender.com` HTTPS domain, no credit card required)
- **Cloud MySQL Database**: [TiDB Cloud Starter](https://tidbcloud.com/) (Serverless — 5 GiB free MySQL 8.0 compatible storage, 50M Request Units/month, no credit card required, never expires)
- **Multimodal AI**: [Google Gemini API](https://aistudio.google.com/) (Free Developer API tier)

---

### Step 1: Create Free Cloud MySQL Database (TiDB Cloud Starter)
1. Sign up for free at [tidbcloud.com](https://tidbcloud.com/) (Log in with GitHub or Google — no credit card needed).
2. Click **Create Cluster** and select **Starter** (Free).
3. Choose your nearest region (e.g., AWS / Singapore or US) and click **Create**.
4. In the security dialog, generate your root password and save it securely.
5. In the TiDB Cloud Console, click **SQL Editor**:
   - Open [`database/schema_cloud.sql`](database/schema_cloud.sql) from this project.
   - Copy the entire SQL content, paste it into the TiDB Cloud SQL Editor, and click **Run**.
   - This creates all 8 tables (`users`, `nutrition_goals`, `foods`, `food_nutrition`, `meals`, `meal_items`, `ai_analyses`, `chat_history`) and inserts 30 pre-seeded staple foods.
6. Click the **Connect** button in your cluster dashboard and select **PyMySQL**:
   - Note down your `Host`, `Port` (usually `4000`), `User` (e.g. `xxxx.root`), and `Database` (`test` or your cluster name).

---

### Step 2: Push Project to GitHub
1. Create a new repository on [GitHub](https://github.com/new) named `NutriScanAI_New` (set to **Public** or **Private**).
2. Push your code:
   ```powershell
   git remote add origin https://github.com/your-username/NutriScanAI_New.git
   git branch -M main
   git push -u origin main
   ```

---

### Step 3: Deploy to Render
1. Sign up or log in to [Render.com](https://render.com) with your GitHub account.
2. From the dashboard, click **New + > Web Service**.
3. Select your `NutriScanAI_New` GitHub repository and click **Connect**.
4. Configure service settings:
   - **Name**: `nutriscan-ai` (or your preferred name)
   - **Region**: Nearest to your TiDB database (e.g. Singapore, Oregon, Frankfurt)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Select **Free** (512 MB RAM)
5. Scroll down to **Environment Variables** and add the following:

   | Variable | Value / Description |
   |---|---|
   | `SECRET_KEY` | Strong random 32-character string |
   | `FLASK_ENV` | `production` |
   | `FLASK_DEBUG` | `False` |
   | `DATABASE_HOST` | Your TiDB Cloud Gateway Host (e.g. `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`) |
   | `DATABASE_PORT` | `4000` |
   | `DATABASE_NAME` | `test` (or your TiDB database name) |
   | `DATABASE_USER` | Your TiDB username (e.g. `2yBxxxx.root`) |
   | `DATABASE_PASSWORD` | Your TiDB root password |
   | `DATABASE_SSL` | `True` |
   | `GEMINI_API_KEY` | Your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/) |
   | `GEMINI_MODEL` | `gemini-3.6-flash` |

6. Click **Deploy Web Service**.
7. Render will build the environment, install dependencies, and launch Gunicorn. Within 2–3 minutes, your application will be live at `https://<your-service-name>.onrender.com`!
8. Test your live deployment:
   - Visit `https://<your-service-name>.onrender.com/health` — should return `{"status": "healthy", "database_connected": true}`.
   - Register an account, test the camera food scanner, and chat with the AI assistant.

---

## 📋 Environment Variables Reference

| Variable | Required | Default (Local) | Cloud (Render) | Description |
|---|---|---|---|---|
| `SECRET_KEY` | Yes | `nutriscan_ai_...` | *(Random String)* | Flask session encryption key |
| `FLASK_ENV` | No | `development` | `production` | Environment mode |
| `FLASK_DEBUG` | No | `True` | `False` | Flask debugger flag |
| `PORT` | No | `5050` | *(Render provides)* | Web server port |
| `DATABASE_HOST` | Yes | `localhost` | *(TiDB host)* | MySQL host address |
| `DATABASE_PORT` | Yes | `3306` | `4000` | MySQL port |
| `DATABASE_NAME` | Yes | `nutriscan_ai_db` | `test` | Database name |
| `DATABASE_USER` | Yes | `root` | *(TiDB user)* | Database username |
| `DATABASE_PASSWORD`| Yes | *(empty)* | *(TiDB pass)* | Database password |
| `DATABASE_SSL` | No | `False` | `True` | Enable TLS/SSL connection |
| `DATABASE_SSL_CA` | No | *(empty)* | *(empty)* | Optional path to CA bundle |
| `GEMINI_API_KEY` | Yes | *(your key)* | *(your key)* | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.6-flash` | `gemini-3.6-flash` | Gemini model name |
| `MAX_CONTENT_LENGTH`| No | `16777216` | `16777216` | Max upload size in bytes (16MB) |
| `UPLOAD_FOLDER` | No | `uploads` | `uploads` | Storage folder for meal scans |

---

## 🔒 Security & Privacy

- **Password Protection**: Passwords are never stored in plain text; they are secured using salted PBKDF2/SHA-256 hashes via `werkzeug.security`.
- **API Key Security**: The Gemini API key remains strictly on the server backend; it is never exposed to client-side JavaScript or HTML.
- **SQL Injection Prevention**: All queries utilize parameterized PyMySQL statements.
- **File Upload Security**: Uploaded files are verified via Pillow image parsing to ensure genuine image headers and reject executable or script extensions.
- **Multi-Tenant Data Isolation**: All meal records, goals, and chat interactions are strictly scoped to the authenticated user's session ID.

---

## ⚕️ Disclaimer

NutriScan AI is designed for educational, fitness tracking, and wellness purposes. Caloric values, portion weights, and nutritional percentages estimated by Gemini AI are approximations and should not be used as clinical medical prescriptions or diagnostic dietary advice.

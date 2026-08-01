# 🧠 AI Quiz & Study Generator

An intelligent, full-stack learning platform powered by **FastAPI**, **React (Vite)**, **Tailwind CSS**, and **Google Gemini AI**. It transforms study materials into interactive quizzes, 3D flashcards, personalized AI study advice, and real-time performance analytics.

---

## 🌟 Key Features

### 📄 1. Document Upload & Processing
- Upload **PDF**, **DOCX**, and **TXT** files.
- Automated text extraction, cleaning, and smart chunking pipeline.

### 🤖 2. Dual Quiz Generation Modes
- **Document-Based Quizzes:** Select any uploaded document, configure difficulty (Easy / Medium / Hard) and question count (3–15), and generate tailored multiple-choice quizzes.
- **Topic-Based Quizzes:** Generate quizzes instantly on any subject (e.g., *"Python Loops"*, *"Indian History"*, *"Quantum Physics"*) using Gemini AI — no file upload required!

### 🎴 3. Interactive 3D AI Flashcards
- Extract key concepts, formulas, and definitions from study documents.
- 3D CSS flip cards with **"Got It"** vs. **"Needs Review"** mastery tracking and final completion stats.

### ⏱️ 4. Quiz-Taking Engine & Real-Time Scoring
- Live countdown timer with auto-submission upon expiry.
- Question navigator sidebar, selection tracking, and instant answer grading.

### 💡 5. Gemini AI Personalized Feedback
- Gemini analyzes incorrect quiz answers to provide custom **AI Study Recommendations** on the results page.
- Comprehensive question breakdown with answer keys and detailed explanations.

### 📥 6. Offline Study Support (Quiz Export)
- Download quizzes as printable **`.txt`** or structured **`.json`** files.
- Option to export **with full answers & explanations** or as a **blank practice worksheet**.

### 📚 7. Quizzes Library (`/quizzes`)
- Centralized hub to search quizzes by title, filter by difficulty (Easy/Medium/Hard), retake, export, or delete past quizzes.

### 📈 8. Real-Time Analytics Dashboard
- Track total quizzes completed, average score percentage, study time, uploaded docs, and recent attempt history.

### 👤 9. User Profile & Daily Goals
- Editable display name, bio, and interactive **Daily Quiz Goal** tracker (1–10 quizzes/day) with live progress bar.

### 🔔 10. Toast Notification System
- Smooth, non-blocking global toast alerts (**Success**, **Error**, **Warning**, **Info**) for instant UI feedback.

---

## 🛠️ Tech Stack

| Domain | Technologies Used |
| :--- | :--- |
| **Frontend** | React, Vite, Tailwind CSS, React Router v6, Lucide Icons |
| **Backend** | FastAPI (Python 3.10+), Pydantic v2, Uvicorn |
| **Database** | SQLite + SQLAlchemy ORM |
| **AI Integration** | Google Gemini API (`google-genai` SDK, `gemini-3.1-flash-lite`) |
| **Authentication** | JWT (JSON Web Tokens) with `passlib` (bcrypt) password hashing |

---

## 🔌 API Endpoints Summary

### 🔑 Auth (`/api/auth`)
- `POST /api/auth/signup` — Register a new account
- `POST /api/auth/login` — Authenticate user & return JWT token
- `GET /api/auth/me` — Get current logged-in user profile

### 📁 Uploads (`/api/uploads`)
- `POST /api/uploads` — Upload document (PDF/DOCX/TXT)
- `GET /api/uploads` — List all user uploaded documents
- `DELETE /api/uploads/{id}` — Delete document

### 📝 Quizzes (`/api/quizzes`)
- `POST /api/quizzes/generate` — Generate quiz from uploaded document
- `POST /api/quizzes/generate-from-topic` — Generate quiz from free-text topic
- `GET /api/quizzes` — List user's quizzes summary
- `GET /api/quizzes/{id}` — Fetch full quiz with questions
- `POST /api/quizzes/{id}/submit` — Grade attempt & get Gemini feedback
- `GET /api/quizzes/{id}/export` — Download quiz (`.txt` or `.json`)
- `DELETE /api/quizzes/{id}` — Delete quiz

### 🎴 Flashcards (`/api/flashcards`)
- `POST /api/flashcards/generate` — Generate flashcard deck from document

### 📊 Analytics & Profile
- `GET /api/analytics/dashboard` — Fetch dashboard statistics
- `GET /api/profile` — Fetch user profile & daily goal
- `PATCH /api/profile` — Update name, bio, or daily goal

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** (v18+)
- **Python** (3.10+)
- **Google Gemini API Key**

---

### 1️⃣ Backend Setup

```bash
cd backend

# Create & activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Add your Gemini API key:
# GEMINI_API_KEY=your_gemini_api_key_here
# SECRET_KEY=your_jwt_secret_key_here

# Run backend server
python -m uvicorn app.main:app --reload --port 8000
```

The backend server will run at `http://localhost:8000`. Interactive API Docs are available at `http://localhost:8000/docs`.

---

### 2️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend development server
npm run dev
```

The frontend application will be running at `http://localhost:5173`.

---

## 📂 Project Structure

```
AI-quiz-generator/
├── backend/
│   ├── app/
│   │   ├── database.py       # SQLAlchemy engine & session setup
│   │   ├── main.py           # FastAPI application entry & router registration
│   │   ├── config.py         # Environment variables & configuration
│   │   ├── models/           # User, Upload, Quiz, Question, Attempt DB models
│   │   ├── routers/          # Auth, Upload, Quiz, Flashcards, Analytics, Profile routers
│   │   ├── schemas/          # Pydantic data schemas
│   │   ├── services/         # Gemini AI service & text processing service
│   │   └── middleware/       # Auth middleware & JWT verification
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/       # Layout, UI components, Modals (TopicQuizModal, etc.)
    │   ├── context/          # AuthContext, ToastContext
    │   ├── pages/            # Dashboard, Upload, Quizzes, Quiz, Flashcards, Profile
    │   ├── services/         # Axios API client setup
    │   ├── App.jsx           # Routing definition
    │   └── main.jsx          # App root & ToastProvider wrapper
    ├── index.html
    └── package.json
```

---

## 📜 License

This project is licensed under the MIT License.

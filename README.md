# 🧠 AI Quiz Generator

An AI-powered quiz generation platform that transforms your study materials into interactive quizzes, flashcards, and personalized learning experiences.

## Features

- 📄 **Upload Documents** — PDF, DOCX, PPTX, TXT
- 🤖 **AI Quiz Generation** — Powered by Google Gemini
- 📊 **Smart Analytics** — Track performance over time
- 🎯 **Adaptive Learning** — Quizzes adapt to your weak areas
- 💬 **AI Tutor** — Ask questions about your materials
- 📇 **Flashcards** — Auto-generated from your notes
- 📥 **Export** — Download quizzes as PDF, DOCX, CSV

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS v4 |
| Backend | FastAPI (Python) |
| Database | SQLite |
| AI | Google Gemini API |

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Project Structure
```
AI-quiz-generator/
├── frontend/          # React + Vite
├── backend/           # FastAPI
├── docs/              # Documentation
├── .gitignore
└── README.md
```

## License
MIT

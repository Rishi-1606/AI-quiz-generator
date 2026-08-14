from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database import engine, Base
from app.limiter import limiter
from app.models import User, Upload, Quiz, Question, Attempt, GenerationJob  # noqa: F401 — ensure models are registered
from app.routers import auth, upload, quiz, analytics, flashcards, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Quiz Generator API",
    lifespan=lifespan,
)

# Rate-limit state + middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware — allow Vite dev server (support port fallback)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(quiz.router)
app.include_router(analytics.router)
app.include_router(flashcards.router)
app.include_router(profile.router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "AI Quiz Generator API"}
